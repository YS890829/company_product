import Foundation
import SwiftData

@MainActor
final class TranscriptionService {
    private let apiKey: String
    private let model = "gemini-2.5-flash-lite"

    private let fileAPIBaseURL = "https://generativelanguage.googleapis.com/upload/v1beta/files"
    private let geminiAPIBaseURL = "https://generativelanguage.googleapis.com/v1beta/models"

    // リトライ設定
    private let maxRetries = 3
    private let baseDelaySeconds: UInt64 = 2

    init() throws {
        guard let key = KeychainService.shared.getAPIKey(), !key.isEmpty else {
            throw TranscriptionError.noAPIKey
        }
        self.apiKey = key
    }

    // MARK: - Main Entry Point

    /// メイン処理: 音声ファイルをアップロードし、文字起こしを実行
    func transcribe(recording: Recording, modelContext: ModelContext) async throws {
        // 1. ステータス更新: uploading
        updateStatus(recording, .uploading, modelContext: modelContext)

        // 2. File APIにアップロード（リトライ付き）
        let audioURL = StorageManager.shared.getFileURL(fileName: recording.audioFileName)
        let fileUri = try await withRetry {
            try await self.uploadToFileAPI(audioURL: audioURL, apiKey: self.apiKey)
        }

        // 3. ステータス更新: processing
        updateStatus(recording, .processing, modelContext: modelContext)

        // 4. Gemini APIで文字起こし（リトライ付き）
        let result = try await withRetry {
            try await self.callGeminiAPI(fileUri: fileUri, apiKey: self.apiKey)
        }

        // 5. 結果を保存
        saveResult(recording, result, modelContext: modelContext)

        // 6. (オプション) File APIのファイルを削除
        try? await deleteFromFileAPI(fileUri: fileUri, apiKey: apiKey)
    }

    // MARK: - Retry Logic

    /// 指数バックオフでリトライを実行
    private func withRetry<T>(operation: @escaping () async throws -> T) async throws -> T {
        var lastError: Error?

        for attempt in 0..<maxRetries {
            do {
                return try await operation()
            } catch let error as TranscriptionError {
                lastError = error

                // リトライ不可能なエラーは即座にスロー
                guard error.isRetryable else {
                    throw error
                }

                // 最後の試行ならスロー
                if attempt == maxRetries - 1 {
                    throw error
                }

                // 指数バックオフで待機
                let delay = baseDelaySeconds * UInt64(pow(2.0, Double(attempt)))
                try await Task.sleep(nanoseconds: delay * 1_000_000_000)
            } catch {
                // その他のエラー
                lastError = error

                if attempt == maxRetries - 1 {
                    throw TranscriptionError.networkError(underlying: error)
                }

                let delay = baseDelaySeconds * UInt64(pow(2.0, Double(attempt)))
                try await Task.sleep(nanoseconds: delay * 1_000_000_000)
            }
        }

        throw lastError ?? TranscriptionError.networkError(underlying: URLError(.unknown))
    }

    // MARK: - File API Operations

    /// Google File APIに音声ファイルをアップロード
    nonisolated private func uploadToFileAPI(audioURL: URL, apiKey: String) async throws -> String {
        // ファイルが存在するか確認
        guard FileManager.default.fileExists(atPath: audioURL.path) else {
            throw TranscriptionError.audioFileNotFound
        }

        // ファイルデータを読み込み
        let audioData: Data
        do {
            audioData = try Data(contentsOf: audioURL)
        } catch {
            throw TranscriptionError.audioFileNotFound
        }

        // multipart/form-data の境界文字列を生成
        let boundary = "Boundary-\(UUID().uuidString)"

        // URLを構築
        guard var urlComponents = URLComponents(string: "https://generativelanguage.googleapis.com/upload/v1beta/files") else {
            throw TranscriptionError.networkError(underlying: URLError(.badURL))
        }
        urlComponents.queryItems = [URLQueryItem(name: "key", value: apiKey)]

        guard let url = urlComponents.url else {
            throw TranscriptionError.networkError(underlying: URLError(.badURL))
        }

        // リクエストを構築
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")

        // multipart/form-data ボディを構築
        var body = Data()

        // パート1: メタデータ (JSON)
        let metadata: [String: Any] = [
            "file": [
                "displayName": audioURL.lastPathComponent,
                "mimeType": "audio/mp4"
            ]
        ]
        let metadataJSON = try JSONSerialization.data(withJSONObject: metadata)

        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"metadata\"\r\n".data(using: .utf8)!)
        body.append("Content-Type: application/json\r\n\r\n".data(using: .utf8)!)
        body.append(metadataJSON)
        body.append("\r\n".data(using: .utf8)!)

