# -*- coding: utf-8 -*-
"""麻雀漫画の記事の、1巻の表紙・著者・出版社・発売日・アフィリエイトの商品URLを楽天ブックスAPIから取る（2026-10-27）。
fetch_book_covers.py と同じ鍵（applicationId は公開してよい値・accessKey は tools/.rakuten-access-key）。
タイトルで探して、候補を出す → MANGA の isbn を決めたら、ISBNで取り直して tools/manga_covers.json に保存する。
実行: python tools/fetch_manga_covers.py search   （候補を見る）
      python tools/fetch_manga_covers.py           （MANGA の ISBN で取って保存）
"""
import io, json, os, sys, time, urllib.parse, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch_book_covers import APP_ID, AFF_ID, access_key

HERE = os.path.dirname(os.path.abspath(__file__))
API = "https://openapi.rakuten.co.jp/services/api/BooksBook/Search/20170404?"

# (記事での名前, 探す言葉, 著者の一部, 1巻のISBN)
MANGA = [
 ("咲-Saki-", "咲", "小林", "9784757517820"),
 ("アカギ", "アカギ", "福本", "9784884755744"),
 ("天 天和通りの快男児", "天和通りの快男児", "福本", "9784801953215"),
 ("哲也 雀聖と呼ばれた男", "哲也", "星野", ""),
 ("兎 野性の闘牌", "兎 野性の闘牌 1", "伊藤", "9784801959927"),
 ("麻雀飛翔伝 哭きの竜", "哭きの竜", "能條", ""),
 ("ノーマーク爆牌党", "爆牌党", "片山", ""),
 ("打姫オバカミーコ", "オバカミーコ", "片山", ""),
 ("ムダヅモ無き改革", "ムダヅモ", "大和田", "9784801961821"),
 ("東大を出たけれど", "東大を出たけれど", "須田", ""),
 ("鉄鳴きの麒麟児", "麒麟児", "", ""),
 ("ぽんのみち", "ぽんのみち", "", ""),
 ("咲-Saki- 阿知賀編", "阿知賀編", "五十嵐", "9784757535350"),
 ("シノハユ", "シノハユ", "", "9784757541849"),
]


def get(params, key):
    q = urllib.parse.urlencode({"format": "json", "applicationId": APP_ID, "affiliateId": AFF_ID, **params})
    req = urllib.request.Request(API + q, headers={"accessKey": key, "Referer": "https://majasco.jp/", "Origin": "https://majasco.jp"})
    return json.loads(urllib.request.urlopen(req, timeout=30).read().decode("utf-8"))


def main():
    key = access_key()
    if len(sys.argv) > 1 and sys.argv[1] == "search":
        for name, q, au, _ in MANGA:
            d = get({"title": q, "hits": 8, "sort": "+releaseDate", "booksGenreId": "001001"}, key)
            print("==", name)
            for it in d.get("Items", []):
                i = it["Item"]
                if au and au not in i.get("author", ""):
                    continue
                print("  ", i["isbn"], i["title"], "|", i["author"], "|", i["publisherName"], "|", i["salesDate"])
            time.sleep(1.1)
        return
    out = {}
    for name, q, au, isbn in MANGA:
        if not isbn:
            continue
        d = get({"isbn": isbn, "hits": 1}, key)
        if d.get("Items"):
            i = d["Items"][0]["Item"]
            out[name] = {k: i.get(k, "") for k in ("isbn", "title", "author", "publisherName", "salesDate", "largeImageUrl", "affiliateUrl", "itemUrl")}
            print("ok", name, i["title"])
        time.sleep(1.1)
    json.dump(out, io.open(os.path.join(HERE, "manga_covers.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
