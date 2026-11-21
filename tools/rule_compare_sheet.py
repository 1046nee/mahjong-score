# -*- coding: utf-8 -*-
"""打つ前に決めるルールのチェックシート（A4縦1枚。SNSの投稿用。2026-11-20 ユーザーの依頼）。
2列に、事前に決めておきたい項目を並べ、選択肢ごとにMリーグのロゴと雀魂のアイコンの印で、どちらがどれを選んでいるかを見せる。
比べる表ではなく、チェックシート。文字・選択肢はぎゅっと詰めてよい（ユーザーの指定）。
出典: Mリーグ＝公式サイト m-league.jp/about の公式戦ルール（2026-11-20 に確認）。雀魂＝Wikipedia「雀魂」の段位戦のルールと、blog-yakuman-rules の表。
確かめられなかったもの・規定がないものは札を付けず、項目の右に小さく書く。
出力: まじゃすこ素材/x/rule-hikaku/rule-check.png（1588×2382＝縦横2:3。項目が増えたのでA4から縦に伸ばした。2026-11-21）
実行: python tools/rule_compare_sheet.py
"""
import io, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sheet_logo import LOGO_CSS, logo_html  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "まじゃすこ素材", "x", "rule-hikaku")

# 選択肢の印: "M"＝Mリーグ・"J"＝雀魂。項目は (名前, [(選択肢, 印), ...], 補足)
LEFT = [
    ("##", "試合と点数"),
    ("試合形式", [("半荘", "MJ"), ("東風", "J")], "雀魂は東風・半荘を選ぶ"),
    ("西入（延長）", [("なし", "M"), ("あり", "J")], "雀魂はトップが30,000点未満のとき"),
    ("持ち点／返し点", [("25,000／30,000", "M"), ("25,000／25,000", "J")], ""),
    ("ウマ", [("10-30", "M"), ("10-20", ""), ("5-15", "J"), ("なし", "")], ""),
    ("同点のとき", [("同着", "M"), ("上家取り", "J")], "上家取り＝起家に近い人が上"),
    ("終了時の供託", [("トップ", "MJ"), ("誰も取らない", ""), ("出した人に", "")], "流局で終わったとき"),
    ("チョンボ", [("罰符なし", ""), ("スコアから引く", "M"), ("満貫払い", ""), ("供託1,000点", "")], "M＝−20pt。雀魂はチョンボがない"),
    ("チップ・祝儀", [("なし", "MJ"), ("一発・裏・赤", ""), ("役満", "")], ""),
    ("焼き鳥", [("なし", "MJ"), ("あり", "")], ""),
    ("##", "鳴き・アガリ"),
    ("赤ドラ", [("なし", ""), ("3枚", "MJ")], ""),
    ("喰いタン", [("あり", "MJ"), ("なし", "")], ""),
    ("後付け", [("あり", "MJ"), ("なし", "")], ""),
    ("喰い替え", [("禁止", "MJ"), ("あり", "")], "同じ牌・スジ"),
    ("2人が同時にロン", [("頭ハネ", "M"), ("ダブロン", "J")], ""),
    ("3人が同時にロン", [("頭ハネ", "M"), ("トリロン", "J"), ("流局", "")], ""),
    ("連荘", [("テンパイ連荘", "MJ"), ("アガリ連荘だけ", "")], ""),
    ("アガリやめ", [("あり", "J"), ("なし", "M")], ""),
]
RIGHT = [
    ("##", "リーチとトビ"),
    ("ツモ番がないリーチ", [("できる", "M"), ("できない", "J")], ""),
    ("0点・マイナスのリーチ", [("できる", "M"), ("1,000点未満は不可", "J")], ""),
    ("トビ", [("なし", "M"), ("0点未満で終了", "J"), ("0点で終了", "")], ""),
    ("トビ賞", [("なし", "MJ"), ("あり", "")], ""),
    ("##", "ローカル役・途中流局"),
    ("流し満貫", [("なし", "M"), ("満貫", "J")], ""),
    ("途中流局", [("なし", "M"), ("あり", "J")], "九種九牌・四風連打・四家立直・四開槓"),
    ("人和", [("なし", "MJ"), ("満貫", ""), ("役満", "")], "雀魂は友人戦で設定"),
    ("##", "役満"),
    ("形でダブル役満", [("なし", "M"), ("あり", "J")], "四暗刻単騎・国士13面・純正九蓮・大四喜"),
    ("役満が2つ重なる", [("2倍", "MJ"), ("1倍", "")], ""),
    ("数え役満", [("なし", "M"), ("あり", "J")], ""),
    ("国士で暗槓をロン", [("できない", "M"), ("できる", "J")], ""),
    ("##", "カン"),
    ("カンドラのタイミング", [("すぐ", "M"), ("暗槓すぐ・明槓は打牌後", "J")], ""),
    ("パオ", [("なし", ""), ("大三元・大四喜", "J"), ("＋四槓子", "M")], ""),
    ("リーチ後のカン", [("面子が変わらない暗槓のみ", "MJ"), ("待ちが変わらない暗槓のみ", "")], ""),      # 雀魂もMリーグと同じ（2026-11-20 ユーザーの指摘）
    # 2026-11-21 ユーザーの指摘で足した（連風牌）。ほかの抜け（切り上げ満貫・西入）も確かめて足した。
    # 出典: Mリーグ公式サイト（連風牌の対子も2符・西入の規定なし。切り上げ満貫はあり＝ユーザーの指摘）、Wikipedia「雀魂」（連風牌の雀頭は4符・30符4飜は切り上げない・トップが30,000点未満なら西入）
    ("##", "符と満貫"),
    ("連風牌の雀頭", [("2符", "M"), ("4符", "J")], "場風＝自風の牌（東場の東家の東）"),
    ("切り上げ満貫", [("あり", "M"), ("なし", "J")], "30符4翻・60符3翻を満貫にするか")      # Mリーグはあり（2026-11-21 ユーザーの指摘）,
]


