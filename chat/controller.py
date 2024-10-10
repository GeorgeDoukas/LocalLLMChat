import os
import logging
from .services.text_to_speech_service import TextToSpeechService
from .services.voice_recognition_service import VoiceRecognitionService
from .services.llm_model_service import LLMModelService
from .models import CallSession, Exchange
from django.utils import timezone
from django.http import JsonResponse, FileResponse

# Configure logging
logging.basicConfig(level=logging.INFO)

BOT_AUDIO_FILE_PATH = "chat/media/chat/generated_response.mp3"  # Path for bot audio
USER_AUDIO_FILE_PATH = "chat/media/chat/audio_request.wav"  # Path for user audio
GREETINGS_AUDIO_FILE_PATH = "chat/media/chat/greetings.mp3"  # Path for greetings audio
SORRY_AUDIO_FILE_PATH = "chat\media\chat\sorry_i_didnt_get_that.mp3"

class Controller:
    """Handles the coordination of audio processing and state management."""

    def __init__(self):
        self.is_listening = False
        self.current_session = None
        self.voice_recognition_service = VoiceRecognitionService()
        self.is_processing = False  # Maintain processing state

    def process_audio(self, audio):
        """Processes audio input and generates a response."""
        self.is_processing = True  # Set processing flag to True when starting

        try:
            # Transcribe user audio
            transcription = self.voice_recognition_service.transcribe_audio(audio)
            logging.info(f"Transcription: {transcription}")

            # Store the user exchange
            current_exchange = Exchange.objects.create(
                session=self.current_session,
                speaker="U",
                input="",
                response=transcription if transcription else "Transcription failed",
                audio=USER_AUDIO_FILE_PATH,
                timestamp=timezone.now(),
            )

            # Get previous exchange to use as context
            previous_exchange_id = current_exchange.id - 1
            previous_exchange = Exchange.objects.get(id=previous_exchange_id)
            current_exchange.input = previous_exchange.response
            current_exchange.save()

            return transcription

        except Exception as e:
            logging.error(f"Error during processing of audio input: {e}")
            return ""
        finally:
            self.is_processing = (
                False  # Ensure the flag is reset after processing is done
            )

    def process_transcription(self, transcription):
        # Get bot response from the Ollama model
        try:
            response_text = LLMModelService.get_response(transcription)
        except Exception as e:
            logging.error(f"Error during processing of transcription: {e}")
            return ""
        logging.info(f"Agent Response: {response_text}")

        return response_text

    def process_agent_response(self, transcription, response):
        # Generate bot audio response
        try:
            TextToSpeechService.generate_speech(response)

            # Store the bot exchange
            Exchange.objects.create(
                session=self.current_session,
                speaker="A",
                input=transcription if transcription else "Transcription failed",
                response=response if response else "Response generation failed",
                audio=BOT_AUDIO_FILE_PATH,
                timestamp=timezone.now(),
            )
        except Exception as e:
            logging.error(f"Error during processing of agent response: {e}")

    def toggle_call_session(self):
        """Starts or ends a call session."""
        if self.current_session is None:
            # Start a new session
            self.current_session = CallSession.objects.create(sentiment="")
            # Store the Exchange (greeting)
            Exchange.objects.create(
                session=self.current_session,
                speaker="A",
                input="Start of Conversation",
                response="Γεία σας πως θα μπορούσα να σας εξυπηρετήσω;",
                audio=GREETINGS_AUDIO_FILE_PATH,
                timestamp=timezone.now(),
            )

            return {
                "status": "Call session started.",
                "current_session_id": self.current_session.id,
            }
        else:
            # End the current session
            self.is_listening = False
            self.current_session = None
            return {"status": "Call session ended."}

    def get_audio_response(self, audio_file_path):
        """Serves the generated bot speech audio."""
        if os.path.exists(audio_file_path):
            return FileResponse(open(audio_file_path, "rb"), content_type="audio/mp3")
        return JsonResponse({"error": "No audio available."})

    def main_flow(self):
        try:
            audio_data = self.voice_recognition_service.listen_for_audio()
            transcription = self.process_audio(audio_data)
            response_text = self.process_transcription(transcription)
            self.process_agent_response(transcription, response_text)
        except Exception as e:
            logging.error(f"Error during main flow: {e}")
