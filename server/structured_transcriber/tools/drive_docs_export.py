#!/usr/bin/env python3
"""
Google Docs Export Module (Phase 10-4 拡張 + Enhanced JSON対応)
Enhanced JSONファイルからモバイルフレンドリーなGoogle Docsを生成

使い方:
    from drive_docs_export import export_json_to_docs
    export_json_to_docs('path/to/file_structured_enhanced.json')

機能:
- Enhanced JSONから読みやすいGoogle Docs作成
- 要約・トピック・参加者・全文・アクションアイテム・キーワード・メタデータをフォーマット
- 話者名識別付きセグメント表示
- transcriptionsフォルダへ自動配置
"""

import os
import json
import time
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# 環境変数読み込み
load_dotenv()

# 設定
FOLDER_NAME = os.getenv('DRIVE_UPLOAD_FOLDER', 'transcriptions')
TOKEN_PATH = 'token.json'
# Phase 20: 統一スコープを使用
SCOPES_STR = os.getenv('GOOGLE_ALL_SCOPES', 'https://www.googleapis.com/auth/drive,https://www.googleapis.com/auth/documents,https://www.googleapis.com/auth/calendar.readonly')
SCOPES = [s.strip() for s in SCOPES_STR.split(',')]


def authenticate_services():
    """
    Google Drive + Docs API認証
    既存のtoken.jsonを使用
    """
    creds = None

    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    # トークンが無効または期限切れの場合、リフレッシュ
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            # 更新したトークンを保存
            with open(TOKEN_PATH, 'w') as token:
                token.write(creds.to_json())
        else:
            raise ValueError("有効なtoken.jsonが見つかりません。drive_download.pyで認証を完了してください。")

    drive_service = build('drive', 'v3', credentials=creds)
    docs_service = build('docs', 'v1', credentials=creds)

    return drive_service, docs_service


