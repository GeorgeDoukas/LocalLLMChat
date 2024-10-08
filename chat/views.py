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

from .models import CallSession, Message

# Global variables
is_listening = False
is_processing = False
stop_listening_event = threading.Event()
current_session = None
AUDIO_FILE_PATH = "audio/generated_response.mp3"

# Initialize TTS engine for Greek
tts_engine = pyttsx3.init()
tts_engine.setProperty('rate', 150)

# Load Whisper model for transcription
whisper_model = whisper.load_model("base")

def generate_speech(text):
    voices = tts_engine.getProperty('voices')
    for voice in voices:
        if 'greek' in voice.languages:
            tts_engine.setProperty('voice', voice.id)
            break
    tts_engine.save_to_file(text, AUDIO_FILE_PATH)
    tts_engine.runAndWait()

# Function to handle transcription and response generation
def transcribe_and_generate(audio_path):
    global is_processing
    is_processing = True  # Set processing flag to True when starting

    try:
        transcription = whisper_model.transcribe(audio_path, language="el")["text"]
        print(f"Transcription: {transcription}")

        ollama_response = ollama.chat(
            model="llama3.2:1b",
            messages=[{"role": "user", "content": transcription}]
        )
        response_text = ollama_response["message"]["content"]
        print(f"Bot Response: {response_text}")

        generate_speech(response_text)

        # Store transcription and response in the database
        Message.objects.create(
            session=current_session,
            user_input=transcription if transcription else "Transcription failed",
            bot_response=response_text if response_text else "Response generation failed",
            timestamp=timezone.now()
        )

        is_processing = False  # Reset processing flag after processing is done
        return transcription, response_text
    except Exception as e:
        is_processing = False  # Ensure the flag is reset even if there's an error
        print(f"Error during transcription or response generation: {e}")
        return "", ""

def listen_for_audio():
    global is_listening, is_processing, current_session
    recognizer = sr.Recognizer()

    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)

        phrase_time_limit = 10
        timeout = 10

        while not stop_listening_event.is_set() and not is_processing:
            try:
                # print("Listening for speech...")
                # audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)

                audio_path = "audio/audio_request.wav"
                # with open(audio_path, "wb") as f:
                #     f.write(audio.get_wav_data())

                # Process audio only if not currently processing
                if not is_processing:
                    transcription, response = transcribe_and_generate(audio_path)

            except sr.WaitTimeoutError:
                print("Listening timed out waiting for phrase.")
            except sr.UnknownValueError:
                print("Could not understand the audio, skipping this segment.")
            except Exception as e:
                print(f"Error while listening: {e}")

    # print("Stopped listening.")

def toggle_listening(request):
    global is_listening, current_session

    if not is_listening:
        print("Started listening.")
        is_listening = True
        stop_listening_event.clear()
        # current_session = CallSession.objects.create(sentiment="")
        listening_thread = threading.Thread(target=listen_for_audio)
        listening_thread.start()
        return JsonResponse({"status": "Listening...", "is_processing": is_processing})

    else:
        print("Stopped listening.")
        is_listening = False
        stop_listening_event.set()
        return JsonResponse({"status": "Stopped listening.", "is_processing": is_processing})

def toggle_call_session(request):
    global current_session

    if current_session is None:
        # Start a new session
        current_session = CallSession.objects.create(sentiment="")
        return JsonResponse({"status": "Call session started.","current_session_id":current_session.id})
    else:
        # End the current session
        # current_session.delete()
        current_session = None
        return JsonResponse({"status": "Call session ended."})

def get_speech_audio(request):
    if os.path.exists(AUDIO_FILE_PATH):
        return FileResponse(open(AUDIO_FILE_PATH, 'rb'), content_type='audio/mp3')
    return JsonResponse({"error": "No audio available."})

# View to render the index page
def index(request):
    return render(request, 'chat/index.html')

# View to get the chat history for the current session
def get_chat(request):
    global current_session, is_processing, is_listening

    if current_session:
        messages = current_session.messages.all()  # Retrieve messages
        chat_data = [
            {
                "user_input": message.user_input,
                "bot_response": message.bot_response,
                "timestamp": message.timestamp,
            }
            for message in messages
        ]
        resp = {"chat_data":chat_data,
                "is_processing":is_processing,
                "is_listening":is_listening,
                "current_session_id":current_session.id
                }
        return JsonResponse(resp, safe=False)
    
    return JsonResponse([], safe=False)
