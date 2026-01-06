import Foundation

class StorageManager: ObservableObject {
    @Published var memos: [VoiceMemo] = []

    private let userDefaultsKey = "voiceMemos"

    init() {
        load()
    }

    func save() {
        do {
            let data = try JSONEncoder().encode(memos)
            UserDefaults.standard.set(data, forKey: userDefaultsKey)
        } catch {
            print("Failed to save memos: \(error)")
        }
    }

    func load() {
        guard let data = UserDefaults.standard.data(forKey: userDefaultsKey) else {
            return
        }
        do {
            memos = try JSONDecoder().decode([VoiceMemo].self, from: data)
        } catch {
            print("Failed to load memos: \(error)")
        }
    }

    func add(memo: VoiceMemo) {
        memos.insert(memo, at: 0)
        save()
    }

    func delete(memo: VoiceMemo) {
        let fileURL = getFileURL(fileName: memo.fileName)
        try? FileManager.default.removeItem(at: fileURL)
        memos.removeAll { $0.id == memo.id }
        save()
    }

    func getDocumentsDirectory() -> URL {
        FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
    }

    func getFileURL(fileName: String) -> URL {
        getDocumentsDirectory().appendingPathComponent(fileName)
    }
}
