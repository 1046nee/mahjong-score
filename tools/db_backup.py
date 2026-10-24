# -*- coding: utf-8 -*-
"""本番DB（Realtime Database）の「消えると困る一覧」を書き出す。GitHub Actions（.github/workflows/db-backup.yml）が毎日動かす。

書き出すもの: mylists（アカウントの試合一覧）・users（アカウントと一覧のつながり）・circles・circleMembers（仲間ページ）。
sessions（試合の中身）は誰にも消せないルールなので入れない（大きいうえ、消える心配がない）。

使い方（Actions 以外で動かすことは想定していない）:
  FIREBASE_SA_JSON='{...サービスアカウントのJSON...}' python tools/db_backup.py out.json
サービスアカウントに「Firebase Realtime Database 閲覧者」（roles/firebasedatabase.viewer）の権限が要る（docs/site-spec.md「バックアップ」）。
中身（試合ID・アカウントID）も件数もログに出さない（公開リポジトリのActionsのログは誰でも見られる）。
"""
import json
import os
import sys
import urllib.request

from google.oauth2 import service_account
from google.auth.transport.requests import Request

DB_URL = 'https://mahjong-score-2e8aa-default-rtdb.asia-southeast1.firebasedatabase.app'
NODES = ['mylists', 'users', 'circles', 'circleMembers']
SCOPES = ['https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/firebase.database']


def main():
    out = sys.argv[1]
    info = json.loads(os.environ['FIREBASE_SA_JSON'])
    cred = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
    cred.refresh(Request())
    data = {}
    for node in NODES:
        req = urllib.request.Request(f'{DB_URL}/{node}.json', headers={'Authorization': 'Bearer ' + cred.token})
        with urllib.request.urlopen(req, timeout=300) as r:
            data[node] = json.loads(r.read().decode('utf-8'))
    n_lists = len(data['mylists'] or {})
    n_groups = sum(len((v or {}).get('groups') or {}) for v in (data['mylists'] or {}).values())
    # 一覧が空・極端に少ないのは、権限やURLの間違いの可能性が高い（空のバックアップで上書きしたつもりにならないよう失敗にする）
    if n_lists == 0 or n_groups == 0:
        print('mylists が空でした。権限（Realtime Database 閲覧者）とURLを確かめてください', file=sys.stderr)
        sys.exit(1)
    with open(out, 'w', encoding='utf-8') as f:
        json.dump({'exportedFrom': DB_URL, 'nodes': data}, f, ensure_ascii=False, separators=(',', ':'))
    print('書き出しました')


if __name__ == '__main__':
    main()
