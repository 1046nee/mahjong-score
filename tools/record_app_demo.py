# -*- coding: utf-8 -*-
# 実アプリの操作デモ動画を録画する（LP → グループ作成 → URL共有 → 点数入力 → 成績・グラフ確認）。
# shoot_app_screens.py と同じ「ローカル起動＋Firebaseスタブ」方式（本番に触れない）。
# タップ位置はオレンジのリップルで可視化。共有URLは表示直前に https://majasco.jp/#... に差し替える。
#
# 出力（まじゃすこ素材/ig/video/）:
#   demo-raw.mp4        … 素の縦長スクリーン録画 780x1688（説明動画・編集素材用）
#   demo-short-9x16.mp4 … vividグラデ背景＋スマホフレーム合成 1080x1920（ショート動画用）
#
# 実行: PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers python3 tools/record_app_demo.py
#       （要: pip install playwright imageio-ffmpeg pillow）
import functools
import glob
import http.server
import math
import os
import re
import shutil
import subprocess
import threading

from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTDIR = os.path.join(BASE, "まじゃすこ素材", "ig", "video")
os.makedirs(OUTDIR, exist_ok=True)

PORT = 8789
VIEW_W, VIEW_H = 390, 844          # スマホ実寸ビューポート
# 録画はビューポート等倍で行う（Playwrightのrecord_video_sizeは縮小専用。
# 大きい値を指定すると左上に等倍配置＋グレー余白になる）。拡大はffmpeg側でlanczos補間
REC_W, REC_H = VIEW_W, VIEW_H
CANVAS_W, CANVAS_H = 1080, 1920    # ショート動画キャンバス（9:16）
SCREEN_W = 744                     # 合成時のスマホ画面幅
SCREEN_H = SCREEN_W * REC_H // REC_W
SCREEN_X = (CANVAS_W - SCREEN_W) // 2
SCREEN_Y = (CANVAS_H - SCREEN_H) // 2
BEZEL = 18

FONT = r"C:\Windows\Fonts\NotoSansJP-VF.ttf"
if not os.path.exists(FONT):
    FONT = "/usr/share/fonts/truetype/noto-jp/NotoSansJP.ttf"

GREEN_BG0, GREEN_BG1 = (17, 96, 116), (66, 97, 170)
ORANGE = (231, 86, 32)

# firebaseスタブ（shoot_app_screens.pyと同じ。セッションは空で始めてアプリに作らせる）
FIREBASE_STUB = """
(() => {
  const STORE = { sessions: {} };
  const listeners = [];
  const get = p => { let c = STORE; for (const k of p.split('/').filter(Boolean)) { if (c == null) return null; c = c[k]; } return c === undefined ? null : c; };
  const snap = p => ({ val: () => get(p), exists: () => get(p) != null });
  const fire = () => listeners.forEach(l => l.cb(snap(l.path)));
  const setPath = (p, v) => {
    const ks = p.split('/').filter(Boolean); let c = STORE;
    ks.slice(0, -1).forEach(k => { if (c[k] == null) c[k] = {}; c = c[k]; });
    if (v === null) delete c[ks[ks.length - 1]]; else c[ks[ks.length - 1]] = v;
    fire();
  };
  const ref = p => ({
    once: () => Promise.resolve(snap(p)),
    on: (ev, cb) => { listeners.push({ path: p, cb }); setTimeout(() => cb(snap(p)), 0); return cb; },
    off: (ev, cb) => { const i = listeners.findIndex(l => l.cb === cb); if (i >= 0) listeners.splice(i, 1); },
    set: v => { setPath(p, v); return Promise.resolve(); },
    update: o => { Object.keys(o).forEach(k => setPath(p + '/' + k, o[k])); return Promise.resolve(); },
    remove: () => { setPath(p, null); return Promise.resolve(); },
  });
  window.firebase = { initializeApp: () => {}, database: () => ({ ref }) };
})();
"""

