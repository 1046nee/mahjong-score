# -*- coding: utf-8 -*-
"""試合の「記録の確定」（sessions/{id} の lockAt・endedAt）のセキュリティルールを、本番のRealtime Databaseで確かめる。

アプリの画面で入力の入口を隠すだけでは、試合IDを知っている人がREST APIなどで直接書き換えられる。
「確定したあとは誰も書き換えられない」が本当にサーバーで効いているかはここでしか分からない。
ログインは使わない（試合の入力もログインなしで動く）。検証用の試合を作り、REST API で読み書きを試して
許可／拒否が期待どおりかを見る。最後に作ったデータを消す（締め切り前なので消せる）。

「締め切りを過ぎたら書けない」は、締め切りを11時間より近くにできない（いたずらで即確定させないための決まり）ので
その場では試せない。--canary で確認用の試合を1つ置き、12時間以上たってから --check-canary で確かめる
（確定した試合は消せないので、確認用の試合は「ロック確認用」という名前のままDBに残る。中身はダミー）。

前提: database.rules.json をFirebaseコンソール（Realtime Database → ルール）に貼って「公開」してから実行する。
実行: python tools/lock_rules_test.py            （その場で試せる14項目）
      python tools/lock_rules_test.py --canary   （確認用の試合を置く。IDは %LOCALAPPDATA%\\majasco\\lock_canary.json に控える）
      python tools/lock_rules_test.py --check-canary
"""
import email.utils
import json
import os
import random
import sys
import time
import urllib.error
import urllib.request

DB = "https://mahjong-score-2e8aa-default-rtdb.asia-southeast1.firebasedatabase.app"
ID_CHARS = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz23456789"
H = 3600 * 1000
CANARY_FILE = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "majasco", "lock_canary.json")


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


def server_now():
    """サーバーの時刻（ミリ秒）。HTTPの Date ヘッダーから取る（秒単位で十分。ルールの幅は時間単位）"""
    req = urllib.request.Request(f"{DB}/.json?shallow=true&print=silent", method="GET")
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            d = r.headers.get("Date")
    except urllib.error.HTTPError as e:
        d = e.headers.get("Date")
    return int(email.utils.parsedate_to_datetime(d).timestamp() * 1000) if d else int(time.time() * 1000)


def game(sid, name="ルール確認用（自動で消えます）", **extra):
    g = {"id": sid, "name": name, "createdAt": "2026-09-26T00:00:00.000Z",
         "settings": {"playerNames": ["A", "B", "C", "D"], "numPlayers": 4},
         "rounds": [{"points": [40000, 30000, 20000, 10000], "scores": [50, 10, -20, -40]}]}
    g.update(extra)
    return g


def report(results, title):
    ok = True
    for label, passed, st in results:
        ok &= passed
        print(("PASS  " if passed else "FAIL  ") + label + ("" if passed else f"（実際 {st}）"))
    print(f"{title}:", "ALL PASS" if ok else "FAILED")
    return 0 if ok else 1


