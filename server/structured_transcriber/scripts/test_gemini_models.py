#!/usr/bin/env python3
"""
Gemini APIモデル動作確認スクリプト（Phase 1A検証用）

使い方:
    python scripts/test_gemini_models.py

確認内容:
1. gemini-2.5-pro-exp-03-25 が利用可能か
2. フォールバック機能が正常に動作するか
3. 各モデルのレスポンス品質
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# .envファイルを読み込み
load_dotenv()

# Gemini API Key（無料枠）
GEMINI_API_KEY_FREE = os.getenv("GEMINI_API_KEY_FREE")
if not GEMINI_API_KEY_FREE:
    print("❌ エラー: GEMINI_API_KEY_FREE が設定されていません")
    sys.exit(1)

genai.configure(api_key=GEMINI_API_KEY_FREE)

print("=" * 70)
print("Gemini API モデル動作確認（Phase 1A検証）")
print("=" * 70)
print()

# テスト用プロンプト
test_prompt = """以下の会話から、各話者が誰かを推論してください。

Speaker 1: おはようございます。今日は天気が良いですね。
Speaker 2: そうですね。散歩日和です。

JSON形式で回答してください:
{
  "speaker_1": "推定される人物",
  "speaker_2": "推定される人物",
  "reasoning": "判断理由"
}
"""

# テスト1: gemini-2.5-pro-exp-03-25
print("【テスト1】gemini-2.5-pro-exp-03-25")
print("-" * 70)
try:
    model = genai.GenerativeModel('gemini-2.5-pro-exp-03-25')
    response = model.generate_content(
        test_prompt,
        generation_config={'temperature': 0.1}
    )
    print("✅ 成功")
    print(f"レスポンス長: {len(response.text)} 文字")
    print(f"プレビュー: {response.text[:200]}...")
    print()
except Exception as e:
    print(f"❌ 失敗: {e}")
    print()

# テスト2: gemini-2.5-flash
print("【テスト2】gemini-2.5-flash")
print("-" * 70)
try:
    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content(
        test_prompt,
        generation_config={'temperature': 0.1}
    )
    print("✅ 成功")
    print(f"レスポンス長: {len(response.text)} 文字")
    print(f"プレビュー: {response.text[:200]}...")
    print()
except Exception as e:
    print(f"❌ 失敗: {e}")
    print()

# テスト3: フォールバック機能のシミュレーション
print("【テスト3】フォールバック機能のシミュレーション")
print("-" * 70)

def test_with_fallback(prompt):
    """フォールバック機能付きモデル呼び出し"""
    try:
        model = genai.GenerativeModel('gemini-2.5-pro-exp-03-25')
        print("  → gemini-2.5-pro-exp-03-25 を試行中...")
        response = model.generate_content(prompt, generation_config={'temperature': 0.1})
        print("  ✅ gemini-2.5-pro-exp-03-25 で成功")
        return response
    except Exception as e:
        error_msg = str(e).lower()
        if 'not found' in error_msg or 'unavailable' in error_msg or 'invalid model' in error_msg:
            print(f"  ⚠️  gemini-2.5-pro-exp-03-25 が利用不可: {e}")
            print("  → gemini-2.5-flash にフォールバック中...")
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(prompt, generation_config={'temperature': 0.1})
            print("  ✅ gemini-2.5-flash で成功")
            return response
        else:
            raise

try:
    response = test_with_fallback(test_prompt)
    print(f"レスポンス長: {len(response.text)} 文字")
    print()
except Exception as e:
    print(f"❌ フォールバックも失敗: {e}")
    print()

# テスト4: レート制限情報の表示
print("【参考】無料枠レート制限")
print("-" * 70)
print("gemini-2.5-pro-exp-03-25:")
print("  - RPM: 5 (12秒に1回)")
print("  - RPD: 100")
print("  - TPM: 125,000")
print()
print("gemini-2.5-flash:")
print("  - RPM: 10 (6秒に1回)")
print("  - RPD: 250")
print("  - TPM: 250,000")
print()

print("=" * 70)
print("✅ テスト完了")
print("=" * 70)
print()
print("【次のステップ】")
print("1. すべてのテストが成功していることを確認")
print("2. 実際の文字起こしでテスト:")
print("   python src/transcription/structured_transcribe.py downloads/<テストファイル>.m4a")
print()
