# Realtime Transcriber Benchmark Research

リアルタイム音声文字起こしのベンチマーク研究プロジェクト（リファクタリング版）

## プロジェクト概要

このプロジェクトは、音声文字起こしシステムのベンチマークと研究を行うためのものです。

## プロジェクト構成

```
.
├── README.md                    # このファイル
├── requirements.txt             # Python依存パッケージ
├── .env                         # 環境変数（Git管理外）
├── .env.example                 # 環境変数サンプル
├── .gitignore                   # Git除外設定
│
├── src/                         # ソースコード
│   ├── core/                    # コアモジュール
│   ├── services/                # 外部サービス連携
│   ├── utils/                   # ユーティリティ
│   ├── models/                  # データモデル
│   └── api/                     # APIエンドポイント
│
├── config/                      # 設定ファイル
│   ├── __init__.py
│   └── settings.py              # プロジェクト設定
│
├── tests/                       # テストコード
│   ├── __init__.py
│   └── conftest.py              # pytest設定
│
├── scripts/                     # 実行スクリプト
│
├── docs/                        # ドキュメント
│
├── data/                        # データディレクトリ
│   ├── raw/                     # 生データ
│   ├── processed/               # 処理済みデータ
│   └── output/                  # 出力データ
│
├── logs/                        # ログファイル
│
├── venv/                        # Python仮想環境（Git管理外）
│
└── archive_old_structure/       # 旧プロジェクト構造のアーカイブ
    ├── src/                     # 旧ソースコード
    ├── scripts/                 # 旧スクリプト
    ├── docs/                    # 旧ドキュメント
    ├── memory-bank/             # プロジェクト履歴
    └── ...                      # その他旧ファイル
```

## セットアップ

### 1. 仮想環境の作成と有効化

```bash
# 仮想環境作成
python3 -m venv venv

# 仮想環境有効化（macOS/Linux）
source venv/bin/activate

# 仮想環境有効化（Windows）
venv\Scripts\activate
```

### 2. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### 3. 環境変数の設定

```bash
# .env.exampleをコピー
cp .env.example .env

# .envファイルを編集して必要な環境変数を設定
```

## 開発ガイド

### コーディング規約

- PEP 8に準拠
- 型ヒントの使用を推奨
- docstringの記述

### テストの実行

```bash
pytest tests/
```

## 旧プロジェクト構造について

このプロジェクトは2025年10月にリファクタリングされました。

旧プロジェクト構造のすべてのファイルは [archive_old_structure/](archive_old_structure/) ディレクトリに保存されています。

### 旧プロジェクトの主要機能

- 音声文字起こし（Gemini Audio API）
- Google Drive/iCloud Drive連携
- 参加者管理・話者推論
- Vector DB（ChromaDB）によるセマンティック検索
- Web UI（FastAPI + Streamlit）

詳細は [archive_old_structure/README.md](archive_old_structure/README.md) を参照してください。

### 旧ドキュメント

- 技術ドキュメント: [archive_old_structure/docs/](archive_old_structure/docs/)
- プロジェクト履歴: [archive_old_structure/memory-bank/](archive_old_structure/memory-bank/)

## ライセンス

MIT License