# 印は本物のロゴ・アイコン（2026-11-20 ユーザーの判断で使う。元の画像は非公開の素材リポジトリ まじゃすこ素材/x/rule-hikaku/src/ だけに置く）。
# Mリーグ＝公式ロゴのマーク部分（文字は切る）。雀魂＝アプリのアイコンの顔の部分を丸く切る
SRC = os.path.join(OUT, "src")
def _uri(im):
    import base64; buf = io.BytesIO(); im.save(buf, "PNG"); return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
def _icons():
    from PIL import Image
    m = Image.open(os.path.join(SRC, "mleague.png")).convert("RGBA").crop((338, 28, 689, 474))
    px = m.load()                                                     # 白い地は透かす（色の札の上に白い四角が出ないように）
    for y in range(m.height):
        for x in range(m.width):
            r, g, b_, al = px[x, y]
            if min(r, g, b_) > 235: px[x, y] = (255, 255, 255, 0)
    m = m.resize((round(m.width * 96 / m.height), 96), Image.LANCZOS)
    j = Image.open(os.path.join(SRC, "jantama.jpg")).convert("RGB").crop((125, 125, 405, 405)).resize((96, 96), Image.LANCZOS)
    return _uri(m), _uri(j)
ICON_M, ICON_J = _icons()
def badge(k): return {"M": f'<i class="bm" title="Mリーグ"><img src="{ICON_M}"></i>', "J": f'<i class="bj" title="雀魂"><img src="{ICON_J}"></i>'}[k]
# 色は3つの意味だけに絞る（2026-11-20 ユーザーの指定「違う所を目立たせる・色をいい感じに」）:
#   オレンジの行＝Mリーグと雀魂でルールが違う項目（それぞれ別の選択肢に印がある）／緑の札＝両方同じ／紺の札＝Mリーグだけ・紫の札＝雀魂だけ
def is_one(opts): return any(m for _, m in opts)
def is_same(opts): return any("M" in m and "J" in m for _, m in opts)
def is_diff(opts): return any("M" in m and "J" not in m for _, m in opts) and any("J" in m and "M" not in m for _, m in opts)
N_DIFF = 0


