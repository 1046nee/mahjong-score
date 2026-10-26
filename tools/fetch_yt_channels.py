# -*- coding: utf-8 -*-
"""ブログに出すYouTubeチャンネルのアイコンと登録者数を、YouTube Data API で取り直して記事に書き込む（2026-10-22〜）。

YouTube API の開発者ポリシーで、APIで取ったデータ（アイコン・登録者数）は30日をこえて置いておけない。
**月に1回このスクリプトを実行して push する**（Notionの運用タスクに毎月の行がある）。

- APIキーは秘密なので tools/.youtube-api-key（1行・.gitignore 済み）か環境変数 YOUTUBE_API_KEY に置く。チャットやリポジトリに書かない
- 記事の中の次の3か所を、HTMLに書いてあるチャンネルのURLから探して書き換える（新しいチャンネルを足すときもURLを書くだけでよい）
  1. チャンネル紹介の行 .ch-card … アイコン（チャンネルへのリンク）・「登録者 ○人（○年○月）」・YouTubeのアイコン
  2. Mリーグのチーム表 a.tm-yt … チームの公式チャンネルのアイコン（チャンネルへのリンク）
  3. 団体カードのYouTubeのリンク … 「公式YouTube（登録者 ○人）」
  4. 団体カードの見出し .org-ic … 団体の公式チャンネルのアイコン（YouTubeが無い団体は公式サイトのアイコン＝Googleのfavicon配信。それも無ければ団体の色の丸に頭文字）
- YouTubeのアイコンは Google が配っている公式の画像（gstatic）をそのまま使う。色や形は変えない（ブランドガイドライン）
- 取ってきた内容は tools/yt_channels.json にも残す（いつ取ったかの記録）
実行: python tools/fetch_yt_channels.py
"""
import glob, html, io, json, os, re, sys, urllib.parse, urllib.request
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
YT_ICON = "https://www.gstatic.com/youtube/img/branding/favicon/favicon_144x144.png"
URL_RE = r"https://www\.youtube\.com/(?:@[^\"/?#]+|channel/UC[\w-]+)"


def api_key():
    k = os.environ.get("YOUTUBE_API_KEY", "").strip()
    f = os.path.join(HERE, ".youtube-api-key")
    if not k and os.path.exists(f):
        k = open(f, encoding="utf-8").read().strip()
    if not k:
        sys.exit("APIキーがありません。tools/.youtube-api-key に1行で保存してください")
    return k


def api(key, path, **q):
    q["key"] = key
    u = "https://www.googleapis.com/youtube/v3/" + path + "?" + urllib.parse.urlencode(q)
    return json.loads(urllib.request.urlopen(u, timeout=30).read().decode("utf-8"))


def fmt_subs(n):
    """YouTubeの画面と同じ見せ方（38.2万人・7,610人）"""
    if n >= 10000:
        v = n / 10000
        return (f"{v:.3g}" if v < 1000 else f"{v:.0f}") + "万人"
    return f"{n:,}人"


def fetch(key, urls):
    out = {}
    ids = {}
    for u in urls:
        ref = u.split("youtube.com/")[1]
        if ref.startswith("@"):
            d = api(key, "channels", part="snippet,statistics", forHandle=urllib.parse.unquote(ref))
            items = d.get("items") or []
            if not items:
                print("見つからない", u); continue
            out[u] = items[0]
        else:
            ids[ref.split("/")[1]] = u
    lst = list(ids)
    for i in range(0, len(lst), 50):
        d = api(key, "channels", part="snippet,statistics", id=",".join(lst[i:i + 50]))
        for it in d.get("items") or []:
            out[ids[it["id"]]] = it
    res = {}
    for u, it in out.items():
        st = it.get("statistics", {})
        th = it["snippet"]["thumbnails"]
        res[u] = {"id": it["id"], "title": it["snippet"]["title"],
                  "thumb": (th.get("default") or th.get("medium"))["url"],
                  "subs": None if st.get("hiddenSubscriberCount") else int(st.get("subscriberCount", 0))}
    return res


