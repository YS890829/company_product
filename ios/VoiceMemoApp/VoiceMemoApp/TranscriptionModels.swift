import Foundation

// MARK: - File API レスポンス

struct FileUploadResponse: Codable {
    let file: FileInfo

    struct FileInfo: Codable {
        let name: String
        let uri: String
        let state: String?
        let mimeType: String?
    }
}

struct FileStatusResponse: Codable {
    let name: String
    let uri: String
    let state: String
    let mimeType: String?
}

// MARK: - Gemini API レスポンス

struct GeminiResponse: Codable {
    let candidates: [Candidate]?
    let error: GeminiError?

    struct Candidate: Codable {
        let content: Content
    }

    struct Content: Codable {
        let parts: [Part]
    }

    struct Part: Codable {
        let text: String?
    }

    struct GeminiError: Codable {
        let code: Int
        let message: String
    }
}

// MARK: - 文字起こし結果

struct TranscriptResult: Codable {
    let summary: String
    let keyPoints: [String]
    let actionItems: [ActionItem]
    let fullTranscript: String

    struct ActionItem: Codable, Identifiable {
        var id: String { task }
        let task: String
        let deadline: String?
    }

    static var empty: TranscriptResult {
        TranscriptResult(
            summary: "",
            keyPoints: [],
            actionItems: [],
            fullTranscript: ""
        )
    }
}
