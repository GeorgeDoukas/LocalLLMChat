from django.urls import path

from . import views

app_name = "chat"

urlpatterns = [
    path("", views.index, name="index"),
    path("run_main_flow/", views.run_main_flow_view, name="run_main_flow"),
    path("toggle_call_session/", views.toggle_call_session_view, name="toggle_call_session"),
    path("refresh/", views.refresh, name="refresh"),
    path("get_speech_audio/", views.get_speech_audio_view, name="get_speech_audio"),
    path("get_greetings_audio/", views.get_greetings_audio_view, name="get_greetings_audio"),
]