def main():
    sid = rnd(10)
    results = []

    def check(label, expect_ok, st):
        results.append((label, (200 <= st < 300) == expect_ok, st))

    T = server_now()
    try:
        check("[1] 締め切りのない試合（今までの試合と同じ）を作れる", True, http("PUT", f"sessions/{sid}", game(sid))[0])
        check("[2] 締め切り（lockAt）を「今から24時間後」にできる（最後の入力から24時間で自動確定）", True,
              http("PUT", f"sessions/{sid}", game(sid, lockAt=T + 24 * H))[0])
        check("[3] 締め切りを遠い先（30時間後）にするのは拒否（いつまでも確定しない抜け道）", False,
              http("PUT", f"sessions/{sid}", game(sid, lockAt=T + 30 * H))[0])
        check("[4] 締め切りを近すぎる時刻（2時間後）にするのは拒否（いたずらでいきなり確定させる）", False,
              http("PUT", f"sessions/{sid}", game(sid, lockAt=T + 2 * H))[0])
        check("[5] 締め切りを数値以外にするのは拒否", False,
              http("PUT", f"sessions/{sid}", game(sid, lockAt="2099-01-01"))[0])
        check("[6] 一度付いた締め切りを消すのは拒否", False, http("PUT", f"sessions/{sid}", game(sid))[0])
        st, cur = http("GET", f"sessions/{sid}/lockAt")
        lock = cur if isinstance(cur, (int, float)) else T + 24 * H
        check("[7] 締め切りをそのままにした更新（点数の修正など）は通る", True,
              http("PUT", f"sessions/{sid}", game(sid, name="修正", lockAt=lock))[0])
        E = server_now()
        check("[8] 対局の終了（endedAt＝今・締め切り＝12時間後）ができる", True,
              http("PUT", f"sessions/{sid}", game(sid, endedAt=E, lockAt=E + 12 * H))[0])
        check("[9] 終了後の猶予のうちは、締め切りそのままで修正できる", True,
              http("PUT", f"sessions/{sid}", game(sid, name="猶予中の修正", endedAt=E, lockAt=E + 12 * H))[0])
        check("[10] 終了したまま締め切りを延ばす（24時間後）のは拒否", False,
              http("PUT", f"sessions/{sid}", game(sid, endedAt=E, lockAt=server_now() + 24 * H))[0])
        check("[11] 終了時刻を過去（2時間前）に書き換えるのは拒否", False,
              http("PUT", f"sessions/{sid}", game(sid, endedAt=E - 2 * H, lockAt=E + 12 * H))[0])
        R = server_now()
        check("[12] 猶予のうちは再開（終了時刻を消して締め切りを24時間後に）できる", True,
              http("PUT", f"sessions/{sid}", game(sid, lockAt=R + 24 * H))[0])
        st, body = http("GET", f"sessions/{sid}")
        results.append(("[13] 読むのは誰でもでき、再開した状態が見える", st == 200 and (body or {}).get("endedAt") is None
                        and (body or {}).get("lockAt") == R + 24 * H, (st, (body or {}).get("lockAt"))))
    finally:
        a = http("DELETE", f"sessions/{sid}")[0]
        results.append(("[14] 締め切り前なら試合ごと消せる（検証用のデータが残らない）",
                        a == 200 and http("GET", f"sessions/{sid}")[1] is None, a))
    return report(results, "LOCK RULES TEST")


def canary():
    """締め切り（11時間10分後）を付けた確認用の試合を置く。確定したあとは消せない（中身はダミー）"""
    sid = rnd(10)
    T = server_now()
    lock = T + 11 * H + 10 * 60 * 1000
    st = http("PUT", f"sessions/{sid}", game(sid, name="ロック確認用（確定後は消せません・中身はダミー）", lockAt=lock))[0]
    if not 200 <= st < 300:
        print("確認用の試合を置けませんでした", st)
        return 1
    os.makedirs(os.path.dirname(CANARY_FILE), exist_ok=True)
    with open(CANARY_FILE, "w", encoding="utf-8") as f:
        json.dump({"sid": sid, "lockAt": lock}, f)
    print(f"確認用の試合 {sid} を置きました。締め切り: {time.strftime('%Y-%m-%d %H:%M', time.localtime(lock / 1000))}")
    print("それ以降に python tools/lock_rules_test.py --check-canary を実行してください")
    return 0


def check_canary():
    try:
        with open(CANARY_FILE, encoding="utf-8") as f:
            c = json.load(f)
    except FileNotFoundError:
        print("確認用の試合がありません。先に --canary を実行してください")
        return 1
    sid, lock = c["sid"], c["lockAt"]
    T = server_now()
    if T < lock:
        print(f"まだ締め切り前です（あと {(lock - T) / H:.1f} 時間）。{time.strftime('%Y-%m-%d %H:%M', time.localtime(lock / 1000))} 以降に実行してください")
        return 1
    results = []

    def check(label, expect_ok, st):
        results.append((label, (200 <= st < 300) == expect_ok, st))

    check("[C1] 締め切りを過ぎた試合の書き換えは拒否", False,
          http("PUT", f"sessions/{sid}", game(sid, name="改ざん", lockAt=lock))[0])
    check("[C2] 締め切りを過ぎた試合の一部（rounds）だけの書き換えも拒否", False,
          http("PUT", f"sessions/{sid}/rounds", [{"points": [1, 2, 3, 4], "scores": [9, 9, 9, 9]}])[0])
    check("[C3] 締め切りを延ばして開け直すのも拒否", False,
          http("PUT", f"sessions/{sid}", game(sid, lockAt=T + 24 * H))[0])
    check("[C4] 確定した試合ごと消すのも拒否", False, http("DELETE", f"sessions/{sid}")[0])
    st, body = http("GET", f"sessions/{sid}")
    results.append(("[C5] 確定した試合も読むのはできる（中身は変わっていない）",
                    st == 200 and (body or {}).get("name", "").startswith("ロック確認用"), st))
    return report(results, "LOCK CANARY TEST")


if __name__ == "__main__":
    if "--canary" in sys.argv:
        sys.exit(canary())
    if "--check-canary" in sys.argv:
        sys.exit(check_canary())
    sys.exit(main())
