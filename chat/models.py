from django.db import models

class CallSession(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    sentiment = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"Session {self.id} - {self.created_at}"

    # This will give you the list of dialogs belonging to a session
    def get_dialogs(self):
        return self.exchanges.all()

class Exchange(models.Model):  # Renamed Message to Dialog
    SPEAKER_CHOICES = [
        ("U", "User"),
        ("A", "Agent"),
    ]
    session = models.ForeignKey(CallSession, on_delete=models.CASCADE, related_name='exchanges')
    speaker = models.CharField(max_length=1, choices=SPEAKER_CHOICES, default="U")
    input = models.TextField(blank=True, null=True)
    response = models.TextField(blank=True, null=True)
    audio = models.FileField(upload_to='audio/user/', blank=True, null=True)  # Store user's audio clip
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Exchange from {self.get_speaker()} at {self.timestamp} - Session - {self.session.id} {self.input} : {self.response}"

    def get_speaker(self):
        for choice in self.SPEAKER_CHOICES:
            if choice[0] == self.speaker:
                return choice[1]
        return "Unknown"