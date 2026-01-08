import SwiftUI
import SwiftData

struct RecordingDetailView: View {
    @Environment(\.modelContext) private var modelContext
    @Bindable var recording: Recording
    @ObservedObject var audioManager: AudioManager
    let storageManager: StorageManager

    @State private var isTranscribing = false
    @State private var showFullTranscript = false

    private var transcriptResult: TranscriptResult? {
        guard let data = recording.transcriptJSON else { return nil }
        return try? JSONDecoder().decode(TranscriptResult.self, from: data)
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                // 録音情報ヘッダー
                recordingHeader

                Divider()

                // ステータス別表示
                switch recording.recordingStatus {
                case .pending:
                    pendingView
                case .uploading:
                    progressView(message: "アップロード中...")
                case .processing:
                    progressView(message: "文字起こし中...")
                case .completed:
                    if let result = transcriptResult {
                        transcriptResultView(result: result)
                    } else if let text = recording.transcriptText {
                        fallbackTranscriptView(text: text)
                    }
                case .failed:
                    failedView
                }
            }
            .padding()
        }
        .navigationTitle(recording.displayTitle)
        .navigationBarTitleDisplayMode(.inline)
    }

    // MARK: - Recording Header

    private var recordingHeader: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text(recording.formattedDate)
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                    Text(recording.formattedTime)
                        .font(.headline)
                }

                Spacer()

                // 再生ボタン
                playButton
            }

            HStack(spacing: 16) {
                Label(recording.formattedDuration, systemImage: "clock")
                Label(recording.formattedFileSize, systemImage: "doc")
            }
            .font(.caption)
            .foregroundColor(.secondary)
        }
    }

    private var playButton: some View {
        let isPlaying = audioManager.currentlyPlayingId == recording.id

        return Button {
            if isPlaying {
                audioManager.stopPlaying()
            } else {
                let url = storageManager.getFileURL(fileName: recording.audioFileName)
                audioManager.play(url: url, id: recording.id)
            }
        } label: {
            HStack {
                Image(systemName: isPlaying ? "stop.fill" : "play.fill")
                Text(isPlaying ? "停止" : "再生")
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 8)
            .background(isPlaying ? Color.red : Color.blue)
            .foregroundColor(.white)
            .cornerRadius(8)
        }
    }

    // MARK: - Pending View

    private var pendingView: some View {
        VStack(spacing: 16) {
            Image(systemName: "waveform")
                .font(.system(size: 48))
                .foregroundColor(.secondary)

            Text("文字起こしが完了していません")
                .font(.headline)

            Button {
                startTranscription()
            } label: {
                HStack {
                    if isTranscribing {
                        ProgressView()
                            .progressViewStyle(CircularProgressViewStyle(tint: .white))
                            .scaleEffect(0.8)
                    } else {
                        Image(systemName: "text.bubble")
                    }
                    Text(isTranscribing ? "処理中..." : "文字起こしを開始")
                }
                .frame(maxWidth: .infinity)
                .padding()
                .background(isTranscribing ? Color.gray : Color.blue)
                .foregroundColor(.white)
                .cornerRadius(10)
            }
            .disabled(isTranscribing)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 40)
    }

    // MARK: - Progress View

    private func progressView(message: String) -> some View {
        VStack(spacing: 16) {
            ProgressView()
                .scaleEffect(1.5)
                .padding()

            Text(message)
                .font(.headline)
                .foregroundColor(.secondary)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 40)
    }

    // MARK: - Transcript Result View

    private func transcriptResultView(result: TranscriptResult) -> some View {
        VStack(alignment: .leading, spacing: 24) {
            // 要約セクション
            if !result.summary.isEmpty {
                sectionView(title: "要約", icon: "doc.text") {
                    Text(result.summary)
                        .font(.body)
                }
            }

            // 重要ポイントセクション
            if !result.keyPoints.isEmpty {
                sectionView(title: "重要ポイント", icon: "star") {
                    VStack(alignment: .leading, spacing: 8) {
                        ForEach(result.keyPoints, id: \.self) { point in
                            HStack(alignment: .top, spacing: 8) {
                                Image(systemName: "circle.fill")
                                    .font(.system(size: 6))
                                    .foregroundColor(.blue)
                                    .padding(.top, 6)
                                Text(point)
                                    .font(.body)
                            }
                        }
                    }
                }
            }

            // アクションアイテムセクション
            if !result.actionItems.isEmpty {
                sectionView(title: "アクションアイテム", icon: "checkmark.circle") {
                    VStack(alignment: .leading, spacing: 12) {
                        ForEach(result.actionItems) { item in
                            HStack(alignment: .top, spacing: 8) {
                                Image(systemName: "square")
                                    .foregroundColor(.orange)
                                VStack(alignment: .leading, spacing: 2) {
                                    Text(item.task)
                                        .font(.body)
                                    if let deadline = item.deadline, !deadline.isEmpty {
                                        Text("期限: \(deadline)")
                                            .font(.caption)
                                            .foregroundColor(.secondary)
                                    }
                                }
                            }
                        }
                    }
                }
            }

            // 全文セクション
            if !result.fullTranscript.isEmpty {
                sectionView(title: "全文", icon: "text.alignleft") {
                    VStack(alignment: .leading, spacing: 8) {
                        if showFullTranscript {
                            Text(result.fullTranscript)
                                .font(.body)
                        }

                        Button {
                            withAnimation {
                                showFullTranscript.toggle()
                            }
                        } label: {
                            HStack {
                                Text(showFullTranscript ? "折りたたむ" : "全文を表示")
                                Image(systemName: showFullTranscript ? "chevron.up" : "chevron.down")
                            }
                            .font(.subheadline)
                            .foregroundColor(.blue)
                        }
                    }
                }
            }
        }
    }

    private func fallbackTranscriptView(text: String) -> some View {
        sectionView(title: "文字起こし結果", icon: "text.alignleft") {
            Text(text)
                .font(.body)
        }
    }

    // MARK: - Failed View

    private var failedView: some View {
        VStack(spacing: 16) {
            Image(systemName: "exclamationmark.triangle")
                .font(.system(size: 48))
                .foregroundColor(.red)

            Text("文字起こしに失敗しました")
                .font(.headline)

            if let error = recording.errorMessage {
                Text(error)
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                    .multilineTextAlignment(.center)
            }

            Button {
                startTranscription()
            } label: {
                HStack {
                    if isTranscribing {
                        ProgressView()
                            .progressViewStyle(CircularProgressViewStyle(tint: .white))
                            .scaleEffect(0.8)
                    } else {
                        Image(systemName: "arrow.clockwise")
                    }
                    Text(isTranscribing ? "処理中..." : "再試行")
                }
                .frame(maxWidth: .infinity)
                .padding()
                .background(isTranscribing ? Color.gray : Color.blue)
                .foregroundColor(.white)
                .cornerRadius(10)
            }
            .disabled(isTranscribing)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 40)
    }

    // MARK: - Helper Views

    private func sectionView<Content: View>(title: String, icon: String, @ViewBuilder content: () -> Content) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: icon)
                    .foregroundColor(.blue)
                Text(title)
                    .font(.headline)
            }

            content()
        }
        .padding()
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color(.systemGray6))
        .cornerRadius(12)
    }

    // MARK: - Actions

    private func startTranscription() {
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
    NavigationStack {
        RecordingDetailView(
            recording: Recording(
                audioFileName: "test.m4a",
                duration: 120,
                fileSize: 1024000
            ),
            audioManager: AudioManager(),
            storageManager: StorageManager.shared
        )
    }
    .modelContainer(for: Recording.self, inMemory: true)
}
