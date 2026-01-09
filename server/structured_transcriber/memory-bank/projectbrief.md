# Project Brief - リファクタリング版

## プロジェクト名
リアルタイム音声文字起こしシステム（リファクタリング版）

## プロジェクト概要
旧実装（archive_old_structure）を新しいプロジェクト構造に移植し、モダンなPythonアプリケーションとして再構築する。

## 背景
- 2025年10月22日、プロジェクトの大規模リファクタリングを実施
- 旧実装（41ファイル、13モジュール）をarchive_old_structureに移動
- 新構造（src/core, src/services, src/utils等）を作成
- 全機能を新構造に移植することで、保守性・拡張性を向上

## 核心的な問題
1. **コードの複雑化**: 旧実装は機能追加により複雑化（Phase 0-18まで段階的拡張）
2. **構造の不統一**: モジュール間の依存関係が複雑
3. **保守性の低下**: 新機能追加時の影響範囲が不明確

## ソリューション
- **モダンな構造**: src/core, src/services, src/utils等の明確な責務分離
- **段階的移植**: Phase 1（基盤層）→ Phase 6（検証）まで体系的に実施
- **ドキュメント整備**: リファクタリング計画、進捗管理をMemory Bankで管理

## プロジェクトの目標
1. **完全な機能移植**: 旧実装の全機能（文字起こし、Vector DB、Web UI等）を新構造で動作させる
2. **コード品質向上**: 型ヒント、docstring、テストの充実
3. **保守性向上**: モジュール間の依存関係を明確化
4. **拡張性向上**: 新機能追加が容易な構造

## 移植対象の主要機能（旧実装）
1. **文字起こし**: Gemini Audio APIによる音声→テキスト変換
2. **統合パイプライン**: 参加者抽出、話者推論、要約生成（10ステップ）
3. **Vector DB**: ChromaDBによるセマンティック検索・RAG Q&A
4. **データベース**: SQLite参加者DB
5. **サービス連携**: Google Drive/iCloud Drive監視、Google Calendar統合
6. **Web UI**: FastAPI + Streamlit
7. **ファイル管理**: 自動リネーム、重複検知、自動削除

## 成功の定義
- [ ] Phase 1完了: 基盤層（utils, models, config）移植
- [ ] Phase 2完了: コア機能（transcription, pipeline, vector_db）移植
- [ ] Phase 3完了: サービス連携（Google Drive/iCloud/Calendar）移植
- [ ] Phase 4完了: API・Webアプリ移植
- [ ] Phase 5完了: スクリプト・テスト移植
- [ ] Phase 6完了: 全機能の動作検証

## 技術スタック（移植後）
- **言語**: Python 3.10+
- **文字起こし**: Gemini 2.0 Flash Experimental (Audio API)
- **LLM**: Google Gemini 2.0 Flash / 2.5 Pro
- **Vector DB**: ChromaDB (Gemini text-embedding-004)
- **データベース**: SQLite
- **Web**: FastAPI + Streamlit
- **監視**: watchdog (iCloud), FastAPI Webhook (Google Drive)

## 制約条件
- **後方互換性**: 旧実装のデータ（downloads/, data/participants.db, chroma_db/）をそのまま利用
- **環境変数**: 既存の.envをそのまま利用
- **API制限**: Gemini API (1,500 RPD), 同時実行数の制限

## 関連ドキュメント
- [リファクタリング計画](../docs/refactoring_plan.md)
- [進捗管理](progress.md)
- [システムパターン](systemPatterns.md)（作成予定）
- [技術詳細](techContext.md)（作成予定）

## 旧実装ドキュメント（参照用）
- [旧README](../archive_old_structure/README.md)
- [旧Memory Bank](../archive_old_structure/memory-bank/)
- [旧技術ドキュメント](../archive_old_structure/docs/)
