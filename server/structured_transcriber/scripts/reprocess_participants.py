#!/usr/bin/env python3
"""
既存会議データの参加者情報再処理スクリプト

目的:
- 既存の会議（enhanced JSON）から参加者情報を再抽出
- データベースに参加者を登録し、会議との紐付けを更新

使用方法:
    python scripts/reprocess_participants.py [--dry-run] [--force]

オプション:
    --dry-run: 実際のDB更新なしでプレビュー
    --force: 既存の参加者情報も上書き
"""

import sys
import os
import json
import argparse
from datetime import datetime

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.participants.participants_db import ParticipantsDB


def load_enhanced_json(file_path: str):
    """Enhanced JSONファイルを読み込み"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except json.JSONDecodeError as e:
        print(f"  ⚠️  JSON読み込みエラー: {e}")
        return None


def extract_participants_from_enhanced_json(enhanced_data: dict) -> list:
    """
    Enhanced JSONから参加者を抽出

    優先順位:
    1. participants.canonical_names（カレンダーから抽出済み）
    2. content.entities.people（会話内容から抽出）
    """
    participants = []

    # 優先順位1: カレンダーから抽出済み
    calendar_names = enhanced_data.get('participants', {}).get('canonical_names', [])
    if calendar_names:
        return calendar_names

    # 優先順位2: エンティティ（人物）
    entities_people = enhanced_data.get('content', {}).get('entities', {}).get('people', [])
    if entities_people:
        return entities_people

    return []


def reprocess_meetings(dry_run=False, force=False):
    """
    全会議の参加者情報を再処理

    Args:
        dry_run: True の場合、実際のDB更新は行わない
        force: True の場合、既存参加者も上書き
    """
    print("=" * 70)
    print("既存会議データの参加者情報再処理")
    print("=" * 70)
    print(f"モード: {'DRY-RUN（プレビューのみ）' if dry_run else '本実行'}")
    print(f"上書き: {'有効' if force else '無効（新規のみ）'}")
    print()

    db = ParticipantsDB()

    # DBから全会議を取得
    import sqlite3
    conn = sqlite3.connect(db.db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT meeting_id, structured_file_path, meeting_title, meeting_date
        FROM meetings
        ORDER BY created_at ASC
    """)

    meetings = cursor.fetchall()
    conn.close()

    if not meetings:
        print("⚠️  会議データが見つかりません")
        return

    print(f"✅ {len(meetings)}件の会議を取得しました\n")

    # 統計情報
    stats = {
        'total': len(meetings),
        'enhanced_json_found': 0,
        'enhanced_json_not_found': 0,
        'participants_extracted': 0,
        'participants_registered': 0,
        'meetings_updated': 0,
        'skipped': 0
    }

    # 各会議を処理
    for i, (meeting_id, structured_path, meeting_title, meeting_date) in enumerate(meetings, 1):
        print(f"[{i}/{len(meetings)}] {os.path.basename(structured_path)}")
        print(f"  会議ID: {meeting_id}")
        print(f"  タイトル: {meeting_title}")
        print(f"  日付: {meeting_date}")

        # Enhanced JSONのパスを生成
        enhanced_path = structured_path.replace('_structured.json', '_structured_enhanced.json')

        if not os.path.exists(enhanced_path):
            print(f"  ⚠️  Enhanced JSONが見つかりません: {enhanced_path}")
            stats['enhanced_json_not_found'] += 1
            stats['skipped'] += 1
            print()
            continue

        stats['enhanced_json_found'] += 1

        # Enhanced JSON読み込み
        enhanced_data = load_enhanced_json(enhanced_path)
        if not enhanced_data:
            print(f"  ⚠️  Enhanced JSON読み込み失敗")
            stats['skipped'] += 1
            print()
            continue

        # 参加者抽出
        participant_names = extract_participants_from_enhanced_json(enhanced_data)

        if not participant_names:
            print(f"  ℹ️  参加者情報なし")
            stats['skipped'] += 1
            print()
            continue

        print(f"  ✓ {len(participant_names)}名の参加者を抽出:")
        for name in participant_names:
            print(f"    - {name}")

        stats['participants_extracted'] += len(participant_names)

        if dry_run:
            print(f"  [DRY-RUN] DB更新をスキップ")
            stats['meetings_updated'] += 1
            print()
            continue

        # 参加者をDBに登録
        participant_ids = []
        for name in participant_names:
            try:
                notes = f"再処理により登録 - {datetime.now().strftime('%Y-%m-%d')}"
                participant_id = db.upsert_participant(
                    canonical_name=name,
                    display_names=[name],
                    organization=None,
                    role=None,
                    notes=notes
                )
                participant_ids.append(participant_id)
                stats['participants_registered'] += 1
                print(f"    ✓ {name}: DB登録完了")
            except Exception as e:
                print(f"    ⚠️  {name}: DB登録エラー - {e}")

        # 会議と参加者の紐付けを更新
        if participant_ids:
            try:
                # 既存の紐付けを削除（再処理）
                conn = sqlite3.connect(db.db_path)
                cursor = conn.cursor()

                cursor.execute("DELETE FROM participant_meetings WHERE meeting_id = ?", (meeting_id,))

                # 新しい紐付けを作成
                for participant_id in participant_ids:
                    cursor.execute("""
                        INSERT INTO participant_meetings (participant_id, meeting_id, attended_at)
                        VALUES (?, ?, ?)
                    """, (participant_id, meeting_id, datetime.now().isoformat()))

                    # 参加者の会議カウントを更新
                    cursor.execute("""
                        UPDATE participants
                        SET meeting_count = (
                            SELECT COUNT(*) FROM participant_meetings
                            WHERE participant_id = ?
                        )
                        WHERE participant_id = ?
                    """, (participant_id, participant_id))

                conn.commit()
                conn.close()

                stats['meetings_updated'] += 1
                print(f"  ✓ 会議と参加者の紐付け更新完了")

            except Exception as e:
                print(f"  ⚠️  紐付け更新エラー: {e}")

        print()

    # 結果サマリー
    print("=" * 70)
    print("再処理完了")
    print("=" * 70)
    print(f"総会議数: {stats['total']}")
    print(f"Enhanced JSON発見: {stats['enhanced_json_found']}")
    print(f"Enhanced JSON未発見: {stats['enhanced_json_not_found']}")
    print(f"参加者抽出数: {stats['participants_extracted']}")
    print(f"参加者登録数: {stats['participants_registered']}")
    print(f"会議更新数: {stats['meetings_updated']}")
    print(f"スキップ: {stats['skipped']}")
    print()

    if dry_run:
        print("ℹ️  DRY-RUNモードでした。実際のDB更新は行われていません。")
        print("本実行するには --dry-run オプションなしで実行してください。")
    else:
        print("✅ データベースが正常に更新されました。")
        print("確認コマンド: ./scripts/db_inspect.sh")


def main():
    parser = argparse.ArgumentParser(description='既存会議データの参加者情報再処理')
    parser.add_argument('--dry-run', action='store_true',
                        help='実際のDB更新なしでプレビュー')
    parser.add_argument('--force', action='store_true',
                        help='既存参加者も上書き')

    args = parser.parse_args()

    try:
        reprocess_meetings(dry_run=args.dry_run, force=args.force)
    except KeyboardInterrupt:
        print("\n\n⚠️  処理を中断しました")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
