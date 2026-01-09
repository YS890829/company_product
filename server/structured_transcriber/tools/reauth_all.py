#!/usr/bin/env python3
"""
Google API Re-authentication with unified scopes
Phase 20: 統一スコープでの再認証（全機能をカバー）
"""
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import os
from dotenv import load_dotenv

load_dotenv()

# 統一スコープで再認証（全機能をカバー）
SCOPES_STR = os.getenv('GOOGLE_ALL_SCOPES', 'https://www.googleapis.com/auth/drive,https://www.googleapis.com/auth/documents,https://www.googleapis.com/auth/calendar.readonly')
SCOPES = [s.strip() for s in SCOPES_STR.split(',')]

def main():
    print("=" * 60)
    print("Google OAuth 統一スコープ再認証")
    print("=" * 60)
    print("スコープ:")
    for scope in SCOPES:
        print(f"  - {scope}")
    print("\n権限: Drive, Docs, Calendar (全機能)")
    print()

    # 既存のtoken.jsonを削除
    if os.path.exists('token.json'):
        os.remove('token.json')
        print("✅ 古いtoken.jsonを削除しました")

    # 新しい認証フローを開始
    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)

    print()
    print("ブラウザが自動的に開きます...")
    print("Google アカウントで認証してください。")
    print()

    # ローカルサーバーで認証（自動的にブラウザが開く）
    creds = flow.run_local_server(port=8080)

    # token.jsonに保存
    with open('token.json', 'w') as token:
        token.write(creds.to_json())

    print()
    print("=" * 60)
    print("✅ 再認証完了！")
    print("=" * 60)
    print("token.jsonが更新されました。")
    print("すべてのGoogle API（Drive, Docs, Calendar）の権限が付与されました。")
    print("\n付与されたスコープ:")
    for scope in SCOPES:
        print(f"  ✓ {scope}")
    print()

if __name__ == '__main__':
    main()
