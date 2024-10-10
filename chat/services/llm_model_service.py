import ollama

class LLMModelService:
    """Service for handling interactions with the Ollama model."""

    @staticmethod
    def get_response(transcription):
        """Fetches a response from the Ollama model."""
        ollama_response = ollama.chat(
            model="llama3.2:1b",
            messages=[{"role": "user", "content": transcription}],
        )
        return ollama_response["message"]["content"]
