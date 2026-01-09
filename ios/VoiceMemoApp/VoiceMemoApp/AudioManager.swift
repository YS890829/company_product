import AVFoundation
import Foundation

class AudioManager: NSObject, ObservableObject, AVAudioPlayerDelegate {
    @Published var isRecording = false
    @Published var isPlaying = false
    @Published var currentlyPlayingId: UUID?

    private var audioRecorder: AVAudioRecorder?
    private var audioPlayer: AVAudioPlayer?

    func setupAudioSession() {
        do {
            let session = AVAudioSession.sharedInstance()
            try session.setCategory(.playAndRecord, mode: .default, options: [.defaultToSpeaker])
            try session.setActive(true, options: .notifyOthersOnDeactivation)
        } catch {
            print("Failed to setup audio session: \(error)")
        }
    }

    func requestMicrophonePermission(completion: @escaping (Bool) -> Void) {
        AVAudioApplication.requestRecordPermission { granted in
            DispatchQueue.main.async {
                completion(granted)
            }
        }
    }

    func startRecording() -> String? {
        let fileName = "\(UUID().uuidString).m4a"
        let documentsPath = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        let audioURL = documentsPath.appendingPathComponent(fileName)

        let settings: [String: Any] = [
            AVFormatIDKey: Int(kAudioFormatMPEG4AAC),
            AVSampleRateKey: 44100.0,
            AVNumberOfChannelsKey: 1,
            AVEncoderAudioQualityKey: AVAudioQuality.high.rawValue
        ]

        do {
            audioRecorder = try AVAudioRecorder(url: audioURL, settings: settings)
            audioRecorder?.record()
            isRecording = true
            return fileName
        } catch {
            print("Failed to start recording: \(error)")
            return nil
        }
    }

    func stopRecording() {
        audioRecorder?.stop()
        audioRecorder = nil
        isRecording = false
    }

    func play(url: URL, id: UUID) {
        stopPlaying()

        do {
            audioPlayer = try AVAudioPlayer(contentsOf: url)
            audioPlayer?.delegate = self
            audioPlayer?.play()
            isPlaying = true
            currentlyPlayingId = id
        } catch {
            print("Failed to play audio: \(error)")
        }
    }

    func stopPlaying() {
        audioPlayer?.stop()
        audioPlayer = nil
        isPlaying = false
        currentlyPlayingId = nil
    }

    func audioPlayerDidFinishPlaying(_ player: AVAudioPlayer, successfully flag: Bool) {
        isPlaying = false
        currentlyPlayingId = nil
    }
}
