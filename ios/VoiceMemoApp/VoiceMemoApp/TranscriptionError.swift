import Foundation

enum TranscriptionError: LocalizedError {
    case noAPIKey
    case invalidAPIKey
    case networkError(underlying: Error)
    case uploadFailed(statusCode: Int)
    case apiFailed(statusCode: Int, message: String)
    case quotaExceeded
    case audioFileNotFound
    case decodingFailed
    case fileProcessing

    var errorDescription: String? {
        switch self {
        case .noAPIKey:
            return "APIキーが設定されていません"
        case .invalidAPIKey:
            return "APIキーが無効です"
        case .networkError:
            return "ネットワークエラーが発生しました"
        case .uploadFailed(let code):
            return "ファイルのアップロードに失敗しました（\(code)）"
        case .apiFailed(_, let message):
            return "API処理に失敗しました: \(message)"
        case .quotaExceeded:
            return "本日の無料枠を超えました。明日再度お試しください"
        case .audioFileNotFound:
            return "音声ファイルが見つかりません"
        case .decodingFailed:
            return "レスポンスの解析に失敗しました"
        case .fileProcessing:
            return "ファイル処理中です。しばらくお待ちください"
        }
    }

    var isRetryable: Bool {
        switch self {
        case .networkError, .uploadFailed, .fileProcessing:
            return true
        case .apiFailed(let code, _):
            return code >= 500 || code == 429
        default:
            return false
        }
    }
}
