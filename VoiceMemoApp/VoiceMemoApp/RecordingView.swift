import SwiftUI

struct RecordingView: View {
    @Environment(\.dismiss) private var dismiss
    @ObservedObject var audioManager: AudioManager
    @ObservedObject var storageManager: StorageManager

    @State private var recordedFileName: String?
    @State private var hasRecorded = false
    @State private var animationAmount: CGFloat = 1.0
    @State private var permissionDenied = false

    var body: some View {
        NavigationStack {
            VStack(spacing: 40) {
                Spacer()

                if audioManager.isRecording {
                    Text("録音中...")
                        .font(.title2)
                        .foregroundColor(.red)
                } else if hasRecorded {
                    Text("録音完了")
                        .font(.title2)
                        .foregroundColor(.green)
                } else {
                    Text("タップして録音開始")
                        .font(.title2)
                        .foregroundColor(.secondary)
                }

                Button {
                    if audioManager.isRecording {
                        audioManager.stopRecording()
                        hasRecorded = true
                    } else if !hasRecorded {
                        audioManager.requestMicrophonePermission { granted in
                            if granted {
                                recordedFileName = audioManager.startRecording()
                            } else {
                                permissionDenied = true
                            }
                        }
                    }
                } label: {
                    ZStack {
                        Circle()
                            .fill(audioManager.isRecording ? Color.red : Color.red.opacity(0.8))
                            .frame(width: 100, height: 100)

                        if audioManager.isRecording {
                            Circle()
                                .stroke(Color.red.opacity(0.5), lineWidth: 4)
                                .frame(width: 100, height: 100)
                                .scaleEffect(animationAmount)
                                .opacity(2 - animationAmount)
                                .animation(
                                    .easeInOut(duration: 1)
                                    .repeatForever(autoreverses: false),
                                    value: animationAmount
                                )
                        }

                        Image(systemName: audioManager.isRecording ? "stop.fill" : "mic.fill")
                            .font(.system(size: 40))
                            .foregroundColor(.white)
                    }
                }
                .disabled(hasRecorded)
                .onAppear {
                    animationAmount = 2.0
                }

                Spacer()

                if hasRecorded {
                    HStack(spacing: 40) {
                        Button {
                            if let fileName = recordedFileName {
                                let url = storageManager.getFileURL(fileName: fileName)
                                try? FileManager.default.removeItem(at: url)
                            }
                            dismiss()
                        } label: {
                            Text("キャンセル")
                                .font(.headline)
                                .foregroundColor(.white)
                                .frame(width: 120, height: 50)
                                .background(Color.gray)
                                .cornerRadius(10)
                        }

                        Button {
                            if let fileName = recordedFileName {
                                let memo = VoiceMemo(fileName: fileName)
                                storageManager.add(memo: memo)
                            }
                            dismiss()
                        } label: {
                            Text("保存")
                                .font(.headline)
                                .foregroundColor(.white)
                                .frame(width: 120, height: 50)
                                .background(Color.blue)
                                .cornerRadius(10)
                        }
                    }
                    .padding(.bottom, 40)
                }
            }
            .navigationTitle("録音")
            .navigationBarTitleDisplayMode(.inline)
            .alert("マイクへのアクセスが必要です", isPresented: $permissionDenied) {
                Button("設定を開く") {
                    if let url = URL(string: UIApplication.openSettingsURLString) {
                        UIApplication.shared.open(url)
                    }
                }
                Button("キャンセル", role: .cancel) {}
            } message: {
                Text("録音するには設定からマイクへのアクセスを許可してください。")
            }
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("閉じる") {
                        if audioManager.isRecording {
                            audioManager.stopRecording()
                        }
                        if let fileName = recordedFileName, !hasRecorded {
                            let url = storageManager.getFileURL(fileName: fileName)
                            try? FileManager.default.removeItem(at: url)
                        } else if let fileName = recordedFileName, hasRecorded {
                            let url = storageManager.getFileURL(fileName: fileName)
                            try? FileManager.default.removeItem(at: url)
                        }
                        dismiss()
                    }
                }
            }
        }
    }
}

#Preview {
    RecordingView(
        audioManager: AudioManager(),
        storageManager: StorageManager()
    )
}
