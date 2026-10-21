# -*- coding: utf-8 -*-
"""麻雀の本の記事（blog-mahjong-books.html）の表紙と商品リンクを、楽天ブックスAPIから取ってくる（2026-10-21）。

- applicationId は公開してよい値（下に書く）。accessKey は秘密なので、
  環境変数 RAKUTEN_ACCESS_KEY か tools/.rakuten-access-key（1行・.gitignore 済み）に置く。チャットやリポジトリには書かない
- 取ってきた表紙の画像URLとアフィリエイトの商品URLを tools/book_covers.json に保存する（公開してよい値だけ）
- 記事を作り直すときに、この JSON を読んで表紙を並べる。サイトを見る人のブラウザからAPIは呼ばない
実行: python tools/fetch_book_covers.py
"""
import io, json, os, sys, time, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
APP_ID = "32b1dbb9-9166-4044-9715-d2235a92c1da"
AFF_ID = "5883828c.bd79974c.5883828d.65e0755a"
ISBNS = [
    "9784262107332", "9784528024229", "9784048118569", "9784801930988", "9784910825014", "9784866731117", "9784046075697",
    "9784861998942", "9784861999840", "9784865371987", "9784801918252", "9784865372083", "9784839991500",
    "9784865372663", "9784798626048", "9784801911802", "9784866730875", "9784839984205", "9784801926851",
]


def access_key():
    k = os.environ.get("RAKUTEN_ACCESS_KEY", "").strip()
    f = os.path.join(HERE, ".rakuten-access-key")
    if not k and os.path.exists(f):
        k = open(f, encoding="utf-8").read().strip()
    if not k:
        sys.exit("accessKey がありません。tools/.rakuten-access-key に1行で保存してください")
    return k


def main():
    key = access_key()
    out = {}
    for isbn in ISBNS:
        q = urllib.parse.urlencode({"format": "json", "applicationId": APP_ID, "affiliateId": AFF_ID, "isbn": isbn, "hits": 1})
        req = urllib.request.Request("https://openapi.rakuten.co.jp/services/api/BooksBook/Search/20170404?" + q,
                                     headers={"accessKey": key, "Referer": "https://majasco.jp/", "Origin": "https://majasco.jp"})
        try:
            d = json.loads(urllib.request.urlopen(req, timeout=30).read().decode("utf-8"))
        except Exception as e:
            print("ERR", isbn, str(e)[:120]); continue
        items = d.get("Items") or d.get("items") or []
        if not items:
            print("なし", isbn); continue
        it = items[0].get("Item", items[0])
        out[isbn] = {"title": it.get("title"), "image": it.get("largeImageUrl") or it.get("mediumImageUrl"),
                     "url": it.get("affiliateUrl") or it.get("itemUrl")}
        print("OK", isbn, it.get("title"))
        time.sleep(1.1)  # 1秒に1回まで
    io.open(os.path.join(HERE, "book_covers.json"), "w", encoding="utf-8").write(json.dumps(out, ensure_ascii=False, indent=1))
    print(len(out), "冊 →", os.path.join(HERE, "book_covers.json"))


if __name__ == "__main__":
    main()
