from django.db import models

class CallSession(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    sentiment = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"Session {self.id} - {self.created_at}"

    # This will give you the list of dialogs belonging to a session
    def get_dialogs(self):
        return self.dialogs.all()

class Dialog(models.Model):  # Renamed Message to Dialog
    session = models.ForeignKey(CallSession, on_delete=models.CASCADE, related_name='dialogs')
    user_input = models.TextField(blank=True, null=True)
    bot_response = models.TextField(blank=True, null=True)
    user_audio = models.FileField(upload_to='user_audio/', blank=True, null=True)  # Store user's audio clip
    bot_audio = models.FileField(upload_to='bot_audio/', blank=True, null=True)  # Store bot's audio response
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Dialog at {self.timestamp} - Session {self.session.id} user: {self.user_input} bot: {self.bot_response}"
