#!/usr/bin/env python3
"""
Supabase 全データバックアップ（JSON形式）
4テーブル（companies, deals, meetings, emails）の全件データをJSONファイルに保存
"""
import os
import json
from datetime import datetime
from supabase import create_client

# 環境変数から接続情報を取得
SUPABASE_URL = os.getenv('SUPABASE_URL', 'http://127.0.0.1:54321')
SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0')

def get_supabase_client():
    """Supabaseクライアント取得"""
    return create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

def backup_all_tables():
    """全4テーブルのデータをバックアップ"""
    print("="*80)
    print("Supabase 全データバックアップ（JSON形式）")
    print("="*80)
    print()

    supabase = get_supabase_client()

    # 全テーブルのデータを取得
    print("📊 データ取得中...")

    companies = supabase.table('companies').select('*').execute()
    print(f"  ✅ companies: {len(companies.data)}件")

    deals = supabase.table('deals').select('*').execute()
    print(f"  ✅ deals: {len(deals.data)}件")

    meetings = supabase.table('meetings').select('*').execute()
    print(f"  ✅ meetings: {len(meetings.data)}件")

    emails = supabase.table('emails').select('*').execute()
    print(f"  ✅ emails: {len(emails.data)}件")

    # バックアップデータ構造
    backup_data = {
        'backup_info': {
            'created_at': datetime.now().isoformat(),
            'supabase_url': SUPABASE_URL,
            'total_companies': len(companies.data),
            'total_deals': len(deals.data),
            'total_meetings': len(meetings.data),
            'total_emails': len(emails.data)
        },
        'companies': companies.data,
        'deals': deals.data,
        'meetings': meetings.data,
        'emails': emails.data
    }

    # JSONファイルに保存
    script_dir = os.path.dirname(__file__)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_path = os.path.join(script_dir, f'supabase_backup_full_{timestamp}.json')

    print()
    print("💾 JSONファイル保存中...")

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(backup_data, f, ensure_ascii=False, indent=2, default=str)

    # ファイルサイズ取得
    file_size = os.path.getsize(output_path)
    file_size_mb = file_size / (1024 * 1024)

    print()
    print("="*80)
    print("✅ バックアップ完了")
    print("="*80)
    print()
    print(f"📁 出力ファイル: {output_path}")
    print(f"📊 ファイルサイズ: {file_size_mb:.2f} MB ({file_size:,} bytes)")
    print()
    print("【バックアップ内容】")
    print(f"  • companies: {len(companies.data)}件")
    print(f"  • deals: {len(deals.data)}件")
    print(f"  • meetings: {len(meetings.data)}件（transcriptを含む）")
    print(f"  • emails: {len(emails.data)}件")
    print()
    print("【リストア方法】")
    print("  1. Pythonスクリプトでリストア:")
    print("     supabase.table('companies').insert(backup_data['companies']).execute()")
    print()
    print("  2. または、SQLに変換してリストア:")
    print("     generate_insert_sql.py を使用")
    print()

if __name__ == '__main__':
    backup_all_tables()