def rewrite(s, data, month):
    def icon(u, cls):
        c = data[u]
        return (f'<a class="{cls}" href="{u}" target="_blank" rel="noopener" title="{html.escape(c["title"])}（YouTube）">'
                f'<img src="{c["thumb"]}" alt="{html.escape(c["title"])}のチャンネルのアイコン" width="40" height="40" loading="lazy" referrerpolicy="no-referrer"></a>')

    # 1. チャンネル紹介の行
    def card(m):
        body, u = m.group(0), m.group(2)
        if u not in data:
            return body
        body = body.replace(m.group(1), icon(u, "ch-ic"), 1)
        if data[u]["subs"] is not None:
            body = re.sub(r'<span class="ch-meta">登録者 [^<（]*（[^）]*）</span>',
                          f'<span class="ch-meta">登録者 {fmt_subs(data[u]["subs"])}（{month}）</span>', body, count=1)
        body = re.sub(r'<small>(?:<img class="yt-ico"[^>]*>)?YouTubeでチャンネルを見る</small>',
                      f'<small><img class="yt-ico" src="{YT_ICON}" alt="YouTube" width="16" height="16">YouTubeでチャンネルを見る</small>', body, count=1)
        return body
    s = re.sub(r'<div class="ch-card">(<span class="ch-ic"[^>]*>.*?</span>|<a class="ch-ic".*?</a>).*?<a class="ch-url" href="(' + URL_RE + r')"[^>]*><small>(?:<img class="yt-ico"[^>]*>)?YouTubeでチャンネルを見る</small>', card, s, flags=re.S)

    # 2. チーム表のチャンネルのアイコン
    s = re.sub(r'<a class="tm-yt" href="(' + URL_RE + r')".*?</a>', lambda m: icon(m.group(1), "tm-yt") if m.group(1) in data else m.group(0), s, flags=re.S)

    # 3. 団体カードの登録者数
    def org(m):
        u = m.group(1)
        if u not in data or data[u]["subs"] is None:
            return m.group(0)
        return m.group(0).replace(m.group(2), fmt_subs(data[u]["subs"]))
    s = re.sub(r'<a class="ch-url" href="(' + URL_RE + r')"[^>]*><small>公式YouTube（登録者 ([^）]+)）</small>', org, s)

    # 4. 団体カードの見出しのアイコン（その団体の公式YouTubeチャンネルのアイコン。YouTubeが無い団体は団体の色の丸に頭文字）
    def org_card(m):
        card = m.group(0)
        yt = re.search(r'<a class="ch-url" href="(' + URL_RE + r')"', card)
        head = re.search(r'<div class="org-head">(?:<a class="org-ic".*?</a>|<span class="org-ic"[^>]*>.*?</span>)?(?:<span class="org-name">)?(<b>.*?</b>(?:<small>.*?</small>)?)(?:</span>)?</div>', card, re.S)
        if not head:
            return card
        if yt and yt.group(1) in data:
            ic = icon(yt.group(1), "org-ic")
        else:
            name = re.sub(r"<[^>]+>", "", re.search(r"<b>(.*?)</b>", head.group(1)).group(1))
            site = re.search(r'<a class="ch-url" href="(https?://(?!(?:www\.)?(?:youtube\.com|x\.com))([^/"]+)[^"]*)"', card)
            if site:  # YouTubeが無い団体は、公式サイトのアイコン（ブラウザのタブに出る小さな印）を Google の favicon の配信から表示する（保存して置かない）
                ic = (f'<a class="org-ic site" href="{site.group(1)}" target="_blank" rel="noopener" title="{html.escape(name)}（公式サイト）">'
                      f'<img src="https://www.google.com/s2/favicons?domain={site.group(2)}&amp;sz=64" alt="{html.escape(name)}の公式サイトのアイコン" width="40" height="40" loading="lazy" referrerpolicy="no-referrer"></a>')
            else:
                ic = f'<span class="org-ic" aria-hidden="true">{name[0]}</span>'
        return card.replace(head.group(0), f'<div class="org-head">{ic}<span class="org-name">{head.group(1)}</span></div>', 1)
    s = re.sub(r'<div class="org-card".*?<div class="org-links">.*?</div>', org_card, s, flags=re.S)
    return s


def main():
    key = api_key()
    files = sorted(glob.glob(os.path.join(ROOT, "blog-*.html")) + glob.glob(os.path.join(ROOT, "news", "*.html")))
    pages = {f: io.open(f, encoding="utf-8").read() for f in files}
    urls = set()
    for s in pages.values():
        for blk in re.findall(r'<div class="ch-card">.*?<a class="ch-url" href="(' + URL_RE + r')"', s, flags=re.S):
            urls.add(blk)
        urls.update(re.findall(r'<a class="tm-yt" href="(' + URL_RE + r')"', s))
        urls.update(re.findall(r'<a class="ch-url" href="(' + URL_RE + r')"[^>]*><small>公式YouTube', s))
    data = fetch(key, sorted(urls))
    today = date.today()
    month = f"{today.year}年{today.month}月"
    n = 0
    for f, s in pages.items():
        t = rewrite(s, data, month)
        if t != s:
            io.open(f, "w", encoding="utf-8", newline="").write(t); n += 1
            print("書き換え", os.path.basename(f))
    io.open(os.path.join(HERE, "yt_channels.json"), "w", encoding="utf-8").write(
        json.dumps({"fetched": today.isoformat(), "channels": data}, ensure_ascii=False, indent=1))
    print(f"{len(data)}/{len(urls)} チャンネル・{n} ページ（{today.isoformat()} 取得。30日以内に取り直す）")


if __name__ == "__main__":
    main()
