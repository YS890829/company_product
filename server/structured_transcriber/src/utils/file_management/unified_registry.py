#!/usr/bin/env python3
"""
Phase 10-3 Updated: 統合ファイルレジストリ（関数ベース）- タイムスタンプベース重複管理

Google Drive + iCloud Drive両方の処理履歴を一元管理
- ユーザー表示名 + original_name + created_time で重複検知
- 同じファイル名でも異なる作成時刻なら別ファイルとして処理
- file_id ↔ ファイル名マッピング
- JSONL形式で追記型ログ

スキーマ:
  - source: 'google_drive' or 'icloud_drive'
  - file_id: Google DriveファイルID (iCloudはnull)
  - user_display_name: ユーザー設定の表示名（拡張子なし）
  - original_name: オリジナルファイル名
  - created_time: ファイル作成時刻 (ISO 8601形式) ← 新規追加
  - renamed_to: リネーム後のファイル名
  - local_path: ローカルファイルパス
  - processed_at: 処理時刻 (ISO 8601形式)
"""

import json
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

# 設定
REGISTRY_FILE = Path(os.getenv('PROCESSED_FILES_REGISTRY', '.processed_files_registry.jsonl'))

# グローバルキャッシュ
_registry_cache = {}  # {composite_key: entry} where composite_key = f"{user_display_name}::{original_name}::{created_time}"
_display_name_index = {}  # {user_display_name: [composite_key1, composite_key2, ...]}
_cache_loaded = False


