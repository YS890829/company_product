import Foundation
import SwiftData

// MARK: - ExportService

@MainActor
final class ExportService {

    // MARK: - Export Format

    enum ExportFormat {
        case json
        case text
    }

    // MARK: - Export Data Model (for JSON)

    struct ExportData: Codable {
        let exportedAt: String
        let totalRecordings: Int
        let recordings: [RecordingExport]

        struct RecordingExport: Codable {
            let id: String
            let createdAt: String
            let title: String?
            let duration: Double
            let fileSize: Int64
            let status: String
            let transcript: TranscriptExport?
        }

        struct TranscriptExport: Codable {
            let summary: String
            let keyPoints: [String]
            let actionItems: [ActionItemExport]
            let fullTranscript: String
        }

        struct ActionItemExport: Codable {
            let task: String
            let deadline: String?
        }
    }

    // MARK: - Export All Recordings

    /// 全録音データをJSON形式でエクスポート
    func exportAllAsJSON(recordings: [Recording]) -> Data? {
        let dateFormatter = ISO8601DateFormatter()

        let recordingExports: [ExportData.RecordingExport] = recordings.map { recording in
            var transcriptExport: ExportData.TranscriptExport? = nil

            if let jsonData = recording.transcriptJSON,
               let result = try? JSONDecoder().decode(TranscriptResult.self, from: jsonData) {
                transcriptExport = ExportData.TranscriptExport(
                    summary: result.summary,
                    keyPoints: result.keyPoints,
                    actionItems: result.actionItems.map {
                        ExportData.ActionItemExport(task: $0.task, deadline: $0.deadline)
                    },
                    fullTranscript: result.fullTranscript
                )
            }

            return ExportData.RecordingExport(
                id: recording.id.uuidString,
                createdAt: dateFormatter.string(from: recording.createdAt),
                title: recording.title,
                duration: recording.duration,
                fileSize: recording.fileSize,
                status: recording.status,
                transcript: transcriptExport
            )
        }

        let exportData = ExportData(
            exportedAt: dateFormatter.string(from: Date()),
            totalRecordings: recordings.count,
            recordings: recordingExports
        )

        let encoder = JSONEncoder()
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys]

