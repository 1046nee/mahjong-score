# -*- coding: utf-8 -*-
"""仲間ページのセキュリティルール（database.rules.json）を、本番のRealtime Databaseに対して確かめる。

account_test.py はスタブ（ルールなし）なので、「本人の結びつけは他人が変えられない」などの制限が
本当にサーバーで効いているかはここでしか分からない。
Firebase Authentication の「匿名」ログインで使い捨てのアカウントを3つ作り（作成者A・メンバーB・部外者C）、
REST API で書き込みを試して、許可／拒否が期待どおりかを見る。最後に作ったデータとアカウントを全部消す。

前提: Firebaseコンソール → Authentication → ログイン方法 で「匿名」を一時的に有効にしておく
      （このテストのためだけ。アプリは匿名ログインを使わないので、終わったら無効に戻してよい）
      ルールをコンソールに貼って「公開」してから実行すること。
実行: python tools/circle_rules_test.py
"""
import email.utils
import json
import random
import time
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

DB = "https://mahjong-score-2e8aa-default-rtdb.asia-southeast1.firebasedatabase.app"
ROOT = Path(__file__).resolve().parent.parent
API_KEY = re.search(r'apiKey: "([^"]+)"', (ROOT / "index.html").read_text(encoding="utf-8")).group(1)
ID_CHARS = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz23456789"
CODE_CHARS = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def rnd(n, chars):
    return "".join(random.choice(chars) for _ in range(n))


def http(method, url, body=None):
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, json.loads(r.read().decode("utf-8") or "null")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode("utf-8") or "null")
        except Exception:
            return e.code, None


