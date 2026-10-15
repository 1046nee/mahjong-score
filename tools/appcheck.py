# -*- coding: utf-8 -*-
"""本番DBに触るテストを、App Check の強制後も通すための共通の仕組み（2026-10-15）。

App Check を強制すると、サイトの画面以外（Python の REST・手元の 127.0.0.1 のページ）からの読み書きは弾かれる。
Firebaseコンソール → App Check → アプリ →「デバッグトークンを管理」で作ったトークンを、
  ・環境変数 APPCHECK_DEBUG_TOKEN、または
  ・tools/.appcheck-debug-token（1行。.gitignore 済み。公開リポジトリに載せない）
に置くと、
  ・install(): urllib で本番DBへ送る要求に App Check のトークンを付ける（REST のテスト用）
  ・init_js(): ページの localStorage に入れる JS（ブラウザのテスト用。index.html が __appcheck_debug を読む）
トークンが無いときは何もしない（強制する前は、無くても通る）。
"""
import json
import os
import urllib.request

PROJECT = "mahjong-score-2e8aa"
APP_ID = "1:742827563606:web:91b4e849caa99eda7f39f7"
API_KEY = "AIzaSyDzZPhT7OzQDpaMXorp__yZ57v16VRY4W4"  # ウェブ用の公開キー（index.html と同じ）
TOKEN_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".appcheck-debug-token")
_cache = {}


def debug_token():
    t = os.environ.get("APPCHECK_DEBUG_TOKEN", "").strip()
    if not t and os.path.exists(TOKEN_FILE):
        t = open(TOKEN_FILE, encoding="utf-8").read().strip()
    return t


def app_check_token():
    """デバッグトークンを App Check のトークン（1時間有効）に交換する"""
    if "t" not in _cache:
        dt = debug_token()
        if not dt:
            _cache["t"] = None
        else:
            url = f"https://firebaseappcheck.googleapis.com/v1/projects/{PROJECT}/apps/{APP_ID}:exchangeDebugToken?key={API_KEY}"
            req = urllib.request.Request(url, data=json.dumps({"debugToken": dt}).encode(), method="POST", headers={"Content-Type": "application/json"})
            with _orig_urlopen(req, timeout=30) as r:
                _cache["t"] = json.loads(r.read())["token"]
    return _cache["t"]


_orig_urlopen = urllib.request.urlopen


def install():
    tok = app_check_token()
    if not tok:
        return

    def urlopen(req, *a, **kw):
        if isinstance(req, str):
            req = urllib.request.Request(req)
        if "firebasedatabase.app" in req.full_url:
            req.add_header("X-Firebase-AppCheck", tok)
        return _orig_urlopen(req, *a, **kw)

    urllib.request.urlopen = urlopen


def init_js():
    dt = debug_token()
    return f"try {{ localStorage.setItem('__appcheck_debug', {json.dumps(dt)}); }} catch (e) {{}}" if dt else ""
