import AVFoundation
import Foundation
import SwiftData

final class StorageManager: ObservableObject, Sendable {
    static let shared = StorageManager()

    init() {}

    // MARK: - File Operations

    func getDocumentsDirectory() -> URL {
        FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
    }

    func getFileURL(fileName: String) -> URL {
        getDocumentsDirectory().appendingPathComponent(fileName)
    }

    func deleteAudioFile(fileName: String) {
        let fileURL = getFileURL(fileName: fileName)
        try? FileManager.default.removeItem(at: fileURL)
    }

    func getFileSize(fileName: String) -> Int64 {
        let fileURL = getFileURL(fileName: fileName)
        do {
            let attributes = try FileManager.default.attributesOfItem(atPath: fileURL.path)
            return attributes[.size] as? Int64 ?? 0
        } catch {
            return 0
        }
    }

    func getAudioDuration(fileName: String) -> TimeInterval {
        let fileURL = getFileURL(fileName: fileName)
        do {
            let audioPlayer = try AVAudioPlayer(contentsOf: fileURL)
            return audioPlayer.duration
        } catch {
            return 0
        }
    }
}

// MARK: - SwiftData Helpers

extension StorageManager {
    @MainActor
    func createRecording(fileName: String, modelContext: ModelContext) -> Recording {
        let fileSize = getFileSize(fileName: fileName)
        let duration = getAudioDuration(fileName: fileName)

        let recording = Recording(
            audioFileName: fileName,
            duration: duration,
            fileSize: fileSize
        )

        modelContext.insert(recording)
        return recording
    }

    @MainActor
    func deleteRecording(_ recording: Recording, modelContext: ModelContext) {
        deleteAudioFile(fileName: recording.audioFileName)
        modelContext.delete(recording)
    }
}