        return try? encoder.encode(exportData)
    }

    /// 全録音データをテキスト形式でエクスポート
    func exportAllAsText(recordings: [Recording]) -> String {
        let dateFormatter = DateFormatter()
        dateFormatter.dateFormat = "yyyy年M月d日 HH:mm"
        dateFormatter.locale = Locale(identifier: "ja_JP")

        var text = "# ボイスメモ エクスポート\n"
        text += "エクスポート日時: \(dateFormatter.string(from: Date()))\n"
        text += "録音数: \(recordings.count)件\n"
        text += "\n" + String(repeating: "=", count: 50) + "\n\n"

        for recording in recordings.sorted(by: { $0.createdAt > $1.createdAt }) {
            text += formatRecordingAsText(recording, dateFormatter: dateFormatter)
            text += "\n" + String(repeating: "-", count: 50) + "\n\n"
        }

        return text
    }

    // MARK: - Export Single Recording

    /// 個別録音をテキスト形式でエクスポート
    func exportRecordingAsText(_ recording: Recording) -> String {
        let dateFormatter = DateFormatter()
        dateFormatter.dateFormat = "yyyy年M月d日 HH:mm"
        dateFormatter.locale = Locale(identifier: "ja_JP")

        return formatRecordingAsText(recording, dateFormatter: dateFormatter)
    }

    /// 個別録音をJSON形式でエクスポート
    func exportRecordingAsJSON(_ recording: Recording) -> Data? {
        let dateFormatter = ISO8601DateFormatter()

        var transcriptExport: ExportData.TranscriptExport? = nil

        if let jsonData = recording.transcriptJSON,
           let result = try? JSONDecoder().decode(TranscriptResult.self, from: jsonData) {
            transcriptExport = ExportData.TranscriptExport(
                summary: result.summary,
                keyPoints: result.keyPoints,
                actionItems: result.actionItems.map {
                    ExportData.ActionItemExport(task: $0.task, deadline: $0.deadline)
                },
                fullTranscript: result.fullTranscript
            )
        }

        let recordingExport = ExportData.RecordingExport(
            id: recording.id.uuidString,
            createdAt: dateFormatter.string(from: recording.createdAt),
            title: recording.title,
            duration: recording.duration,
            fileSize: recording.fileSize,
            status: recording.status,
            transcript: transcriptExport
        )

        let encoder = JSONEncoder()
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys]

        return try? encoder.encode(recordingExport)
    }

    // MARK: - Private Methods

    private func formatRecordingAsText(_ recording: Recording, dateFormatter: DateFormatter) -> String {
        var text = ""

        // ヘッダー
        text += "## \(recording.displayTitle)\n"
        text += "日時: \(dateFormatter.string(from: recording.createdAt))\n"
        text += "長さ: \(recording.formattedDuration)\n"
        text += "ステータス: \(statusText(recording.recordingStatus))\n\n"

        // 文字起こし結果
        if let jsonData = recording.transcriptJSON,
           let result = try? JSONDecoder().decode(TranscriptResult.self, from: jsonData) {

            // 要約
            if !result.summary.isEmpty {
                text += "### 要約\n"
                text += result.summary + "\n\n"
            }

            // 重要ポイント
            if !result.keyPoints.isEmpty {
                text += "### 重要ポイント\n"
                for point in result.keyPoints {
                    text += "・\(point)\n"
                }
                text += "\n"
            }

            // アクションアイテム
            if !result.actionItems.isEmpty {
                text += "### アクションアイテム\n"
                for item in result.actionItems {
                    if let deadline = item.deadline, !deadline.isEmpty {
                        text += "・\(item.task)（期限: \(deadline)）\n"
                    } else {
                        text += "・\(item.task)\n"
                    }
                }
                text += "\n"
            }

            // 全文
            if !result.fullTranscript.isEmpty {
                text += "### 全文\n"
                text += result.fullTranscript + "\n"
            }
        } else if recording.recordingStatus == .pending {
            text += "（文字起こし未実行）\n"
        } else if recording.recordingStatus == .failed {
            text += "（文字起こし失敗: \(recording.errorMessage ?? "不明なエラー")）\n"
        } else {
            text += "（処理中...）\n"
        }

        return text
    }

    private func statusText(_ status: Recording.Status) -> String {
        switch status {
        case .pending: return "未処理"
        case .uploading: return "アップロード中"
        case .processing: return "処理中"
        case .completed: return "完了"
        case .failed: return "エラー"
        }
    }

    // MARK: - File Export

    /// JSONをファイルとして保存してURLを返す
    func saveJSONToFile(recordings: [Recording]) -> URL? {
        guard let data = exportAllAsJSON(recordings: recordings) else { return nil }

        let dateFormatter = DateFormatter()
        dateFormatter.dateFormat = "yyyyMMdd_HHmmss"
        let fileName = "voicememo_export_\(dateFormatter.string(from: Date())).json"

        let tempDir = FileManager.default.temporaryDirectory
        let fileURL = tempDir.appendingPathComponent(fileName)

        do {
            try data.write(to: fileURL)
            return fileURL
        } catch {
            return nil
        }
    }

    /// テキストをファイルとして保存してURLを返す
    func saveTextToFile(recordings: [Recording]) -> URL? {
        let text = exportAllAsText(recordings: recordings)

        let dateFormatter = DateFormatter()
        dateFormatter.dateFormat = "yyyyMMdd_HHmmss"
        let fileName = "voicememo_export_\(dateFormatter.string(from: Date())).txt"

        let tempDir = FileManager.default.temporaryDirectory
        let fileURL = tempDir.appendingPathComponent(fileName)

        do {
            try text.write(to: fileURL, atomically: true, encoding: .utf8)
            return fileURL
        } catch {
            return nil
        }
    }
}
