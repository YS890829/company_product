import SwiftUI

struct ContentView: View {
    @StateObject private var storageManager = StorageManager()
    @StateObject private var audioManager = AudioManager()
    @State private var showingRecordSheet = false

    var groupedMemos: [(String, [VoiceMemo])] {
        let grouped = Dictionary(grouping: storageManager.memos) { $0.dateKey }
        return grouped.sorted { $0.key > $1.key }
    }

    var body: some View {
        NavigationStack {
            List {
                if storageManager.memos.isEmpty {
                    ContentUnavailableView(
                        "メモがありません",
                        systemImage: "mic.slash",
                        description: Text("右上の＋ボタンをタップして\n録音を開始してください")
                    )
                    .listRowBackground(Color.clear)
                } else {
                    ForEach(groupedMemos, id: \.0) { dateKey, memos in
                        Section(header: Text(memos.first?.formattedDate ?? dateKey)) {
                            ForEach(memos) { memo in
                                MemoRow(
                                    memo: memo,
                                    audioManager: audioManager,
                                    storageManager: storageManager
                                )
                            }
                            .onDelete { indexSet in
                                for index in indexSet {
                                    storageManager.delete(memo: memos[index])
                                }
                            }
                        }
                    }
                }
            }
            .navigationTitle("ボイスメモ")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button {
                        showingRecordSheet = true
                    } label: {
                        Image(systemName: "plus")
                    }
                }
            }
            .sheet(isPresented: $showingRecordSheet) {
                RecordingView(
                    audioManager: audioManager,
                    storageManager: storageManager
                )
            }
            .onAppear {
                audioManager.setupAudioSession()
            }
        }
    }
}

struct MemoRow: View {
    let memo: VoiceMemo
    @ObservedObject var audioManager: AudioManager
    @ObservedObject var storageManager: StorageManager

    var isCurrentlyPlaying: Bool {
        audioManager.currentlyPlayingId == memo.id
    }

    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text(memo.title ?? memo.formattedTime)
                    .font(.headline)
                if memo.title != nil {
                    Text(memo.formattedTime)
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }

            Spacer()

            Button {
                if isCurrentlyPlaying {
                    audioManager.stopPlaying()
                } else {
                    let url = storageManager.getFileURL(fileName: memo.fileName)
                    audioManager.play(url: url, id: memo.id)
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
}