def col(items):
    out = ""
    for it in items:
        if it[0] == "##":
            out += f'<h2>{it[1]}</h2>'; continue
        name, opts, note = it
        d = is_diff(opts); sm = not d and is_same(opts); one = not d and not sm and is_one(opts)
        chips = "".join(f'<span class="op{" m" * ("M" in m and "J" not in m)}{" j" * ("J" in m and "M" not in m)}{" mj" * ("M" in m and "J" in m)}">{t}{"".join(badge(k) for k in m)}</span>' for t, m in opts)
        out += (f'<div class="it{" diff" * d}{" same" * sm}{" one" * one}"><b><i class="cb"></i><span>{name}{"<em><i>!</i>違う・要チェック</em>" if d else ""}</span></b>'
                f'<div class="ops">{chips}</div>{f"<small>{note}</small>" if note else ""}</div>')
    return out
N_DIFF = sum(1 for it in LEFT + RIGHT if it[0] != "##" and is_diff(it[1]))


def html():
    return f"""<!doctype html><html lang="ja"><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700;900&display=block" rel="stylesheet">
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
html, body {{ width: 794px; height: 1191px; }}
body {{ font-family: 'Noto Sans JP', sans-serif; color: #1F2A28; background: #EEF6F3; padding: 10px 24px 18px; position: relative; font-feature-settings: "palt"; }}
header {{ display: flex; align-items: center; justify-content: space-between; background: #177083; color: #fff; border-radius: 8px; padding: 9px 16px; margin-bottom: 7px; }}
header h1 {{ font-size: 25px; font-weight: 900; line-height: 1.15; }}
header h1 small {{ display: block; font-size: 12.5px; font-weight: 700; color: #DDF0EC; margin-top: 4px; }}
header h1 small b {{ color: #FFD0B5; }}
.legend {{ font-size: 11.5px; font-weight: 800; white-space: nowrap; margin-left: auto; margin-right: 12px; display: flex; flex-direction: column; gap: 6px; }} .legend > span {{ display: flex; align-items: center; gap: 6px; }}      /* 2つのアイコンが上下で重なっていた（2026-11-20 ユーザーの指摘） */
.legend i {{ margin-right: 3px; }}
{LOGO_CSS}
i.bm, i.bj {{ --d: 17px; font-style: normal; display: inline-flex; align-items: center; justify-content: center; width: var(--d); height: var(--d); border-radius: 50%; overflow: hidden; background: #fff; box-shadow: 0 0 0 1.5px #fff, 0 0 0 2.3px rgba(0,0,0,.12); margin-left: 4px; flex: none; }}
i.bm img {{ height: 72%; width: auto; display: block; }}
i.bm + i.bj {{ margin-left: 6px; }}      /* 2つ並ぶとき白い縁どうしが重ならない間 */
i.bj img {{ width: 100%; height: 100%; display: block; }}
.legend i.bm, .legend i.bj {{ --d: 22px; margin: 0; }}
.key {{ display: flex; align-items: center; gap: 14px; font-size: 11px; font-weight: 800; color: #4F5C5A; margin: 0 2px 5px; }}
.key .op {{ font-size: 10.5px; padding: 0 7px; }} .key .sw {{ display: inline-flex; align-items: center; gap: 5px; }}
.key .dsw {{ display: inline-block; width: 26px; height: 14px; border-radius: 3px; background: #FFE1CE; border: 2.5px solid #E75620; box-shadow: 0 0 0 2px rgba(231, 86, 32, .2); }} .key .ssw {{ display: inline-block; width: 26px; height: 14px; border-radius: 3px; background: #E3F4EC; border: 1.5px solid #7CC3A6; }}
.grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }}
.colw {{ background: #fff; border: 2px solid #177083; border-radius: 8px; padding: 2px 8px 6px; }}
h2 {{ font-size: 15px; font-weight: 900; color: #fff; background: #177083; margin: 7px -8px 4px; padding: 3px 12px; letter-spacing: .03em; }}
.colw h2:first-child {{ margin-top: -2px; border-radius: 6px 6px 0 0; }}
.it {{ display: grid; grid-template-columns: var(--nw) 1fr; column-gap: 6px; align-items: center; padding: 4.5px 6px; margin: 0 -4px; border-top: 1px solid #E3ECEA; border-radius: 6px; }}
h2 + .it {{ border-top: 0; }}
.it.one {{ background: #F3F6F5; border: 1.5px solid #C5D3CF; padding: 4px 4.5px; }}      /* 片方の規定だけの行（チョンボ）も囲う（2026-11-21 ユーザーの指摘） */
.it.same {{ background: #E3F4EC; border: 1.5px solid #7CC3A6; padding: 4px 4.5px; }}      /* 同じ行も枠で囲う（2026-11-20 ユーザーの指定） */
.it.diff {{ background: #FFE1CE; border: 3px solid #E75620; padding: 2.5px 3px; box-shadow: 0 0 0 3px rgba(231, 86, 32, .2); }}      /* 違う行＝要チェック: 太い枠＋外の光＋「!」の札（2026-11-20 ユーザーの指定） */
.it.diff + .it:not(.diff), .it.same + .it:not(.diff), .it.one + .it:not(.diff) {{ border-top-color: transparent; }}      /* 違う行の上の線は消さない（オレンジの枠が切れた。2026-11-20 ユーザーの指摘） */ .it.diff + .it, .it.same + .it.same, .it + .it.diff, .it.same + .it.diff, .it.diff + .it.diff, .it.one, .it.one + .it {{ margin-top: 4.5px; }}
.it > b {{ font-size: 13.5px; font-weight: 900; line-height: 1.25; white-space: nowrap; display: flex; align-items: flex-start; gap: 5px; }}
.it > b em {{ display: flex; align-items: center; gap: 3px; width: fit-content; font-style: normal; font-size: 10px; font-weight: 900; color: #fff; background: #E75620; border-radius: 4px; padding: 0 6px 0 2px; margin-top: 2px; }}
.it > b em i {{ font-style: normal; display: inline-flex; align-items: center; justify-content: center; width: 12px; height: 12px; border-radius: 50%; background: #fff; color: #E75620; font-size: 10px; font-weight: 900; }}
.it.diff i.cb {{ border-width: 2.5px; }}
.it.diff > b {{ color: #B23A0E; }}
i.cb {{ flex: none; width: 13px; height: 13px; border: 2px solid #177083; border-radius: 3px; margin-top: 1px; background: #fff; }}
.it.diff i.cb {{ border-color: #E75620; }}
.ops {{ display: flex; flex-wrap: wrap; gap: 3px; }}
.op {{ font-size: 12px; font-weight: 800; border: 1.5px solid #D5E0DD; border-radius: 12px; padding: 0 7px 0 8px; color: #6B7A77; background: #fff; white-space: nowrap; display: inline-flex; align-items: center; }}
.op.m {{ border-color: #2F3B57; color: #fff; background: #3E4C66; }}
.op.j {{ border-color: #6E4CC4; color: #fff; background: #7E5AD2; }}
.op.mj {{ border-color: #1F7A5C; color: #fff; background: #23866A; }}
.it > small {{ grid-column: 2; white-space: nowrap; font-size: 11px; font-weight: 700; color: #6B7A77; margin-top: 2px; }}
.note {{ font-size: 11px; font-weight: 700; color: #4F5C5A; line-height: 1.55; margin-top: 7px; }}
.note b {{ color: #E75620; }}
footer {{ position: absolute; left: 24px; right: 24px; bottom: 7px; display: flex; justify-content: space-between; font-size: 10px; color: #8A9A97; }}
footer b {{ color: #177083; font-weight: 900; }}
</style></head><body>
<header><h1>打つ前に決める ルールチェックシート<small>Mリーグと雀魂は、どれを選んでいる？　<b>ルールが違うのは{N_DIFF}項目</b></small></h1>
<div class="legend"><span>{badge("M")}Mリーグ</span><span>{badge("J")}雀魂（段位戦）</span></div>{logo_html()}</header>
<div class="key"><span class="sw"><i class="dsw"></i>ルールが違う＝要チェック</span><span class="sw"><i class="ssw"></i>同じ</span><span class="sw"><span class="op mj">両方</span></span><span class="sw"><span class="op m">Mリーグだけ</span></span><span class="sw"><span class="op j">雀魂だけ</span></span><span class="sw"><span class="op">どちらでもない</span></span></div>
<div class="grid"><div class="colw" style="--nw:124px">{col(LEFT)}</div><div class="colw" style="--nw:158px">{col(RIGHT)}</div></div>
<p class="note"><b>□にチェックして、仲間内のルールを決めよう。</b>Mリーグは公式サイトの公式戦ルール、雀魂はWikipedia「雀魂」の段位戦のルールなどによる（2026年11月）。印が無い所は、規定がないか確かめられなかった所。ゲームのルールは変わることがある。</p>
<footer><span>麻雀スコア記録アプリ <b>まじゃすこ</b>　majasco.jp</span><span>決めたルールで打ったら、スコアはまじゃすこで</span></footer>
</body></html>"""


