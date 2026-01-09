import SwiftUI
import SwiftData

struct ContentView: View {
    @Environment(\.modelContext) private var modelContext
    @Query(sort: \Recording.createdAt, order: .reverse) private var recordings: [Recording]
    @StateObject private var audioManager = AudioManager()
    @State private var showingRecordSheet = false
    @State private var showingSettings = false

    private let storageManager = StorageManager.shared

    var groupedRecordings: [(String, [Recording])] {
        let grouped = Dictionary(grouping: recordings) { $0.dateKey }
        return grouped.sorted { $0.key > $1.key }
    }

    var body: some View {
        NavigationStack {
            List {
                if recordings.isEmpty {
                    ContentUnavailableView(
                        "メモがありません",
                        systemImage: "mic.slash",
                        description: Text("右上の＋ボタンをタップして\n録音を開始してください")
                    )
                    .listRowBackground(Color.clear)
                } else {
                    ForEach(groupedRecordings, id: \.0) { dateKey, dayRecordings in
                        Section(header: Text(dayRecordings.first?.formattedDate ?? dateKey)) {
                            ForEach(dayRecordings) { recording in
                                NavigationLink {
                                    RecordingDetailView(
                                        recording: recording,
                                        audioManager: audioManager,
                                        storageManager: storageManager
                                    )
                                } label: {
                                    RecordingRow(
                                        recording: recording,
                                        audioManager: audioManager,
                                        storageManager: storageManager,
                                        modelContext: modelContext
                                    )
                                }
                            }
                            .onDelete { indexSet in
                                for index in indexSet {
                                    let recording = dayRecordings[index]
                                    storageManager.deleteRecording(recording, modelContext: modelContext)
                                }
                            }
                        }
                    }
                }
            }
            .navigationTitle("ボイスメモ")
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button {
                        showingSettings = true
                    } label: {
                        Image(systemName: "gearshape")
                    }
                }
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button {
                        showingRecordSheet = true
                    } label: {
                        Image(systemName: "plus")
                    }
                }
            }
            .sheet(isPresented: $showingRecordSheet) {
                RecordingView(audioManager: audioManager)
            }
            .sheet(isPresented: $showingSettings) {
                SettingsView()
            }
            .onAppear {
                audioManager.setupAudioSession()
            }
        }
    }
}

struct RecordingRow: View {
    @Bindable var recording: Recording
    @ObservedObject var audioManager: AudioManager
    let storageManager: StorageManager
    let modelContext: ModelContext

    @State private var isTranscribing = false

    var isCurrentlyPlaying: Bool {
        audioManager.currentlyPlayingId == recording.id
    }

    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                HStack(spacing: 8) {
                    Text(recording.displayTitle)
                        .font(.headline)

                    // ステータスアイコン
                    statusIcon
                }

                if recording.title != nil {
                    Text(recording.formattedTime)
                        .font(.caption)
                        .foregroundColor(.secondary)
                }

                HStack(spacing: 8) {
                    Text(recording.formattedDuration)
                    Text(recording.formattedFileSize)
                    // ステータステキスト
                    statusText
                }
                .font(.caption2)
                .foregroundColor(.secondary)
            }

            Spacer()

            // 文字起こしボタン（pending状態のみ）
            if recording.recordingStatus == .pending {
                transcribeButton
            }

            // 再生ボタン
            Button {
                if isCurrentlyPlaying {
                    audioManager.stopPlaying()
                } else {
                    let url = storageManager.getFileURL(fileName: recording.audioFileName)
                    audioManager.play(url: url, id: recording.id)
                }
            } label: {
                Image(systemName: isCurrentlyPlaying ? "stop.circle.fill" : "play.circle.fill")
                    .font(.title)
                    .foregroundColor(isCurrentlyPlaying ? .red : .blue)
            }
            .buttonStyle(BorderlessButtonStyle())
        }
        .padding(.vertical, 4)
    }

    @ViewBuilder
    private var statusIcon: some View {
        switch recording.recordingStatus {
        case .pending:
            EmptyView()
        case .uploading, .processing:
            ProgressView()
                .scaleEffect(0.6)
        case .completed:
            Image(systemName: "checkmark.circle.fill")
                .foregroundColor(.green)
                .font(.caption)
        case .failed:
            Image(systemName: "exclamationmark.triangle.fill")
                .foregroundColor(.red)
                .font(.caption)
        }
    }

    @ViewBuilder
    private var statusText: some View {
        switch recording.recordingStatus {
        case .pending:
            EmptyView()
        case .uploading:
            Text("アップロード中")
                .foregroundColor(.blue)
        case .processing:
            Text("処理中")
                .foregroundColor(.blue)
        case .completed:
            Text("文字起こし完了")
                .foregroundColor(.green)
        case .failed:
            Text("エラー")
                .foregroundColor(.red)
        }
    }

    private var transcribeButton: some View {
        Button {
            startTranscription()
        } label: {
            Image(systemName: isTranscribing ? "hourglass" : "text.bubble")
                .font(.title2)
                .foregroundColor(isTranscribing ? .gray : .orange)
        }
        .buttonStyle(BorderlessButtonStyle())
        .disabled(isTranscribing)
    }

    private func startTranscription() {
        guard !isTranscribing else { return }
        isTranscribing = true

        Task {
            do {
                let service = try TranscriptionService()
                try await service.transcribe(recording: recording, modelContext: modelContext)
            } catch {
                recording.recordingStatus = .failed
                recording.errorMessage = error.localizedDescription
                try? modelContext.save()
            }
            isTranscribing = false
        }
    }
}

#Preview {
    ContentView()
        .modelContainer(for: Recording.self, inMemory: true)
}
