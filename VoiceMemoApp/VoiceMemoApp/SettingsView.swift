import SwiftUI

struct SettingsView: View {
    @Environment(\.dismiss) private var dismiss
    @State private var apiKey: String = ""
    @State private var showSavedMessage = false
    @State private var showErrorMessage = false
    @State private var errorMessage = ""
    @State private var hasExistingKey = false

    var body: some View {
        NavigationStack {
            Form {
                Section {
                    SecureField("APIキーを入力", text: $apiKey)
                        .textContentType(.password)
                        .autocorrectionDisabled()
                        .textInputAutocapitalization(.never)

                    if hasExistingKey && apiKey.isEmpty {
                        HStack {
                            Image(systemName: "checkmark.circle.fill")
                                .foregroundColor(.green)
                            Text("APIキーは設定済みです")
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                    }
                } header: {
                    Text("Gemini API設定")
                } footer: {
                    Text("Google AI StudioでAPIキーを取得してください")
                }

                Section {
                    Button {
                        saveAPIKey()
                    } label: {
                        HStack {
                            Spacer()
                            Text("保存")
                                .fontWeight(.semibold)
                            Spacer()
                        }
                    }
                    .disabled(apiKey.isEmpty)

                    if hasExistingKey {
                        Button(role: .destructive) {
                            deleteAPIKey()
                        } label: {
                            HStack {
                                Spacer()
                                Text("APIキーを削除")
                                Spacer()
                            }
                        }
                    }
                }

                Section {
                    Link(destination: URL(string: "https://aistudio.google.com/app/apikey")!) {
                        HStack {
                            Text("Google AI Studioでキーを取得")
                            Spacer()
                            Image(systemName: "arrow.up.right.square")
                                .foregroundColor(.secondary)
                        }
                    }
                } header: {
                    Text("ヘルプ")
                }
            }
            .navigationTitle("設定")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("閉じる") {
                        dismiss()
                    }
                }
            }
            .onAppear {
                loadExistingKey()
            }
            .alert("保存しました", isPresented: $showSavedMessage) {
                Button("OK") {
                    dismiss()
                }
            } message: {
                Text("APIキーをKeychainに保存しました")
            }
            .alert("エラー", isPresented: $showErrorMessage) {
                Button("OK", role: .cancel) {}
            } message: {
                Text(errorMessage)
            }
        }
    }

    private func loadExistingKey() {
        hasExistingKey = KeychainService.shared.hasAPIKey()
    }

    private func saveAPIKey() {
        do {
            try KeychainService.shared.saveAPIKey(apiKey)
            apiKey = ""
            hasExistingKey = true
            showSavedMessage = true
        } catch {
            errorMessage = error.localizedDescription
            showErrorMessage = true
        }
    }

    private func deleteAPIKey() {
        KeychainService.shared.deleteAPIKey()
        hasExistingKey = false
        apiKey = ""
    }
}

#Preview {
    SettingsView()
}
