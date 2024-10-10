import os
import logging
from django.http import JsonResponse, FileResponse
from django.shortcuts import render
from rest_framework.decorators import api_view
from .models import CallSession
from .controller import Controller

# Configure logging
logging.basicConfig(level=logging.INFO)

# Create an instance of Controller
controller = Controller()

BOT_AUDIO_FILE_PATH = "chat/media/chat/generated_response.mp3"  # Path for bot audio
USER_AUDIO_FILE_PATH = "chat/media/chat/audio_request.wav"  # Path for user audio
GREETINGS_AUDIO_FILE_PATH = "chat/media/chat/greetings.mp3"  # Path for greetings audio


@api_view(["POST"])
def run_main_flow_view(request):
    """View to toggle listening state."""
    controller.main_flow()
    return JsonResponse(
        {
            "status": "Listening...",
            "is_listening": controller.is_listening,
        }
    )


@api_view(["POST"])
def toggle_call_session_view(request):
    """View to start or end a call session."""
    response = controller.toggle_call_session()
    return JsonResponse(response)


@api_view(["GET"])
def get_speech_audio_view(request):
    """Serves the generated bot speech audio."""
    return controller.get_audio_response(BOT_AUDIO_FILE_PATH)


@api_view(["GET"])
def get_greetings_audio_view(request):
    """Serves the generated greetings audio."""
    return controller.get_audio_response(GREETINGS_AUDIO_FILE_PATH)


@api_view(["GET"])
def index(request):
    """View to render the index page"""
    return render(request, "chat/index.html")


@api_view(["GET"])
def refresh(request):
    """Fetches chat history for the current session."""
    
    exchanges = controller.current_session.exchanges.all()  # Retrieve dialogs
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
        "is_processing": controller.is_processing,
        "is_listening": controller.is_listening,
        "current_session_id": controller.current_session.id,
    }
    return JsonResponse(resp, safe=False)


def process_audio_view(request):
    """View to process audio input."""
    if request.method == "POST":
        audio_data = request.FILES.get("audio_file")  # Assuming audio is sent as file
        transcription = controller.process_audio(audio_data)
        response_text = controller.process_transcription(transcription)
        controller.process_agent_response(transcription, response_text)
        return JsonResponse({"transcription": transcription, "response": response_text})

    return JsonResponse({"error": "Invalid request."}, status=400)
