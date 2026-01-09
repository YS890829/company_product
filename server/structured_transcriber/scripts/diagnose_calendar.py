#!/usr/bin/env python3
"""
カレンダーAPI診断スクリプト
指定日のカレンダーイベントを取得し、詳細ログを出力します。
"""

import sys
import os
from datetime import datetime

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.calendar_integration import get_events_for_file_date, authenticate_calendar_service


def diagnose_calendar(date_str: str):
    """
    指定日のカレンダーイベントを診断

    Args:
        date_str: YYYYMMDD形式の日付
    """
    print("=" * 70)
    print("カレンダーAPI診断ツール")
    print("=" * 70)
    print(f"対象日: {date_str}")
    print()

    # Step 1: 認証確認
    print("[Step 1] カレンダーAPI認証確認...")
    service = authenticate_calendar_service()
    if not service:
        print("❌ 認証失敗")
        print("\n修正方法:")
        print("1. token.jsonを削除して再認証")
        print("2. credentials.jsonが正しく配置されているか確認")
        print("3. GOOGLE_ALL_SCOPESに calendar.readonly が含まれているか確認")
        return False
    print("✅ 認証成功")
    print()

    # Step 2: カレンダーリスト取得
    print("[Step 2] カレンダーリスト取得...")
    try:
        calendar_list = service.calendarList().list().execute()
        calendars = calendar_list.get('items', [])
        print(f"✅ {len(calendars)}個のカレンダーを検出")
        for cal in calendars:
            cal_id = cal.get('id')
            summary = cal.get('summary', '(名前なし)')
            primary = ' [PRIMARY]' if cal.get('primary') else ''
            print(f"  - {summary}{primary}")
            print(f"    ID: {cal_id}")
        print()
    except Exception as e:
        print(f"❌ カレンダーリスト取得エラー: {e}")
        return False

    # Step 3: 指定日のイベント取得
    print(f"[Step 3] {date_str}の予定取得...")
    try:
        events = get_events_for_file_date(date_str)

        if not events:
            print("⚠️  予定が見つかりません")
            print("\n考えられる理由:")
            print("1. その日に予定が登録されていない")
            print("2. primaryカレンダー以外に予定がある")
            print("3. 日付のタイムゾーン設定が正しくない")
            print("\n確認方法:")
            print(f"Googleカレンダー({date_str[:4]}/{date_str[4:6]}/{date_str[6:]})を開いて、")
            print("予定が実際に存在するか確認してください。")
            return False

        print(f"✅ {len(events)}件の予定を取得")
        print()

        # Step 4: 各イベントの詳細確認
        print("[Step 4] イベント詳細:")
        for i, event in enumerate(events, 1):
            print(f"\n--- イベント {i} ---")
            print(f"ID: {event.get('id')}")
            print(f"タイトル: {event.get('summary', '(タイトルなし)')}")

            start = event.get('start', {})
            start_time = start.get('dateTime', start.get('date', '不明'))
            print(f"開始時刻: {start_time}")

            end = event.get('end', {})
            end_time = end.get('dateTime', end.get('date', '不明'))
            print(f"終了時刻: {end_time}")

            description = event.get('description', '')
            if description:
                desc_preview = description[:100].replace('\n', ' ')
                if len(description) > 100:
                    desc_preview += '...'
                print(f"説明: {desc_preview}")

                # 参加者情報の有無をチェック
                participant_keywords = ['参加者', '出席者', 'メンバー', '同席', '出席', '参加']
                has_participants = any(kw in description for kw in participant_keywords)
                if has_participants:
                    print("✅ 参加者情報あり")
                else:
                    print("⚠️  参加者情報なし（キーワード未検出）")
            else:
                print("⚠️  説明なし")

            attendees = event.get('attendees', [])
            if attendees:
                print(f"参加者リスト: {len(attendees)}名")
                for attendee in attendees[:3]:
                    email = attendee.get('email', '不明')
                    print(f"  - {email}")
                if len(attendees) > 3:
                    print(f"  ... 他{len(attendees) - 3}名")
            else:
                print("参加者リスト: なし")

        print("\n" + "=" * 70)
        print("診断完了")
        print("=" * 70)
        return True

    except Exception as e:
        print(f"❌ イベント取得エラー: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    if len(sys.argv) < 2:
        print("使用方法: python scripts/diagnose_calendar.py <YYYYMMDD>")
        print("例: python scripts/diagnose_calendar.py 20251021")
        print()
        print("または、今日の日付で診断:")
        print("python scripts/diagnose_calendar.py today")
        sys.exit(1)

    date_arg = sys.argv[1]

    if date_arg.lower() == 'today':
        date_str = datetime.now().strftime('%Y%m%d')
    else:
        date_str = date_arg

    # 日付形式チェック
    try:
        datetime.strptime(date_str, '%Y%m%d')
    except ValueError:
        print(f"❌ 日付形式エラー: {date_str}")
        print("正しい形式: YYYYMMDD (例: 20251021)")
        sys.exit(1)

    success = diagnose_calendar(date_str)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