# タップ位置の可視化（オレンジのリップル）
TAP_FX = """
(() => {
  const css = `.tapfx{position:fixed;width:56px;height:56px;margin:-28px 0 0 -28px;border-radius:50%;
    background:rgba(231,86,32,.35);border:3px solid rgba(231,86,32,.85);pointer-events:none;z-index:99999;
    animation:tapfx .55s ease-out forwards}
    @keyframes tapfx{0%{transform:scale(.4);opacity:1}100%{transform:scale(1.6);opacity:0}}`;
  const add = () => { const s = document.createElement('style'); s.textContent = css; document.head.appendChild(s); };
  if (document.head) add(); else document.addEventListener('DOMContentLoaded', add);
  document.addEventListener('pointerdown', e => {
    const d = document.createElement('div'); d.className = 'tapfx';
    d.style.left = e.clientX + 'px'; d.style.top = e.clientY + 'px';
    document.body.appendChild(d); setTimeout(() => d.remove(), 650);
  }, true);
})();
"""


def find_chromium():
    for pat in ["/opt/pw-browsers/chromium",
                "/opt/pw-browsers/chromium-*/chrome-linux/chrome",
                "/opt/pw-browsers/chromium-*/chrome-linux/headless_shell"]:
        for h in sorted(glob.glob(pat)):
            if os.path.isfile(h) and os.access(h, os.X_OK):
                return h
    return None


def ffmpeg_exe():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()  # libx264入りのフルビルド
    except ImportError:
        exe = shutil.which("ffmpeg")
        if exe:
            return exe
        raise RuntimeError("ffmpegが見つかりません（pip install imageio-ffmpeg）")


def sparkle(d, x, y, R, color):
    rr = R * 0.22
    pts = []
    for i in range(8):
        ang = math.radians(i * 45 - 90)
        rad = R if i % 2 == 0 else rr
        pts.append((x + rad * math.cos(ang), y + rad * math.sin(ang)))
    d.polygon(pts, fill=color)


def font(size, weight):
    f = ImageFont.truetype(FONT, size)
    try:
        f.set_variation_by_axes([weight])
    except Exception:
        pass
    return f


