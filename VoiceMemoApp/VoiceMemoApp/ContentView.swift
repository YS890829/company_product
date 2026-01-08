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
                                RecordingRow(
                                    recording: recording,
                                    audioManager: audioManager,
                                    storageManager: storageManager
                                )
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
    let recording: Recording
    @ObservedObject var audioManager: AudioManager
    let storageManager: StorageManager

    var isCurrentlyPlaying: Bool {
        audioManager.currentlyPlayingId == recording.id
    }

    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text(recording.displayTitle)
                    .font(.headline)
                if recording.title != nil {
                    Text(recording.formattedTime)
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                HStack(spacing: 8) {
                    Text(recording.formattedDuration)
                    Text(recording.formattedFileSize)
                }
                .font(.caption2)
                .foregroundColor(.secondary)
            }

            Spacer()

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
}

#Preview {
    ContentView()
        .modelContainer(for: Recording.self, inMemory: true)
}