def get_transcriptions_folder_id(drive_service):
    """
    transcriptionsフォルダIDを取得（既存のdrive_upload.pyと同じロジック）
    """
    query = f"name='{FOLDER_NAME}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    results = drive_service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    folders = results.get('files', [])

    if folders:
        return folders[0]['id']
    else:
        # フォルダが存在しない場合は作成
        file_metadata = {
            'name': FOLDER_NAME,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        folder = drive_service.files().create(body=file_metadata, fields='id').execute()
        print(f"✅ フォルダ '{FOLDER_NAME}' を作成（ID: {folder['id']}）")
        return folder['id']


def read_json_file(json_path):
    """
    JSONファイルを読み込み
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data


def create_google_doc(docs_service, title):
    """
    空のGoogle Documentを作成
    """
    body = {
        'title': title
    }
    doc = docs_service.documents().create(body=body).execute()
    return doc['documentId']


def build_document_requests(data):
    """
    Enhanced JSONデータからGoogle Docs batchUpdate requestsを構築

    ドキュメント構成:
    1. 📊 要約 (summary.overview)
    2. 🎯 トピック (content.topics)
    3. 👥 参加者 (participants)
    4. 📝 全文 (segments with speaker_name)
    5. ✅ アクションアイテム (summary.action_items)
    6. 🏷️ キーワード (summary.keywords)
    7. ℹ️ メタデータ (metadata)
    """
    requests = []
    current_index = 1  # ドキュメントの先頭は1

    # セクション1: 要約
    overview_section = "━━━━━━━━━━━━━━━━━\n📊 要約\n━━━━━━━━━━━━━━━━━\n\n"
    summary_data = data.get('summary', {})

    # summaryが文字列の場合（旧形式）
    if isinstance(summary_data, str):
        overview = summary_data if summary_data else '要約なし'
    # summaryがdictの場合（新形式）
    elif isinstance(summary_data, dict):
        # summary.summary または summary.overview を使用
        overview = summary_data.get('summary', summary_data.get('overview', '要約なし'))
    else:
        overview = '要約なし'

    overview_section += f"{overview}\n\n"

    requests.append({
        'insertText': {
            'location': {'index': current_index},
            'text': overview_section
        }
    })

    # 要約見出しのスタイル適用
    requests.append({
        'updateParagraphStyle': {
            'range': {
                'startIndex': current_index + len("━━━━━━━━━━━━━━━━━\n"),
                'endIndex': current_index + len("━━━━━━━━━━━━━━━━━\n📊 要約\n")
            },
            'paragraphStyle': {
                'namedStyleType': 'HEADING_1'
            },
            'fields': 'namedStyleType'
        }
    })

    current_index += len(overview_section)

    # セクション2: トピック
    topics_section = "━━━━━━━━━━━━━━━━━\n🎯 トピック\n━━━━━━━━━━━━━━━━━\n\n"
    content_data = data.get('content', {})
    topics = content_data.get('topics', [])

    if topics:
        for i, topic in enumerate(topics, 1):
            topic_name = topic.get('name', 'トピック名なし')
            topic_summary = topic.get('summary', '')
            topic_keywords = topic.get('keywords', [])

            topics_section += f"【トピック {i}: {topic_name}】\n"
            if topic_summary:
                topics_section += f"{topic_summary}\n"
            if topic_keywords:
                topics_section += f"キーワード: {', '.join(topic_keywords)}\n"
            topics_section += "\n"
    else:
        topics_section += "トピック情報なし\n\n"

    requests.append({
        'insertText': {
            'location': {'index': current_index},
            'text': topics_section
        }
    })

    # トピック見出しのスタイル適用
    requests.append({
        'updateParagraphStyle': {
            'range': {
                'startIndex': current_index + len("━━━━━━━━━━━━━━━━━\n"),
                'endIndex': current_index + len("━━━━━━━━━━━━━━━━━\n🎯 トピック\n")
            },
            'paragraphStyle': {
                'namedStyleType': 'HEADING_1'
            },
            'fields': 'namedStyleType'
        }
    })

    current_index += len(topics_section)

    # セクション3: 参加者
    participants_section = "━━━━━━━━━━━━━━━━━\n👥 参加者\n━━━━━━━━━━━━━━━━━\n\n"
    participants_raw = data.get('participants', [])

    # participantsがdictの場合（新形式）
    if isinstance(participants_raw, dict):
        canonical_names = participants_raw.get('canonical_names', [])
        if canonical_names:
            for name in canonical_names:
                participants_section += f"• {name}\n"
            participants_section += "\n"
        else:
            participants_section += "参加者情報なし\n\n"
    # participantsがlistの場合（旧形式）
    elif isinstance(participants_raw, list) and participants_raw:
        for participant in participants_raw:
            if isinstance(participant, dict):
                canonical_name = participant.get('canonical_name', '名前不明')
                organization = participant.get('organization', '')
                if organization:
                    participants_section += f"• {canonical_name} ({organization})\n"
                else:
                    participants_section += f"• {canonical_name}\n"
            elif isinstance(participant, str):
                participants_section += f"• {participant}\n"
        participants_section += "\n"
    else:
        participants_section += "参加者情報なし\n\n"

    requests.append({
        'insertText': {
            'location': {'index': current_index},
            'text': participants_section
        }
    })

    # 参加者見出しのスタイル適用
    requests.append({
        'updateParagraphStyle': {
            'range': {
                'startIndex': current_index + len("━━━━━━━━━━━━━━━━━\n"),
                'endIndex': current_index + len("━━━━━━━━━━━━━━━━━\n👥 参加者\n")
            },
            'paragraphStyle': {
                'namedStyleType': 'HEADING_1'
            },
            'fields': 'namedStyleType'
        }
    })

    current_index += len(participants_section)

    # セクション4: 全文（話者名付きセグメント）
    transcript_section = "━━━━━━━━━━━━━━━━━\n📝 全文\n━━━━━━━━━━━━━━━━━\n\n"

    segments = data.get('segments', [])
    if segments:
        for seg in segments:
            # Enhanced JSONではspeaker_nameフィールドを使用
            speaker_name = seg.get('speaker_name', seg.get('speaker', 'Unknown'))
            timestamp = seg.get('timestamp', '00:00')
            text = seg.get('text', '')
            transcript_section += f"{speaker_name} ({timestamp})\n{text}\n\n"
    else:
        transcript_section += "文字起こしテキストなし\n\n"

    requests.append({
        'insertText': {
            'location': {'index': current_index},
            'text': transcript_section
        }
    })

    # 全文見出しのスタイル適用
    requests.append({
        'updateParagraphStyle': {
            'range': {
                'startIndex': current_index + len("━━━━━━━━━━━━━━━━━\n"),
                'endIndex': current_index + len("━━━━━━━━━━━━━━━━━\n📝 全文\n")
            },
            'paragraphStyle': {
                'namedStyleType': 'HEADING_1'
            },
            'fields': 'namedStyleType'
        }
    })

    current_index += len(transcript_section)

    # セクション5: アクションアイテム
    action_items_section = "━━━━━━━━━━━━━━━━━\n✅ アクションアイテム\n━━━━━━━━━━━━━━━━━\n\n"

    # summaryがdictの場合のみaction_itemsを取得
    if isinstance(summary_data, dict):
        action_items = summary_data.get('action_items', [])
    else:
        action_items = []

    if action_items:
        for item in action_items:
            action_items_section += f"• {item}\n"
        action_items_section += "\n"
    else:
        action_items_section += "アクションアイテムなし\n\n"

    requests.append({
        'insertText': {
            'location': {'index': current_index},
            'text': action_items_section
        }
    })

    # アクションアイテム見出しのスタイル適用
    requests.append({
        'updateParagraphStyle': {
            'range': {
                'startIndex': current_index + len("━━━━━━━━━━━━━━━━━\n"),
                'endIndex': current_index + len("━━━━━━━━━━━━━━━━━\n✅ アクションアイテム\n")
            },
            'paragraphStyle': {
                'namedStyleType': 'HEADING_1'
            },
            'fields': 'namedStyleType'
        }
    })

    current_index += len(action_items_section)

    # セクション6: キーワード
    keywords_section = "━━━━━━━━━━━━━━━━━\n🏷️ キーワード\n━━━━━━━━━━━━━━━━━\n\n"

    # summaryがdictの場合のみkeywordsを取得
    if isinstance(summary_data, dict):
        keywords = summary_data.get('keywords', [])
    else:
        keywords = []

    if keywords:
        keywords_section += f"{', '.join(keywords)}\n\n"
    else:
        keywords_section += "キーワードなし\n\n"

    requests.append({
        'insertText': {
            'location': {'index': current_index},
            'text': keywords_section
        }
    })

    # キーワード見出しのスタイル適用
    requests.append({
        'updateParagraphStyle': {
            'range': {
                'startIndex': current_index + len("━━━━━━━━━━━━━━━━━\n"),
                'endIndex': current_index + len("━━━━━━━━━━━━━━━━━\n🏷️ キーワード\n")
            },
            'paragraphStyle': {
                'namedStyleType': 'HEADING_1'
            },
            'fields': 'namedStyleType'
        }
    })

    current_index += len(keywords_section)

    # セクション7: メタデータ
    metadata_section = "━━━━━━━━━━━━━━━━━\nℹ️ メタデータ\n━━━━━━━━━━━━━━━━━\n\n"

    metadata = data.get('metadata', {})
    transcription_meta = metadata.get('transcription', {})
    file_meta = metadata.get('file', {})
    meeting_meta = data.get('meeting', {})

    # メタデータ項目
    metadata_items = []

    # ミーティング情報
    if meeting_meta.get('title'):
        metadata_items.append(f"• タイトル: {meeting_meta['title']}")

    # 文字起こし情報
    metadata_items.extend([
        f"• 文字起こし日時: {transcription_meta.get('transcribed_at', 'N/A')}",
        f"• 言語: {transcription_meta.get('language', 'N/A')}",
        f"• 文字数: {transcription_meta.get('char_count', 0):,}",
        f"• 単語数: {transcription_meta.get('word_count', 0):,}",
        f"• セグメント数: {transcription_meta.get('segment_count', 0)}",
    ])

    # ファイル情報
    metadata_items.extend([
        f"• ファイル名: {file_meta.get('file_name', 'N/A')}",
        f"• ファイルサイズ: {file_meta.get('file_size_bytes', 0) / 1024 / 1024:.2f} MB",
    ])

    # 音声長がある場合
    if file_meta.get('duration_seconds'):
        duration = file_meta['duration_seconds']
        metadata_items.append(f"• 音声長: {duration:.1f}秒 ({duration/60:.1f}分)")

    metadata_section += "\n".join(metadata_items) + "\n"

    requests.append({
        'insertText': {
            'location': {'index': current_index},
            'text': metadata_section
        }
    })

    # メタデータ見出しのスタイル適用
    requests.append({
        'updateParagraphStyle': {
            'range': {
                'startIndex': current_index + len("━━━━━━━━━━━━━━━━━\n"),
                'endIndex': current_index + len("━━━━━━━━━━━━━━━━━\nℹ️ メタデータ\n")
            },
            'paragraphStyle': {
                'namedStyleType': 'HEADING_1'
            },
            'fields': 'namedStyleType'
        }
    })

    return requests


def export_json_to_docs(json_path, max_retries=3):
    """
    JSONファイルからGoogle Docsを作成してtranscriptionsフォルダへ配置

    Args:
        json_path: 入力JSONファイルパス
        max_retries: リトライ回数

    Returns:
        bool: 成功時True、失敗時False
    """
    json_path = Path(json_path)

    if not json_path.exists():
        print(f"⚠️  ファイルが見つかりません: {json_path}")
        return False

    print(f"\n📄 Google Docs作成中...")
    print(f"   ファイル: {json_path.name}")

    try:
        # 認証
        drive_service, docs_service = authenticate_services()

        # JSONデータ読み込み
        data = read_json_file(json_path)

        # ドキュメントタイトル（.jsonを除去）
        doc_title = json_path.stem.replace('_structured_enhanced', '')

        # Google Docs作成
        doc_id = create_google_doc(docs_service, doc_title)
        print(f"✅ ドキュメント作成: {doc_title}")

        # コンテンツ挿入リクエスト構築
        requests = build_document_requests(data)

        # batchUpdate実行（リトライロジック付き）
        for attempt in range(max_retries):
            try:
                docs_service.documents().batchUpdate(
                    documentId=doc_id,
                    body={'requests': requests}
                ).execute()
                print(f"✅ コンテンツ挿入完了")
                break
            except HttpError as e:
                if e.resp.status == 429 and attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 2
                    print(f"⚠️  Rate limit（試行 {attempt + 1}/{max_retries}）: {wait_time}秒待機...")
                    time.sleep(wait_time)
                else:
                    raise

        # transcriptionsフォルダへ移動
        folder_id = get_transcriptions_folder_id(drive_service)

        drive_service.files().update(
            fileId=doc_id,
            addParents=folder_id,
            fields='id, parents'
        ).execute()

        print(f"✅ Google Docs作成完了: {doc_title}")
        print(f"   URL: https://docs.google.com/document/d/{doc_id}/edit")
        print(f"📱 スマホからアクセス: Google Drive → マイドライブ → {FOLDER_NAME}")

        return True

    except HttpError as e:
        print(f"❌ Google API エラー: {e}")
        return False
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("使い方: python drive_docs_export.py <Enhanced JSONファイルパス>")
        print("例: python drive_docs_export.py downloads/test_structured_enhanced.json")
        sys.exit(1)

    json_path = sys.argv[1]
    success = export_json_to_docs(json_path)

    if success:
        print("\n✅ Google Docs エクスポート完了")
    else:
        print("\n❌ Google Docs エクスポート失敗")
        sys.exit(1)
