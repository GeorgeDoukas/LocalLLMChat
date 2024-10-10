from gtts import gTTS
import os

BOT_AUDIO_FILE_PATH = "chat/media/chat/generated_response.mp3"  # Path for bot audio

class TextToSpeechService:
    """Service for handling text-to-speech functionalities."""

    @staticmethod
    def generate_speech(text):
        """Generates speech from text and saves it to an audio file."""
        tts = gTTS(text=text, lang="el")
        tts.save(BOT_AUDIO_FILE_PATH)
