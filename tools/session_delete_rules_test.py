# -*- coding: utf-8 -*-
"""「試合そのものは誰も消せない」ルール（sessions/$id の .write に newData.exists()）を本番で確かめる。

検証用の試合を1つ作り、REST API（ログインなし）で
  [1] 点数の追加（書き換え）はできる（確定前）
  [2] 試合をまるごと消す（DELETE）は拒否
  [3] 試合を null で上書きする（PUT null）も拒否
を見る。消せないことを確かめるテストなので、作った試合は本番に残る（中身は名前だけの空の試合）。
残った試合には、確定の期限（lockAt＝24時間後）を付けておくので、翌日以降は書き換えもできなくなる。

前提: database.rules.json をFirebaseコンソールに貼って「公開」してから実行する。
実行: python tools/session_delete_rules_test.py
"""
import sys
import time

from view_rules_test import http, rnd


def main():
    sid = rnd(10)
    now_ms = int(time.time() * 1000)
    game = {"id": sid, "name": "ルール確認用（削除できないことの確認）", "createdAt": "2026-09-29T00:00:00.000Z",
            "settings": {"playerNames": ["A", "B", "C", "D"], "numPlayers": 4}}
    st, _ = http("PUT", f"sessions/{sid}", game)
    if st != 200:
        print("検証用の試合を作れませんでした", st)
        return 1
    results = []
    st, _ = http("PUT", f"sessions/{sid}/rounds/0", {"points": [40000, 30000, 20000, 10000], "scores": [50, 10, -20, -40]})
    results.append(("[1] 確定前の試合は、点数を書き込める", st == 200, st))
    st, _ = http("DELETE", f"sessions/{sid}")
    results.append(("[2] 試合をまるごと消す（DELETE）は拒否される", st in (401, 403), st))
    st, _ = http("PUT", f"sessions/{sid}", None)
    results.append(("[3] 試合を空（null）で上書きするのも拒否される", st in (400, 401, 403), st))
    st, v = http("GET", f"sessions/{sid}/name")
    results.append(("[4] 試合は残っている", st == 200 and v == game["name"], st))
    # 残る試合には確定の期限を付ける（24時間後から誰も書き換えられない）
    http("PUT", f"sessions/{sid}/lockAt", now_ms + 24 * 3600 * 1000)
    ok = True
    for label, passed, code in results:
        print(("PASS  " if passed else "FAIL  ") + label + ("" if passed else f"（HTTP {code}）"))
        ok = ok and passed
    print(f"検証用の試合 {sid} は本番に残ります（消せないことの確認のため）")
    print("SESSION DELETE RULES: " + ("ALL PASS" if ok else "FAILED"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
