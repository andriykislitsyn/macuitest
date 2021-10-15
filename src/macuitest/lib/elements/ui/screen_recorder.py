import time

import AVFoundation
import Foundation
from Quartz import CGMainDisplayID


class ScreenRecorder:
    def __init__(self):
        self.session = AVFoundation.AVCaptureSession.new()
        self.session.setSessionPreset_(AVFoundation.AVCaptureSessionPresetHigh)
        self.screen_input = AVFoundation.AVCaptureScreenInput.new().initWithDisplayID_(
            CGMainDisplayID()
        )
        self.screen_input.setCapturesMouseClicks_(True)
        self.screen_input.setCapturesCursor_(True)

        if self.session.canAddInput_:
            self.session.addInput_(self.screen_input)

        self.movie_file_output = AVFoundation.AVCaptureMovieFileOutput.new()
        if self.session.canAddOutput_:
            self.session.addOutput_(self.movie_file_output)

    def start_recording(self, destination: str):
        self.session.startRunning()
        destination = Foundation.NSURL.fileURLWithPath_(destination)
        self.movie_file_output.startRecordingToOutputFileURL_recordingDelegate_(destination, self)
        time.sleep(1.5)

    def stop_recording(self):
        time.sleep(0.5)
        self.movie_file_output.stopRecording()
        time.sleep(2)  # For macOS to catch up.