def render():
    from playwright.sync_api import sync_playwright
    os.makedirs(OUT, exist_ok=True)
    hp = os.path.join(OUT, "_p.html"); io.open(hp, "w", encoding="utf-8").write(html())
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={"width": 794, "height": 1191}, device_scale_factor=2)
        pg.goto("file:///" + hp.replace("\\", "/")); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(1200)
        h = pg.evaluate("document.querySelector('footer').getBoundingClientRect().top - document.querySelector('.note').getBoundingClientRect().bottom")
        bad = pg.evaluate("""[...document.querySelectorAll('.it')].flatMap(it => {const o=[]; const b=it.querySelector('b'), ops=it.querySelector('.ops'), sm=it.querySelector('small');
          if (b.scrollWidth > b.clientWidth + 1 || b.getBoundingClientRect().right > ops.getBoundingClientRect().left) o.push('名前:'+b.textContent);
          [...ops.children].forEach(c => { if (c.getBoundingClientRect().height > 24) o.push('札の中で改行:'+c.textContent); });
          if (sm && sm.getBoundingClientRect().right > it.getBoundingClientRect().right + 1) o.push('補足:'+b.textContent);
          if (ops.getBoundingClientRect().right > it.getBoundingClientRect().right + 1) o.push('はみ出し:'+b.textContent); return o;})""")
        print("改行・はみ出し", bad); assert not bad, bad
        ov = pg.evaluate("""(() => { const sel = 'i.bm, i.bj, .op, .it > b, .it > b em, .legend > span, .key > span, h2, header h1, .logo-pill';
          const els = [...document.querySelectorAll(sel)]; const out = [];
          const r = e => { const b = e.getBoundingClientRect(); const s = e.matches('i.bm, i.bj') ? 2.3 : 0; return {l: b.left - s, r: b.right + s, t: b.top - s, b: b.bottom + s}; };
          for (let i = 0; i < els.length; i++) for (let j = i + 1; j < els.length; j++) {
            const a = els[i], c = els[j]; if (a.contains(c) || c.contains(a)) continue;
            const x = r(a), y = r(c); if (x.l < y.r - .5 && y.l < x.r - .5 && x.t < y.b - .5 && y.t < x.b - .5) out.push((a.className || a.tagName) + ':' + a.textContent.slice(0, 8) + ' × ' + (c.className || c.tagName) + ':' + c.textContent.slice(0, 8)); }
          return out; })()""")
        print("重なり", ov); assert not ov, ov
        print("余白", round(h)); pg.screenshot(path=os.path.join(OUT, "rule-check.png")); b.close()
    os.remove(hp)


if __name__ == "__main__":
    render()
