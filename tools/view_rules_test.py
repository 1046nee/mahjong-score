# -*- coding: utf-8 -*-
"""見るだけのリンク（views / sessionViews）のセキュリティルールを、本番のRealtime Databaseで確かめる。

account_test.py はスタブ（ルールなし）なので、「見るだけのリンクを知っていても点数（写し）は書き換えられない」
「写しから試合IDは読めない」が本当にサーバーで効いているかはここでしか分からない。
ログインは使わない（アプリの見るだけのリンクもログインなしで動く）。検証用の試合を2つ作り、
REST API で読み書きを試して許可／拒否が期待どおりかを見る。最後に作ったデータを全部消す。

前提: database.rules.json をFirebaseコンソール（Realtime Database → ルール）に貼って「公開」してから実行する。
実行: python tools/view_rules_test.py
"""
import json
import random
import sys
import urllib.error
import urllib.request

DB = "https://mahjong-score-2e8aa-default-rtdb.asia-southeast1.firebasedatabase.app"
ID_CHARS = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz23456789"


def rnd(n):
    return "".join(random.choice(ID_CHARS) for _ in range(n))


def http(method, path, body=None):
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(f"{DB}/{path}.json", data=data, method=method, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, json.loads(r.read().decode("utf-8") or "null")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode("utf-8") or "null")
        except Exception:
            return e.code, None


def main():
    sid, other = rnd(10), rnd(10)
    vid, vid2 = rnd(12), rnd(12)
    game = lambda i: {"id": i, "name": "ルール確認用（自動で消えます）", "createdAt": "2026-09-26T00:00:00.000Z",
                      "settings": {"playerNames": ["A", "B", "C", "D"], "numPlayers": 4}}
    snap = lambda name: {"name": name, "createdAt": "2026-09-26T00:00:00.000Z", "settings": {"playerNames": ["A", "B", "C", "D"], "numPlayers": 4},
                         "rounds": [{"points": [40000, 30000, 20000, 10000], "scores": [50, 10, -20, -40]}], "h": "x", "lv": 1, "at": "2026-09-26T00:00:00.000Z"}
    results = []

    def check(label, expect_ok, st):
        ok = (200 <= st < 300) == expect_ok
        results.append((label, ok, st))

    try:
        assert http("PUT", f"sessions/{sid}", game(sid))[0] == 200, "検証用の試合を作れませんでした"
        assert http("PUT", f"sessions/{other}", game(other))[0] == 200
        n1 = rnd(12)
        # ---- 作る ----
        check("[1] 試合IDを知っている人は、見るだけのリンクを作れる（sessionViews と views をまとめて）", True,
              http("PATCH", "", {f"sessionViews/{sid}": vid, f"views/{vid}": {"p": f"{sid}_{n1}", "n": n1, "s": snap("最初")}})[0])
        check("[2] 同じ試合にもう1つ作る（sessionViews の上書き）は拒否", False, http("PUT", f"sessionViews/{sid}", rnd(12))[0])
        check("[3] 存在しない試合の見るだけのリンクは作れない", False,
              http("PATCH", "", {f"sessionViews/{rnd(10)}": vid2})[0])
        n9 = rnd(12)
        check("[4] 存在しない試合IDを入れた写しは作れない", False,
              http("PUT", f"views/{vid2}", {"p": f"{rnd(10)}_{n9}", "n": n9, "s": snap("x")})[0])
        # ---- 読む ----
        st, body = http("GET", f"views/{vid}/s")
        check("[5] 見るだけのリンクの写し（s）は誰でも読める", True, st if (body or {}).get("name") == "最初" else 500)
        check("[6] 写しの親（views/ID）は読めない＝試合IDの入った p は見えない", False, http("GET", f"views/{vid}")[0])
        check("[7] p は直接も読めない", False, http("GET", f"views/{vid}/p")[0])
        check("[8] n は直接も読めない", False, http("GET", f"views/{vid}/n")[0])
        st, body = http("GET", f"sessionViews/{sid}")
        check("[9] 試合IDを知っていれば、見るだけIDを引ける", True, st if body == vid else 500)
        st_v, st_s = http("GET", "views")[0], http("GET", "sessionViews")[0]
        check("[10] 一覧（views 全体・sessionViews 全体）は読めない", False, 200 if (st_v < 400 or st_s < 400) else 403)
        # ---- 書き換え（リンクしか知らない人） ----
        check("[11] リンクしか知らない人が写し（s）だけを書き換えるのは拒否", False, http("PUT", f"views/{vid}/s", snap("いたずら"))[0])
        check("[12] n を変えても、p（試合ID）を書かなければ拒否", False,
              http("PATCH", f"views/{vid}", {"n": rnd(12), "s": snap("いたずら")})[0])
        n2 = rnd(12)
        check("[13] 別の試合のIDで書き換える（乗っ取り）は拒否", False,
              http("PATCH", f"views/{vid}", {"p": f"{other}_{n2}", "n": n2, "s": snap("いたずら")})[0])
        check("[14] 写しの削除は拒否（試合がある間）", False, http("DELETE", f"views/{vid}")[0])
        check("[15] 写しに余計なキーは足せない", False, http("PATCH", f"views/{vid}", {"x": 1})[0])
        # ---- 書き換え（試合IDを知っている人＝アプリ） ----
        n3 = rnd(12)
        check("[16] 試合IDを知っている人は、n を変えて写しを更新できる", True,
              http("PATCH", f"views/{vid}", {"p": f"{sid}_{n3}", "n": n3, "s": snap("更新")})[0])
        check("[17] 同じ n のままの更新は拒否（p を書かずに済ませる抜け道をふさぐ）", False,
              http("PATCH", f"views/{vid}", {"p": f"{sid}_{n3}", "n": n3, "s": snap("更新2")})[0])
        st, body = http("GET", f"views/{vid}/s")
        check("[18] いたずらは反映されておらず、正しい更新だけが見える", True, st if (body or {}).get("name") == "更新" else 500)
    finally:
        # 後片付け: 試合を消すと、見るだけのリンクの写しと sessionViews も消せるようになる
        http("DELETE", f"sessions/{sid}")
        http("DELETE", f"sessions/{other}")
        a = http("DELETE", f"views/{vid}")[0]
        b = http("DELETE", f"sessionViews/{sid}")[0]
        results.append(("[19] 試合が消えたあとは、写しと sessionViews を片付けられる", a == 200 and b == 200, (a, b)))
        left = http("GET", f"views/{vid}/s")[1], http("GET", f"sessionViews/{sid}")[1], http("GET", f"sessions/{sid}")[1]
        results.append(("[20] 検証用のデータが残っていない", left == (None, None, None), left))

    ok = True
    for label, passed, st in results:
        ok &= passed
        print(("PASS  " if passed else "FAIL  ") + label + ("" if passed else f"（実際 {st}）"))
    print("VIEW RULES TEST:", "ALL PASS" if ok else "FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
