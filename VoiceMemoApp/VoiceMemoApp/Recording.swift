import Foundation
import SwiftData

@Model
final class Recording {
    @Attribute(.unique) var id: UUID
    var createdAt: Date
    var title: String?
    var audioFileName: String
    var duration: TimeInterval
    var fileSize: Int64

    // Phase 3: 文字起こし用フィールド
    var transcriptText: String?
    var transcriptJSON: Data?
    var status: String
    var errorMessage: String?
    var processedAt: Date?

    init(
        id: UUID = UUID(),
        createdAt: Date = Date(),
        title: String? = nil,
        audioFileName: String,
        duration: TimeInterval = 0,
        fileSize: Int64 = 0,
        transcriptText: String? = nil,
        transcriptJSON: Data? = nil,
        status: String = "pending",
        errorMessage: String? = nil,
        processedAt: Date? = nil
    ) {
        self.id = id
        self.createdAt = createdAt
        self.title = title
        self.audioFileName = audioFileName
        self.duration = duration
        self.fileSize = fileSize
        self.transcriptText = transcriptText
        self.transcriptJSON = transcriptJSON
        self.status = status
        self.errorMessage = errorMessage
        self.processedAt = processedAt
    }

    // MARK: - Computed Properties

    var formattedDate: String {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy年M月d日"
        formatter.locale = Locale(identifier: "ja_JP")
        return formatter.string(from: createdAt)
    }

    var formattedTime: String {
        let formatter = DateFormatter()
        formatter.dateFormat = "HH:mm"
        return formatter.string(from: createdAt)
    }

    var dateKey: String {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd"
        return formatter.string(from: createdAt)
    }

    var displayTitle: String {
        title ?? formattedTime
    }

    var formattedDuration: String {
        let minutes = Int(duration) / 60
        let seconds = Int(duration) % 60
        return String(format: "%d:%02d", minutes, seconds)
    }

    var formattedFileSize: String {
        let formatter = ByteCountFormatter()
        formatter.countStyle = .file
        return formatter.string(fromByteCount: fileSize)
    }
}

// MARK: - Status Enum

extension Recording {
    enum Status: String {
        case pending = "pending"
        case uploading = "uploading"
        case processing = "processing"
        case completed = "completed"
        case failed = "failed"
    }

    var recordingStatus: Status {
        get { Status(rawValue: status) ?? .pending }
        set { status = newValue.rawValue }
    }
}
