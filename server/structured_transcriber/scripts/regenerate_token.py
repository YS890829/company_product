#!/usr/bin/env python3
"""
Regenerate Google OAuth token with unified scopes
Phase 20: 統一スコープでの再認証（全機能をカバー）
"""
import os
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# 統一スコープ
SCOPES_STR = os.getenv('GOOGLE_ALL_SCOPES', 'https://www.googleapis.com/auth/drive,https://www.googleapis.com/auth/documents,https://www.googleapis.com/auth/calendar.readonly')
SCOPES = [s.strip() for s in SCOPES_STR.split(',')]
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.json'

def main():
    print("🔄 Google OAuth Token Regeneration (Unified Scopes)")
    print("📋 Required Scopes:")
    for scope in SCOPES:
        print(f"   - {scope}")

    if not Path(CREDENTIALS_FILE).exists():
        print(f"❌ Error: {CREDENTIALS_FILE} not found")
        print("Please download OAuth 2.0 credentials from Google Cloud Console")
        return

    if Path(TOKEN_FILE).exists():
        print(f"⚠️  Warning: {TOKEN_FILE} already exists")
        print("The existing token will be overwritten")
        response = input("Continue? (y/n): ")
        if response.lower() != 'y':
            print("Cancelled")
            return

    print("\n🌐 Opening browser for authentication...")
    print("Please sign in and grant permissions")

    flow = InstalledAppFlow.from_client_secrets_file(
        CREDENTIALS_FILE,
        SCOPES
    )

    creds = flow.run_local_server(port=0)

    # Save credentials
    with open(TOKEN_FILE, 'w') as token:
        token.write(creds.to_json())

    print(f"\n✅ Token saved: {TOKEN_FILE}")
    print(f"📋 Scopes granted: {creds.scopes}")
    print("\n🎉 Token regeneration complete!")

if __name__ == '__main__':
    main()
