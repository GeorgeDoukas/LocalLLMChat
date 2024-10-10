import logging
import threading
import speech_recognition as sr

logging.basicConfig(level=logging.INFO)

class VoiceRecognitionService:
    """Service for handling voice recognition functionalities."""

    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.is_processing = False
        self.stop_listening_event = threading.Event()

    def transcribe_audio(self, audio):
        """Transcribes audio from the user."""
        return self.recognizer.recognize_google(audio, language="el-GR")

    def listen_for_audio(self):
        """Continuously listens for user audio and processes it."""
        with sr.Microphone() as source:
            self.recognizer.adjust_for_ambient_noise(source)
            phrase_time_limit = 10
            timeout = 10

            while not self.stop_listening_event.is_set() and not self.is_processing:
                try:
                    logging.info("Listening for speech...")
                    audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)

                    return audio

                except sr.WaitTimeoutError:
                    logging.warning("Listening timed out waiting for phrase.")
                except sr.UnknownValueError:
                    logging.warning("Could not understand the audio, skipping this segment.")
                except Exception as e:
                    logging.error(f"Error while listening: {e}")

    def toggle_listening(self):
        """Toggles the listening state."""
        if not self.stop_listening_event.is_set():
            logging.info("Started listening.")
            self.stop_listening_event.clear()
            return True
        else:
            logging.info("Stopped listening.")
            self.stop_listening_event.set()
            return False
