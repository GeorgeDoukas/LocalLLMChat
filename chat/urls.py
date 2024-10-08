from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.index, name='index'),
    path('toggle_listening/', views.toggle_listening, name='toggle_listening'),
    path('toggle_call_session/', views.toggle_call_session, name='toggle_call_session'),
    path('get_chat/', views.get_chat, name='get_chat'),
    path('get_speech_audio/', views.get_speech_audio, name='get_speech_audio'),
]