def build_overlay_images():
    """ショート動画合成用の背景（bg.png）とスマホフレーム（frame.png）を作る"""
    # 背景: vividグラデーション（IGv2シリーズと同じトーン）
    sw, sh = 108, 192
    bg = Image.new("RGB", (sw, sh))
    px = bg.load()
    for y in range(sh):
        for x in range(sw):
            t = (x / sw + y / sh) / 2
            px[x, y] = tuple(int(a + (b - a) * t) for a, b in zip(GREEN_BG0, GREEN_BG1))
    bg = bg.resize((CANVAS_W, CANVAS_H), Image.BICUBIC)
    d = ImageDraw.Draw(bg)
    sparkle(d, 92, 150, 30, (255, 255, 255))
    sparkle(d, 1000, 240, 38, ORANGE)
    sparkle(d, 70, 1700, 26, (219, 244, 249))
    sparkle(d, 1012, 1780, 30, (255, 255, 255))
    d.ellipse([950, 60, 972, 82], fill=ORANGE)
    d.text((CANVAS_W // 2, CANVAS_H - 60), "majasco.jp", font=font(40, 700), fill=(255, 255, 255), anchor="mm")
    bg_path = os.path.join(OUTDIR, "bg.png")
    bg.save(bg_path)

    # フレーム: ダークベゼルの中を透過（動画がそこに映る）
    frame = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    alpha = Image.new("L", (CANVAS_W, CANVAS_H), 0)
    da = ImageDraw.Draw(alpha)
    da.rounded_rectangle([SCREEN_X - BEZEL, SCREEN_Y - BEZEL,
                          SCREEN_X + SCREEN_W + BEZEL, SCREEN_Y + SCREEN_H + BEZEL],
                         radius=64, fill=255)
    da.rounded_rectangle([SCREEN_X, SCREEN_Y, SCREEN_X + SCREEN_W, SCREEN_Y + SCREEN_H],
                         radius=44, fill=0)
    color = Image.new("RGBA", (CANVAS_W, CANVAS_H), (20, 26, 30, 255))
    frame = Image.composite(color, frame, alpha)
    frame_path = os.path.join(OUTDIR, "frame.png")
    frame.save(frame_path)
    return bg_path, frame_path


def calc_scores(points, settings):
    """アプリと同じ単純ケース（同点なし）のスコア計算: (点数-返し点)/1000 + ウマ、トップにオカ"""
    n = settings["numPlayers"]
    ret, start, uma = settings["returnPoints"], settings["startPoints"], settings["uma"]
    order = sorted(range(n), key=lambda i: -points[i])
    scores = [0.0] * n
    for rank, i in enumerate(order):
        s = (points[i] - ret) / 1000 + uma[rank]
        if rank == 0:
            s += (ret - start) * n / 1000
        scores[i] = round(s, 1)
    return scores


def smooth_scroll_to(page, selector, offset=90, wait=1500):
    page.evaluate("""([sel, off]) => {
        const el = document.querySelector(sel);
        if (el) window.scrollTo({ top: el.getBoundingClientRect().top + window.scrollY - off, behavior: 'smooth' });
    }""", [selector, offset])
    page.wait_for_timeout(wait)


def record():
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=BASE)
    server = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    with sync_playwright() as p:
        exe = find_chromium()
        browser = p.chromium.launch(executable_path=exe) if exe else p.chromium.launch()
        ctx = browser.new_context(
            viewport={"width": VIEW_W, "height": VIEW_H}, locale="ja-JP",
            is_mobile=True, has_touch=True,
            record_video_dir=OUTDIR, record_video_size={"width": REC_W, "height": REC_H},
        )
        ctx.add_init_script(TAP_FX)
        page = ctx.new_page()

        def route_firebase(route):
            body = FIREBASE_STUB if "firebase-app-compat" in route.request.url else "/* stub */"
            route.fulfill(status=200, content_type="application/javascript", body=body)

        page.route("https://www.gstatic.com/firebasejs/**", route_firebase)
        page.route(lambda url: not url.startswith(f"http://127.0.0.1:{PORT}")
                   and not url.startswith("https://www.gstatic.com/firebasejs"),
                   lambda route: route.abort())

        # ---- LP ----
        page.goto(f"http://127.0.0.1:{PORT}/index.html", wait_until="load", timeout=30000)
        # 共有画面のURL欄はローカルURLになるため、表示直後に本番URL表記へ差し替える
        page.evaluate("""() => {
            const orig = window.startGame;
            window.startGame = async function () {
                await orig();
                const el = document.getElementById('share-url');
                if (el && sessionId) el.value = 'https://majasco.jp/#' + sessionId;
            };
        }""")
        page.wait_for_timeout(1800)

        # ---- グループ作成 ----
        page.click("#view-home .cta-btn")
        page.wait_for_timeout(900)
        page.click("#s-name")
        page.locator("#s-name").press_sequentially("金曜メンバー", delay=95)
        page.wait_for_timeout(350)
        for name in ["太郎", "次郎", "三郎", "四郎"]:
            page.click("#member-input")
            page.locator("#member-input").press_sequentially(name, delay=85)
            page.wait_for_timeout(150)
            page.click("#member-add-btn")
            page.wait_for_timeout(300)
        page.wait_for_timeout(700)
        page.click("#setup-submit")

        # ---- URL共有 ----
        page.wait_for_selector(".go-game-btn", state="visible", timeout=15000)
        page.wait_for_timeout(2300)
        page.click(".go-game-btn")
        page.wait_for_timeout(1500)

        # ---- 点数入力（1試合目） ----
        page.click(".fab")
        page.wait_for_selector("#si-0", state="visible", timeout=10000)
        page.wait_for_timeout(700)
        for i, val in enumerate(["483", "267", "182"]):
            page.click(f"#si-{i}")
            page.locator(f"#si-{i}").press_sequentially(val, delay=130)
            page.wait_for_timeout(200)
        page.wait_for_timeout(500)
        page.click("#auto-btn")  # 残り1人を自動入力
        page.wait_for_timeout(900)
        page.click("#confirm-btn")
        page.wait_for_selector("#score-main-body .score-card", state="visible", timeout=10000)
        page.wait_for_timeout(2200)  # メダル付きの総合成績を見せる

        # ---- 2・3試合目はデータ注入（リアルタイム反映のデモを兼ねる） ----
        settings = page.evaluate("activeGame.settings")
        extra = []
        for pts, at in [([31200, 35600, 20400, 12800], "2026-07-17T12:05:00.000Z"),
                        ([42100, 8900, 27600, 21400], "2026-07-17T12:50:00.000Z")]:
            extra.append({"points": pts, "scores": calc_scores(pts, settings),
                          "members": [0, 1, 2, 3], "at": at})
        page.evaluate("""(extra) => {
            const rounds = [...activeGame.rounds, ...extra];
            return firebase.database().ref('sessions/' + sessionId).update({ rounds });
        }""", extra)
        page.wait_for_timeout(1800)

        # ---- 成績・グラフを順に見せる ----
        smooth_scroll_to(page, "#score-main-body", 90, 1600)
        smooth_scroll_to(page, "#rank-card", 70, 1800)   # その他成績
        smooth_scroll_to(page, "#chart-card", 70, 2600)  # スコア推移グラフ
        page.wait_for_timeout(400)

        video = page.video
        ctx.close()  # ここで動画が書き出される
        raw_webm = video.path()
        browser.close()
    server.shutdown()
    return raw_webm


def main():
    raw_webm = record()
    ff = ffmpeg_exe()

    raw_mp4 = os.path.join(OUTDIR, "demo-raw.mp4")
    subprocess.run([ff, "-y", "-i", raw_webm,
                    "-vf", f"scale={VIEW_W * 2}:{VIEW_H * 2}:flags=lanczos",
                    "-c:v", "libx264", "-crf", "20",
                    "-pix_fmt", "yuv420p", "-movflags", "+faststart", raw_mp4],
                   check=True, capture_output=True)
    os.remove(raw_webm)

    # 元動画の長さを取得して -t で明示（-loop 1 の静止画入力が混ざるため、
    # shortest=1 を全overlayに付けた上で出力長も固定しないとエンコードが終わらない）
    probe = subprocess.run([ff, "-i", raw_mp4], capture_output=True, text=True)
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", probe.stderr)
    assert m, "動画の長さを取得できない"
    duration = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))

    bg_path, frame_path = build_overlay_images()
    short_mp4 = os.path.join(OUTDIR, "demo-short-9x16.mp4")
    fc = (f"[1:v]scale={SCREEN_W}:{SCREEN_H}:flags=lanczos[scr];"
          f"[0:v][scr]overlay={SCREEN_X}:{SCREEN_Y}:shortest=1[t1];"
          f"[t1][2:v]overlay=0:0:shortest=1,format=yuv420p")
    subprocess.run([ff, "-y", "-loop", "1", "-i", bg_path, "-i", raw_mp4,
                    "-loop", "1", "-i", frame_path, "-filter_complex", fc,
                    "-t", f"{duration:.2f}", "-r", "30", "-c:v", "libx264", "-crf", "20",
                    "-movflags", "+faststart", short_mp4],
                   check=True, capture_output=True)
    print("saved:", raw_mp4)
    print("saved:", short_mp4)


if __name__ == "__main__":
    main()
