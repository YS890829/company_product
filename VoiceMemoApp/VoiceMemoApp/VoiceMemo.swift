import Foundation

struct VoiceMemo: Identifiable, Codable {
    let id: UUID
    let fileName: String
    let createdAt: Date
    var title: String?

    init(id: UUID = UUID(), fileName: String, createdAt: Date = Date(), title: String? = nil) {
        self.id = id
        self.fileName = fileName
        self.createdAt = createdAt
        self.title = title
    }

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
}
