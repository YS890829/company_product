import Foundation
import Security

final class KeychainService: Sendable {
    static let shared = KeychainService()

    private let service = "com.example.VoiceMemoApp"
    private let account = "gemini_api_key"

    private init() {}

    func saveAPIKey(_ apiKey: String) throws {
        guard let data = apiKey.data(using: .utf8) else {
            throw KeychainError.encodingFailed
        }

        deleteAPIKey()

        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: account,
            kSecValueData as String: data,
            kSecAttrAccessible as String: kSecAttrAccessibleWhenUnlockedThisDeviceOnly
        ]

        let status = SecItemAdd(query as CFDictionary, nil)

        guard status == errSecSuccess else {
            throw KeychainError.saveFailed(status)
        }
    }

    func getAPIKey() -> String? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: account,
            kSecReturnData as String: true,
            kSecMatchLimit as String: kSecMatchLimitOne
        ]

        var result: AnyObject?
        let status = SecItemCopyMatching(query as CFDictionary, &result)

        guard status == errSecSuccess,
              let data = result as? Data,
              let apiKey = String(data: data, encoding: .utf8) else {
            return nil
        }

        return apiKey
    }

    func deleteAPIKey() {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: account
        ]

        SecItemDelete(query as CFDictionary)
    }

    func hasAPIKey() -> Bool {
        getAPIKey() != nil
    }
}

enum KeychainError: Error, LocalizedError {
    case encodingFailed
    case saveFailed(OSStatus)

    var errorDescription: String? {
        switch self {
        case .encodingFailed:
            return "APIキーのエンコードに失敗しました"
        case .saveFailed(let status):
            return "Keychainへの保存に失敗しました (status: \(status))"
        }
    }
}