def anon_user():
    st, res = http("POST", f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={API_KEY}", {"returnSecureToken": True})
    if st != 200:
        msg = (res or {}).get("error", {}).get("message", st)
        print(f"匿名ログインを作れませんでした: {msg}")
        print("→ Firebaseコンソール → Authentication → ログイン方法 で「匿名」を一時的に有効にしてから、もう一度実行してください。")
        sys.exit(2)
    return {"uid": res["localId"], "token": res["idToken"]}


def delete_user(u):
    http("POST", f"https://identitytoolkit.googleapis.com/v1/accounts:delete?key={API_KEY}", {"idToken": u["token"]})


def server_now():
    """サーバーの時刻（ミリ秒）。HTTPの Date ヘッダーから取る（ルールの幅は時間単位なので秒単位で十分）"""
    req = urllib.request.Request(f"{DB}/.json?shallow=true&print=silent", method="GET")
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            d = r.headers.get("Date")
    except urllib.error.HTTPError as e:
        d = e.headers.get("Date")
    return int(email.utils.parsedate_to_datetime(d).timestamp() * 1000) if d else int(time.time() * 1000)


def op(user, method, path, body=None):
    auth = f"?auth={user['token']}" if user else ""
    st, _ = http(method, f"{DB}/{path}.json{auth}", body)
    return st == 200


def main():
    A, B, C = anon_user(), anon_user(), anon_user()
    cid = rnd(10, ID_CHARS)
    code = rnd(8, CODE_CHARS)
    sid = rnd(10, ID_CHARS)
    m1, m2 = rnd(8, ID_CHARS), rnd(8, ID_CHARS)
    now = "2026-09-25T12:00:00.000Z"
    results = []

    def check(label, expect, got):
        results.append((label, expect, got))

    try:
        check("A: 仲間ページを作れる（作成者=自分）", True, op(A, "PUT", f"circles/{cid}", {"id": cid, "name": "ルールテスト", "createdAt": now, "owner": A["uid"]}))
        check("B: 他人の仲間ページを作成者なしで上書きできない", False, op(B, "PUT", f"circles/{cid}", {"id": cid, "name": "乗っ取り", "owner": B["uid"]}))
        check("A: 作成者としてメンバー登録できる", True, op(A, "PUT", f"circleMembers/{cid}/{A['uid']}", {"role": "owner", "name": "A", "joinedAt": now}))
        check("B: 作成者を名乗ってメンバー登録できない", False, op(B, "PUT", f"circleMembers/{cid}/{B['uid']}", {"role": "owner", "name": "B", "joinedAt": now}))
        check("A: 参加コードを発行できる", True, op(A, "PUT", f"circleInvites/{code}", cid) and op(A, "PUT", f"circleSecrets/{cid}", {"code": code}))
        check("B: 参加コードを勝手に作れない", False, op(B, "PUT", f"circleInvites/{rnd(8, CODE_CHARS)}", cid))
        check("B: 間違った参加コードでは参加できない", False, op(B, "PUT", f"circleMembers/{cid}/{B['uid']}", {"role": "editor", "name": "B", "joinedAt": now, "code": "ZZZZZZZZ"}))
        check("C: 正しいコードでも管理者として参加はできない", False, op(C, "PUT", f"circleMembers/{cid}/{C['uid']}", {"role": "admin", "name": "C", "joinedAt": now, "code": code}))
        check("B: 正しい参加コードで編集メンバーとして参加できる", True, op(B, "PUT", f"circleMembers/{cid}/{B['uid']}", {"role": "editor", "name": "B", "joinedAt": now, "code": code}))
        check("C（部外者）: 仲間ページの名前を変えられない", False, op(C, "PUT", f"circles/{cid}/name", "荒らし"))
        check("B: 仲間ページの名前は変えられる", True, op(B, "PUT", f"circles/{cid}/name", "ルールテスト2"))
        check("A: 名簿の自分を本人として登録できる", True, op(A, "PUT", f"circles/{cid}/roster/{m1}", {"name": "えー", "at": now, "uid": A["uid"]}))
        check("B: 本人登録がない人を名簿に足せる", True, op(B, "PUT", f"circles/{cid}/roster/{m2}", {"name": "びー", "at": now}))
        check("B: Aが本人登録した人の名前は変えられない", False, op(B, "PUT", f"circles/{cid}/roster/{m1}/name", "書き換え"))
        check("B: 他人のアカウントで本人登録はできない", False, op(B, "PUT", f"circles/{cid}/roster/{m2}/uid", A["uid"]))
        check("A: 試合を追加できる（自分の席は本人の結びつけ）", True, op(A, "PUT", f"circles/{cid}/games/{sid}", {
            "at": now, "name": "テスト試合", "addedBy": A["uid"], "addedByName": "えー", "addedAt": now,
            "seats": {"0": {"mid": m1, "by": A["uid"], "byName": "えー", "at": now, "self": True},
                      "1": {"mid": m2, "by": A["uid"], "byName": "えー", "at": now, "self": False}}}))
        check("B: Aが本人として結びつけた席は変えられない", False, op(B, "PUT", f"circles/{cid}/games/{sid}/seats/0", {"mid": m2, "by": B["uid"], "at": now, "self": False}))
        check("B: 本人でない席は変えられる", True, op(B, "PUT", f"circles/{cid}/games/{sid}/seats/1", {"mid": m2, "by": B["uid"], "byName": "びー", "at": now, "self": False}))
        check("B: 自分が本人登録していない人の席を「本人」にはできない", False, op(B, "PUT", f"circles/{cid}/games/{sid}/seats/1", {"mid": m2, "by": B["uid"], "at": now, "self": True}))
        check("B: 結びつけた人を他人の名前で記録できない", False, op(B, "PUT", f"circles/{cid}/games/{sid}/seats/1", {"mid": m2, "by": A["uid"], "at": now, "self": False}))
        check("B: 他人が追加した試合を外せない（管理者でない）", False, op(B, "DELETE", f"circles/{cid}/games/{sid}"))
        T = server_now()
        sid2, sid3 = rnd(10, ID_CHARS), rnd(10, ID_CHARS)
        check("A: 期限（24時間後）を付けて試合を追加できる", True, op(A, "PUT", f"circles/{cid}/games/{sid2}", {
            "at": now, "name": "期限つき", "addedBy": A["uid"], "addedByName": "えー", "addedAt": now, "lockAt": T + 24 * 3600 * 1000}))
        check("A: 期限を遠い先（48時間後）にして追加するのは拒否", False, op(A, "PUT", f"circles/{cid}/games/{sid3}", {
            "at": now, "name": "抜け道", "addedBy": A["uid"], "addedByName": "えー", "addedAt": now, "lockAt": T + 48 * 3600 * 1000}))
        check("B: 他人が追加した試合は、期限内でも外せない（管理者でない）", False, op(B, "DELETE", f"circles/{cid}/games/{sid2}"))
        check("A: 自分が追加した試合は、期限（24時間）までは外せる", True, op(A, "DELETE", f"circles/{cid}/games/{sid2}"))
        # 確定した試合（期限の無い古い追加）: 追加した本人（編集メンバー）は外せない。作成者・管理者は外せる（2026-10-09）
        sid4 = rnd(10, ID_CHARS)
        check("B: 期限なしで試合を追加できる（すぐ確定）", True, op(B, "PUT", f"circles/{cid}/games/{sid4}", {
            "at": now, "name": "確定済み", "addedBy": B["uid"], "addedByName": "びー", "addedAt": now}))
        check("B（編集メンバー）: 確定した試合は、追加した本人でも外せない", False, op(B, "DELETE", f"circles/{cid}/games/{sid4}"))
        check("A（作成者）: 確定した試合も外せる", True, op(A, "DELETE", f"circles/{cid}/games/{sid4}"))
        check("B: Aが追加した試合を追加し直して上書きできない（同じ試合は二重に入らない）", False, op(B, "PUT", f"circles/{cid}/games/{sid}", {
            "at": now, "name": "二重", "addedBy": B["uid"], "addedByName": "びー", "addedAt": now}))
        check("B: 自分の役割を管理者に上げられない", False, op(B, "PUT", f"circleMembers/{cid}/{B['uid']}/role", "admin"))
        check("A（作成者）: Bを管理者にできる", True, op(A, "PUT", f"circleMembers/{cid}/{B['uid']}/role", "admin"))
        # 管理者はメンバーの管理（作成者以外の役割を変える・外す）と参加コードの作り直しができる。編集メンバーはできない（2026-10-08）
        check("C: 正しい参加コードで編集メンバーとして参加できる", True, op(C, "PUT", f"circleMembers/{cid}/{C['uid']}", {"role": "editor", "name": "C", "joinedAt": now, "code": code, "gname": "Cのアカウント"}))
        check("C（編集メンバー）: 自分のGoogleアカウント名を書ける", True, op(C, "PUT", f"circleMembers/{cid}/{C['uid']}/gname", "Cのアカウント2"))
        check("C（編集メンバー）: 他人（管理者B）の役割を変えられない", False, op(C, "PUT", f"circleMembers/{cid}/{B['uid']}/role", "editor"))
        check("C（編集メンバー）: 他人（管理者B）を外せない", False, op(C, "DELETE", f"circleMembers/{cid}/{B['uid']}"))
        check("C（編集メンバー）: 参加コードを作り直せない", False, op(C, "PUT", f"circleSecrets/{cid}", {"code": rnd(8, CODE_CHARS)}))
        check("B（管理者）: Cを管理者にできる", True, op(B, "PUT", f"circleMembers/{cid}/{C['uid']}/role", "admin"))
        check("B（管理者）: Cを編集メンバーに戻せる", True, op(B, "PUT", f"circleMembers/{cid}/{C['uid']}/role", "editor"))
        check("B（管理者）: だれかを作成者にはできない", False, op(B, "PUT", f"circleMembers/{cid}/{C['uid']}/role", "owner"))
        check("B（管理者）: 他人のGoogleアカウント名は書き換えられない", False, op(B, "PUT", f"circleMembers/{cid}/{C['uid']}/gname", "なりすまし"))
        check("B（管理者）: 作成者Aは外せない", False, op(B, "DELETE", f"circleMembers/{cid}/{A['uid']}"))
        code2 = rnd(8, CODE_CHARS)
        check("B（管理者）: 参加コードを作り直せる（新しいコード・控え・古いコードを消す）", True,
              op(B, "PUT", f"circleInvites/{code2}", cid) and op(B, "PUT", f"circleSecrets/{cid}", {"code": code2}) and op(B, "DELETE", f"circleInvites/{code}"))
        code = code2
        check("B（管理者）: Cを外せる", True, op(B, "DELETE", f"circleMembers/{cid}/{C['uid']}"))
        check("B（管理者）: 本人が結びつけた席も変えられる", True, op(B, "PUT", f"circles/{cid}/games/{sid}/seats/0", {"mid": m1, "by": B["uid"], "byName": "びー", "at": now, "self": False}))
        check("B（管理者）: 本人登録された人の名前も変えられる", True, op(B, "PUT", f"circles/{cid}/roster/{m1}/name", "エー"))
        check("A（作成者）: 名簿の人のアイコンの色を決められる", True, op(A, "PUT", f"circles/{cid}/roster/{m2}/color", "#1565C0"))
        check("B（管理者）: アイコンの色は変えられない（作成者だけ）", False, op(B, "PUT", f"circles/{cid}/roster/{m2}/color", "#C62828"))
        check("A（作成者）: 色でない値は入れられない", False, op(A, "PUT", f"circles/{cid}/roster/{m2}/color", "red"))
        check("B（管理者）: 他人の役割は変えられない（作成者だけ）", False, op(B, "PUT", f"circleMembers/{cid}/{A['uid']}/role", "editor"))
        check("B: 自分の名前で履歴を残せる", True, op(B, "POST", f"circles/{cid}/log", {"at": now, "by": B["uid"], "byName": "びー", "kind": "bind", "text": "テスト"}))
        check("B: 他人の名前で履歴を残せない", False, op(B, "POST", f"circles/{cid}/log", {"at": now, "by": A["uid"], "byName": "えー", "kind": "bind", "text": "なりすまし"}))
        check("C（部外者）: 履歴を書けない", False, op(C, "POST", f"circles/{cid}/log", {"at": now, "by": C["uid"], "kind": "bind", "text": "x"}))
        check("ログインなし: 仲間ページ（結果）は読める", True, op(None, "GET", f"circles/{cid}"))
        check("ログインなし: 参加コードは読めない", False, op(None, "GET", f"circleSecrets/{cid}"))
        check("ログインなし: メンバー一覧は読めない", False, op(None, "GET", f"circleMembers/{cid}"))
        check("C（部外者）: 参加コードは読めない", False, op(C, "GET", f"circleSecrets/{cid}"))
        check("B（メンバー）: 参加コードを読める（招待に使う）", True, op(B, "GET", f"circleSecrets/{cid}"))
        check("ログインなし: 招待リンクのコードから仲間ページを引ける", True, op(None, "GET", f"circleInvites/{code}"))
        check("ログインなし: 招待の一覧は読めない", False, op(None, "GET", "circleInvites"))
        check("A: 自分の仲間ページ一覧に追加できる", True, op(A, "PUT", f"users/{A['uid']}/circles/{cid}", {"at": now, "name": "ルールテスト"}))
        check("B: 他人の仲間ページ一覧は書けない", False, op(B, "PUT", f"users/{A['uid']}/circles/{cid}", {"at": now, "name": "x"}))
        check("B: 仲間ページから抜けられる", True, op(B, "DELETE", f"circleMembers/{cid}/{B['uid']}"))
    finally:
        # 後片付け（作成者Aが、メンバー→参加コード→仲間ページの順に消す）
        for path in [f"circleMembers/{cid}/{B['uid']}", f"circleMembers/{cid}/{C['uid']}", f"circleMembers/{cid}/{A['uid']}",
                     f"circleInvites/{code}", f"circleSecrets/{cid}", f"circles/{cid}", f"users/{A['uid']}"]:
            op(A, "DELETE", path)
        left = http("GET", f"{DB}/circles/{cid}.json")[1]
        for u in (A, B, C):
            delete_user(u)
        print(f"後片付け: テスト用の仲間ページ {cid} → {'削除済み' if left is None else '残っている！'}／匿名アカウント3つを削除")

    print()
    ok = True
    for label, expect, got in results:
        passed = expect == got
        ok &= passed
        print(f"{'PASS' if passed else 'FAIL'}  {label}（期待 {'許可' if expect else '拒否'} / 実際 {'許可' if got else '拒否'}）")
    print()
    print("CIRCLE RULES TEST:", "ALL PASS" if ok else "FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