        // パート2: ファイルデータ
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"file\"; filename=\"\(audioURL.lastPathComponent)\"\r\n".data(using: .utf8)!)
        body.append("Content-Type: audio/mp4\r\n\r\n".data(using: .utf8)!)
        body.append(audioData)
        body.append("\r\n".data(using: .utf8)!)

        // 終端
        body.append("--\(boundary)--\r\n".data(using: .utf8)!)

        request.httpBody = body

        // リクエストを送信
        let (data, response): (Data, URLResponse)
        do {
            (data, response) = try await URLSession.shared.data(for: request)
        } catch {
            throw TranscriptionError.networkError(underlying: error)
        }

        // HTTPレスポンスをチェック
        guard let httpResponse = response as? HTTPURLResponse else {
            throw TranscriptionError.networkError(underlying: URLError(.badServerResponse))
        }

        // ステータスコードをチェック
        guard (200...299).contains(httpResponse.statusCode) else {
            if httpResponse.statusCode == 401 || httpResponse.statusCode == 403 {
                throw TranscriptionError.invalidAPIKey
            }
            if httpResponse.statusCode == 429 {
                throw TranscriptionError.quotaExceeded
            }
            throw TranscriptionError.uploadFailed(statusCode: httpResponse.statusCode)
        }

        // レスポンスをパース
        let uploadResponse: FileUploadResponse
        do {
            uploadResponse = try JSONDecoder().decode(FileUploadResponse.self, from: data)
        } catch {
            throw TranscriptionError.decodingFailed
        }

        // ファイルが処理されるまで待機
        let fileUri = try await waitForFileProcessing(fileName: uploadResponse.file.name, apiKey: apiKey)

        return fileUri
    }

    /// ファイルがACTIVE状態になるまで待機
    nonisolated private func waitForFileProcessing(fileName: String, apiKey: String) async throws -> String {
        let maxAttempts = 30
        let delaySeconds: UInt64 = 2

        for attempt in 0..<maxAttempts {
            // ファイル状態を取得
            guard var urlComponents = URLComponents(string: "https://generativelanguage.googleapis.com/v1beta/\(fileName)") else {
                throw TranscriptionError.networkError(underlying: URLError(.badURL))
            }
            urlComponents.queryItems = [URLQueryItem(name: "key", value: apiKey)]

            guard let url = urlComponents.url else {
                throw TranscriptionError.networkError(underlying: URLError(.badURL))
            }

            var request = URLRequest(url: url)
            request.httpMethod = "GET"

            let (data, response): (Data, URLResponse)
            do {
                (data, response) = try await URLSession.shared.data(for: request)
            } catch {
                throw TranscriptionError.networkError(underlying: error)
            }

            guard let httpResponse = response as? HTTPURLResponse,
                  (200...299).contains(httpResponse.statusCode) else {
                // まだ処理中の可能性があるので待機
                if attempt < maxAttempts - 1 {
                    try await Task.sleep(nanoseconds: delaySeconds * 1_000_000_000)
                    continue
                }
                throw TranscriptionError.fileProcessing
            }

            let statusResponse: FileStatusResponse
            do {
                statusResponse = try JSONDecoder().decode(FileStatusResponse.self, from: data)
            } catch {
                throw TranscriptionError.decodingFailed
            }

            if statusResponse.state == "ACTIVE" {
                return statusResponse.uri
            }

            if statusResponse.state == "FAILED" {
                throw TranscriptionError.uploadFailed(statusCode: 500)
            }

            // PROCESSING状態の場合は待機
            if attempt < maxAttempts - 1 {
                try await Task.sleep(nanoseconds: delaySeconds * 1_000_000_000)
            }
        }

        throw TranscriptionError.fileProcessing
    }

    /// File APIからファイルを削除
    nonisolated private func deleteFromFileAPI(fileUri: String, apiKey: String) async throws {
        // fileUriからファイル名を抽出
        // 例: "https://generativelanguage.googleapis.com/v1beta/files/xxx" -> "files/xxx"
        guard let url = URL(string: fileUri),
              let lastTwoComponents = url.pathComponents.suffix(2).first,
              url.pathComponents.count >= 2 else {
            return
        }

        let fileName = url.pathComponents.suffix(2).joined(separator: "/")

        // 削除URLを構築
        guard var urlComponents = URLComponents(string: "https://generativelanguage.googleapis.com/v1beta/\(fileName)") else {
            return
        }
        urlComponents.queryItems = [URLQueryItem(name: "key", value: apiKey)]

        guard let deleteURL = urlComponents.url else {
            return
        }

        var request = URLRequest(url: deleteURL)
        request.httpMethod = "DELETE"

        // 削除リクエストを送信（エラーは無視）
        _ = try? await URLSession.shared.data(for: request)
    }

    // MARK: - Gemini API Operations

    /// Gemini APIで文字起こしを実行
    nonisolated private func callGeminiAPI(fileUri: String, apiKey: String) async throws -> TranscriptResult {
        // URLを構築
        guard var urlComponents = URLComponents(string: "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent") else {
            throw TranscriptionError.networkError(underlying: URLError(.badURL))
        }
        urlComponents.queryItems = [URLQueryItem(name: "key", value: apiKey)]

        guard let url = urlComponents.url else {
            throw TranscriptionError.networkError(underlying: URLError(.badURL))
        }

        // プロンプトを構築
        let prompt = """
        この音声を文字起こしして、以下のJSON形式で出力してください。
        JSONのみを出力し、他のテキストは含めないでください。

        {
          "summary": "音声内容の要約（2-3文）",
          "keyPoints": ["重要ポイント1", "重要ポイント2", "重要ポイント3"],
          "actionItems": [
            {"task": "アクションアイテム1", "deadline": "期限（あれば）"},
            {"task": "アクションアイテム2", "deadline": null}
          ],
          "fullTranscript": "音声の全文書き起こし"
        }

        注意事項:
        - summaryは簡潔に要約
        - keyPointsは最大5つまで
        - actionItemsはタスクや宿題があれば抽出、なければ空配列
        - fullTranscriptは話者の発言をそのまま書き起こし
        - 日本語で出力
        """

        // リクエストボディを構築
        let requestBody: [String: Any] = [
            "contents": [
                [
                    "parts": [
                        [
                            "fileData": [
                                "mimeType": "audio/mp4",
                                "fileUri": fileUri
                            ]
                        ],
                        [
                            "text": prompt
                        ]
                    ]
                ]
            ],
            "generationConfig": [
                "responseMimeType": "application/json"
            ]
        ]

        let bodyData = try JSONSerialization.data(withJSONObject: requestBody)

        // リクエストを構築
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = bodyData
        request.timeoutInterval = 300 // 5分のタイムアウト（長い音声用）

        // リクエストを送信
        let (data, response): (Data, URLResponse)
        do {
            (data, response) = try await URLSession.shared.data(for: request)
        } catch {
            throw TranscriptionError.networkError(underlying: error)
        }

        // HTTPレスポンスをチェック
        guard let httpResponse = response as? HTTPURLResponse else {
            throw TranscriptionError.networkError(underlying: URLError(.badServerResponse))
        }

        // ステータスコードをチェック
        guard (200...299).contains(httpResponse.statusCode) else {
            if httpResponse.statusCode == 401 || httpResponse.statusCode == 403 {
                throw TranscriptionError.invalidAPIKey
            }
            if httpResponse.statusCode == 429 {
                throw TranscriptionError.quotaExceeded
            }
            // エラーメッセージを抽出
            if let errorResponse = try? JSONDecoder().decode(GeminiResponse.self, from: data),
               let error = errorResponse.error {
                throw TranscriptionError.apiFailed(statusCode: error.code, message: error.message)
            }
            throw TranscriptionError.apiFailed(statusCode: httpResponse.statusCode, message: "Unknown error")
        }

        // レスポンスをパース
        let geminiResponse: GeminiResponse
        do {
            geminiResponse = try JSONDecoder().decode(GeminiResponse.self, from: data)
        } catch {
            throw TranscriptionError.decodingFailed
        }

        // エラーレスポンスをチェック
        if let error = geminiResponse.error {
            if error.code == 429 {
                throw TranscriptionError.quotaExceeded
            }
            throw TranscriptionError.apiFailed(statusCode: error.code, message: error.message)
        }

        // 結果を抽出
        guard let candidates = geminiResponse.candidates,
              let firstCandidate = candidates.first,
              let text = firstCandidate.content.parts.first?.text else {
            throw TranscriptionError.decodingFailed
        }

        // JSON文字列をパース
        let result: TranscriptResult
        do {
            guard let jsonData = text.data(using: .utf8) else {
                throw TranscriptionError.decodingFailed
            }
            result = try JSONDecoder().decode(TranscriptResult.self, from: jsonData)
        } catch {
            // JSONパースに失敗した場合、全文のみを返す
            return TranscriptResult(
                summary: "文字起こし結果",
                keyPoints: [],
                actionItems: [],
                fullTranscript: text
            )
        }

        return result
    }

    // MARK: - Status Updates

    private func updateStatus(_ recording: Recording, _ status: Recording.Status, modelContext: ModelContext) {
        recording.recordingStatus = status
        if status == .failed {
            recording.errorMessage = nil
        }
        try? modelContext.save()
    }

    func updateStatusWithError(_ recording: Recording, error: Error, modelContext: ModelContext) {
        recording.recordingStatus = .failed
        recording.errorMessage = error.localizedDescription
        try? modelContext.save()
    }

    private func saveResult(_ recording: Recording, _ result: TranscriptResult, modelContext: ModelContext) {
        recording.transcriptText = result.fullTranscript
        recording.transcriptJSON = try? JSONEncoder().encode(result)
        recording.recordingStatus = .completed
        recording.processedAt = Date()
        recording.errorMessage = nil
        try? modelContext.save()
    }
}
