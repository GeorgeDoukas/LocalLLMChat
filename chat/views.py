import os
import threading
from io import BytesIO

import ollama
import pyttsx3
import speech_recognition as sr
import whisper
from django.http import FileResponse, JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from gtts import gTTS
from ollama import Client

from .models import CallSession, Exchange

# Global variables
is_listening = False
is_processing = False
stop_listening_event = threading.Event()
current_session = None
BOT_AUDIO_FILE_PATH = "audio/generated_response.mp3"  # Path for bot audio
USER_AUDIO_FILE_PATH = "audio/audio_request.wav"  # Path for user audio
GREETINGS_AUDIO_FILE_PATH = "audio\greetings.mp3" # Path for greetings audio
recognizer = sr.Recognizer()

# Initialize TTS engine for Greek
# tts_engine = pyttsx3.init()
# tts_engine.setProperty('rate', 150)

# Load Whisper model for transcription
# whisper_model = whisper.load_model("base")

def generate_speech(text):
    """Generates speech from text and saves it to an audio file."""
    # voices = tts_engine.getProperty('voices')
    # for voice in voices:
    #     if 'greek' in voice.languages:
    #         tts_engine.setProperty('voice', voice.id)
    #         break
    # tts_engine.save_to_file(text, BOT_AUDIO_FILE_PATH)
    # tts_engine.runAndWait()
    
    tts = gTTS(text=text, lang='el')
    tts.save("audio\generated_response.mp3")

def transcribe_and_generate(audio):
    """Transcribes audio from the user and generates a bot response."""
    global is_processing, is_listening
    is_listening = False
    is_processing = True  # Set processing flag to True when starting

    try:
        # Transcribe user audio
        # transcription = whisper_model.transcribe(USER_AUDIO_FILE_PATH, language="el")["text"]
        transcription = recognizer.recognize_google(audio, language="el-GR")
        print(f"Transcription: {transcription}")
        
        # Store the Exchange (both text and audio) in the database
        current_exchange = Exchange.objects.create(
            session=current_session,
            speaker="U",
            input="",
            response=transcription if transcription else "Transcription failed",
            audio=USER_AUDIO_FILE_PATH,
            timestamp=timezone.now()
        )
        previous_exchange_id = current_exchange.id - 1
        previous_exchange = Exchange.objects.get(id=previous_exchange_id)
        current_exchange.input = previous_exchange.response

        # Get bot response from the model
        ollama_response = ollama.chat(
            model="llama3.2:1b",
            messages=[{"Assistant": "user", "content": transcription}]
        )
        # client = Client(host='http://localhost:31435')
        # ollama_response = client.chat(
        #     model="llama3.1:70b",
        #     messages=[{"role": "Assistant", "content": transcription}]
        # )
        
        response_text = ollama_response["message"]["content"]
        print(f"Bot Response: {response_text}")

        # Generate bot audio response
        generate_speech(response_text)

        # Store the Exchange (both text and audio) in the database
        Exchange.objects.create(
            session=current_session,
            speaker="A",
            input=transcription if transcription else "Transcription failed",
            response=response_text if response_text else "Response generation failed",
            audio=BOT_AUDIO_FILE_PATH,
            timestamp=timezone.now()
        )

        is_processing = False  # Reset processing flag after processing is done
        return transcription, response_text
    except Exception as e:
        is_processing = False  # Ensure the flag is reset even if there's an error
        print(f"Error during transcription or response generation: {e}")
        return "", ""

def listen_for_audio():
    """Continuously listens for user audio and processes it."""
    global is_listening, is_processing, current_session
    
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)
        phrase_time_limit = 10
        timeout = 10

        while not stop_listening_event.is_set() and not is_processing:
            try:
                # Here, we simulate listening by using a pre-recorded audio file.
                print("Listening for speech...")
                audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
                # transcription = recognizer.recognize_google(audio, language="el-GR")
                # print()
                with open(USER_AUDIO_FILE_PATH, "wb") as f:
                    f.write(audio.get_wav_data())
                # with sr.AudioFile('audio/audio_request.wav') as source:
                #     audio_data = recognizer.record(source)
                #     transcription = recognizer.recognize_google(audio_data, language="el")
                #     print(transcription)
                # Process audio only if not currently processing
                if not is_processing:
                    transcription, response = transcribe_and_generate(audio)
                    
            except sr.WaitTimeoutError:
                print("Listening timed out waiting for phrase.")
            except sr.UnknownValueError:
                print("Could not understand the audio, skipping this segment.")
            except Exception as e:
                print(f"Error while listening: {e}")

def toggle_listening(request):
    """Toggles the listening state for user input."""
    global is_listening, current_session

    if not is_listening:
        print("Started listening.")
        is_listening = True
        stop_listening_event.clear()
        listening_thread = threading.Thread(target=listen_for_audio)
        listening_thread.start()
        return JsonResponse({"status": "Listening...", "is_listening": is_listening})

    else:
        print("Stopped listening.")
        is_listening = False
        stop_listening_event.set()
        return JsonResponse({"status": "Stopped listening.", "is_listening": is_listening})

def toggle_call_session(request):
    """Starts or ends a call session."""
    global current_session, is_listening

    if current_session is None:
        # Start a new session
        current_session = CallSession.objects.create(sentiment="")
        # Store the Exchange (both text and audio) in the database
        Exchange.objects.create(
            session=current_session,
            speaker="A",
            input="Start of Conversation",
            response="Γεία σας πως θα μπορούσα να σας εξυπηρετήσω;",
            audio=GREETINGS_AUDIO_FILE_PATH,
            timestamp=timezone.now()
        )
        return JsonResponse({"status": "Call session started.", "current_session_id": current_session.id})
    else:
        # End the current session
        is_listening = False
        current_session = None
        return JsonResponse({"status": "Call session ended."})

def get_speech_audio(request):
    """Serves the generated bot speech audio."""
    if os.path.exists(BOT_AUDIO_FILE_PATH):
        return FileResponse(open(BOT_AUDIO_FILE_PATH, 'rb'), content_type='audio/mp3')
    return JsonResponse({"error": "No audio available."})

def get_greetings_audio(request):
    """Serves the generated bot speech audio."""
    if os.path.exists(GREETINGS_AUDIO_FILE_PATH):
        return FileResponse(open(GREETINGS_AUDIO_FILE_PATH, 'rb'), content_type='audio/mp3')
    return JsonResponse({"error": "No audio available."})

def index(request):
    """View to render the index page"""
    return render(request, 'chat/index.html')

def get_chat(request):
    """Fetches chat history for the current session."""
    global current_session, is_processing, is_listening
    if current_session:
        exchanges = current_session.exchanges.all()  # Retrieve dialogs
        chat_data = [
            {
                "response": exchange.response,
                "speaker": exchange.speaker,
                "timestamp": exchange.timestamp,
            }
            for exchange in exchanges
        ]
        resp = {
            "chat_data": chat_data,
            "is_processing": is_processing,
            "is_listening": is_listening,
            "current_session_id": current_session.id
        }
        return JsonResponse(resp, safe=False)
    
    return JsonResponse([], safe=False)