def _load_registry_cache():
    """レジストリをメモリキャッシュにロード"""
    global _registry_cache, _display_name_index, _cache_loaded

    if _cache_loaded:
        return

    _registry_cache = {}
    _display_name_index = {}

    if not REGISTRY_FILE.exists():
        _cache_loaded = True
        return

    try:
        with open(REGISTRY_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                entry = json.loads(line)
                if 'user_display_name' in entry and entry['user_display_name'] and 'original_name' in entry:
                    # Composite key: display_name::original_name::created_time
                    # 後方互換性: created_timeがない場合は "legacy" を使用
                    created_time = entry.get('created_time', 'legacy')
                    composite_key = f"{entry['user_display_name']}::{entry['original_name']}::{created_time}"
                    _registry_cache[composite_key] = entry

                    # Index by display name for lookup
                    display_name = entry['user_display_name']
                    if display_name not in _display_name_index:
                        _display_name_index[display_name] = []
                    _display_name_index[display_name].append(composite_key)

        _cache_loaded = True
    except Exception as e:
        print(f"[Warning] Failed to load registry: {e}")
        _cache_loaded = True


def is_processed(user_display_name: str, original_name: Optional[str] = None, created_time: Optional[str] = None) -> bool:
    """
    ユーザー表示名 + original_name + created_time で処理済みチェック

    Args:
        user_display_name: ユーザー設定の表示名（拡張子なし）
        original_name: オリジナルファイル名。Noneの場合は表示名のみでチェック
        created_time: ファイル作成時刻 (ISO 8601形式)。Noneの場合は後方互換モード

    Returns:
        bool: 処理済みならTrue
    """
    _load_registry_cache()

    if original_name:
        # Composite key check (exact match)
        if created_time:
            # 新方式: created_time含む
            composite_key = f"{user_display_name}::{original_name}::{created_time}"
            return composite_key in _registry_cache
        else:
            # 後方互換モード: created_timeなしでチェック
            # 同じ display_name + original_name を持つエントリが1つでもあればTrue
            for key in _display_name_index.get(user_display_name, []):
                cached_entry = _registry_cache.get(key)
                if cached_entry and cached_entry.get('original_name') == original_name:
                    return True
            return False
    else:
        # Display name only check (backward compatibility)
        return user_display_name in _display_name_index


def get_by_display_name(user_display_name: str, original_name: Optional[str] = None, created_time: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    ユーザー表示名でレジストリエントリ取得

    Args:
        user_display_name: ユーザー設定の表示名（拡張子なし）
        original_name: オリジナルファイル名。Noneの場合は最新のエントリを返す
        created_time: ファイル作成時刻 (ISO 8601形式)。Noneの場合は後方互換モード

    Returns:
        dict or None: レジストリエントリ、存在しなければNone
    """
    _load_registry_cache()

    if original_name:
        if created_time:
            # 新方式: created_time含む完全一致
            composite_key = f"{user_display_name}::{original_name}::{created_time}"
            return _registry_cache.get(composite_key)
        else:
            # 後方互換モード: original_nameで検索して最初にマッチしたものを返す
            for key in _display_name_index.get(user_display_name, []):
                cached_entry = _registry_cache.get(key)
                if cached_entry and cached_entry.get('original_name') == original_name:
                    return cached_entry
            return None
    else:
        # Return most recent entry for this display name
        if user_display_name in _display_name_index:
            composite_keys = _display_name_index[user_display_name]
            if composite_keys:
                # Return the last (most recent) entry
                return _registry_cache.get(composite_keys[-1])
        return None


def get_all_by_display_name(user_display_name: str) -> List[Dict[str, Any]]:
    """
    ユーザー表示名で全エントリを取得

    Args:
        user_display_name: ユーザー設定の表示名（拡張子なし）

    Returns:
        list: レジストリエントリのリスト（時系列順）
    """
    _load_registry_cache()

    if user_display_name not in _display_name_index:
        return []

    entries = []
    for composite_key in _display_name_index[user_display_name]:
        if composite_key in _registry_cache:
            entries.append(_registry_cache[composite_key])

    return entries


def get_by_file_id(file_id: str) -> Optional[Dict[str, Any]]:
    """
    Google Drive file_idでレジストリエントリ取得

    Args:
        file_id: Google DriveのファイルID

    Returns:
        dict or None: レジストリエントリ、存在しなければNone
    """
    _load_registry_cache()

    for entry in _registry_cache.values():
        if entry.get('file_id') == file_id:
            return entry

    return None


def search(file_id: Optional[str] = None,
          original_name: Optional[str] = None,
          user_display_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    柔軟な検索

    Args:
        file_id: Google DriveのファイルID（オプション）
        original_name: オリジナルファイル名（オプション）
        user_display_name: ユーザー表示名（オプション）

    Returns:
        dict or None: レジストリエントリ、存在しなければNone
    """
    _load_registry_cache()

    for entry in _registry_cache.values():
        if file_id and entry.get('file_id') == file_id:
            return entry
        if original_name and entry.get('original_name') == original_name:
            return entry
        if user_display_name and entry.get('user_display_name') == user_display_name:
            return entry

    return None


def add_to_registry(source: str,
                   original_name: str,
                   user_display_name: str,
                   renamed_to: Optional[str] = None,
                   file_id: Optional[str] = None,
                   local_path: Optional[str] = None,
                   created_time: Optional[str] = None):
    """
    新規エントリをレジストリに追加

    Args:
        source: ファイルソース（'google_drive' or 'icloud_drive'）
        original_name: オリジナルファイル名
        user_display_name: ユーザー設定の表示名（拡張子なし）
        renamed_to: リネーム後のファイル名（オプション）
        file_id: Google DriveファイルID（Google Driveのみ）
        local_path: ローカルファイルパス（オプション）
        created_time: ファイル作成時刻 (ISO 8601形式)（オプション、後方互換性のため）
    """
    _load_registry_cache()

    entry = {
        'source': source,
        'file_id': file_id,
        'user_display_name': user_display_name,
        'original_name': original_name,
        'created_time': created_time,  # 新規追加
        'renamed_to': renamed_to,
        'local_path': local_path,
        'processed_at': datetime.now(timezone.utc).isoformat()
    }

    # Composite key
    # 後方互換性: created_timeがない場合は "legacy" を使用
    created_time_key = created_time if created_time else 'legacy'
    composite_key = f"{user_display_name}::{original_name}::{created_time_key}"

    # メモリキャッシュ更新
    _registry_cache[composite_key] = entry

    # Display name index更新
    if user_display_name not in _display_name_index:
        _display_name_index[user_display_name] = []
    _display_name_index[user_display_name].append(composite_key)

    # ファイルに追記（JSONL形式）
    with open(REGISTRY_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')


def update_renamed(user_display_name: str, renamed_to: str, original_name: Optional[str] = None):
    """
    リネーム後のファイル名を更新

    Args:
        user_display_name: ユーザー設定の表示名
        renamed_to: リネーム後のファイル名
        original_name: オリジナルファイル名。Noneの場合は最新エントリを更新
    """
    _load_registry_cache()

    if original_name:
        # Composite key update
        composite_key = f"{user_display_name}::{original_name}"
        if composite_key not in _registry_cache:
            print(f"[Warning] Composite key not found in registry: {composite_key}")
            return
        _registry_cache[composite_key]['renamed_to'] = renamed_to
    else:
        # Update most recent entry (backward compatibility)
        if user_display_name not in _display_name_index:
            print(f"[Warning] Display name not found in registry: {user_display_name}")
            return

        composite_keys = _display_name_index[user_display_name]
        if composite_keys:
            latest_key = composite_keys[-1]
            _registry_cache[latest_key]['renamed_to'] = renamed_to

    # JSONL全体を再書き込み
    _rewrite_registry()


def _rewrite_registry():
    """レジストリ全体を再書き込み（更新用）"""
    try:
        with open(REGISTRY_FILE, 'w', encoding='utf-8') as f:
            for entry in _registry_cache.values():
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    except Exception as e:
        print(f"[Error] Failed to rewrite registry: {e}")


def get_stats() -> Dict[str, Any]:
    """
    レジストリ統計情報取得

    Returns:
        dict: 統計情報（総件数、Google Drive件数、iCloud件数）
    """
    _load_registry_cache()

    total = len(_registry_cache)
    google_drive = sum(1 for e in _registry_cache.values() if e.get('source') == 'google_drive')
    icloud_drive = sum(1 for e in _registry_cache.values() if e.get('source') == 'icloud_drive')

    return {
        'total': total,
        'google_drive': google_drive,
        'icloud_drive': icloud_drive
    }


if __name__ == "__main__":
    # テスト用コード
    import sys

    if len(sys.argv) < 2:
        print("Usage: python unified_registry.py <display_name>")
        print("\nTest: Check if display name is processed")
        sys.exit(1)

    display_name = sys.argv[1]

    print(f"Checking display name: {display_name}")

    if is_processed(display_name):
        entry = get_by_display_name(display_name)
        print(f"\n✅ Already processed:")
        print(f"  Source: {entry.get('source')}")
        print(f"  Original: {entry.get('original_name')}")
        print(f"  Renamed: {entry.get('renamed_to')}")
        print(f"  Processed at: {entry.get('processed_at')}")
    else:
        print(f"\n❌ Not processed yet")

    # 統計表示
    stats = get_stats()
    print(f"\nRegistry stats:")
    print(f"  Total: {stats['total']}")
    print(f"  Google Drive: {stats['google_drive']}")
    print(f"  iCloud Drive: {stats['icloud_drive']}")
