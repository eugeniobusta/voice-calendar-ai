"""
transcriber_cloud.py — Transcribes audio via Groq's Whisper API.

WHY THIS EXISTS (vs src/transcriber.py):
  transcriber.py    → downloads and runs Whisper locally on your Mac (CLI use)
  transcriber_cloud → sends audio to Groq's servers, gets text back (web use)

  The cloud version is needed because the web app runs on Render's servers,
  which don't have the RAM or storage to run Whisper locally.

GOOD NEWS: You already have a Groq account and API key.
  Groq runs Whisper on their hardware and exposes it as a free API endpoint.
  Same quality as local Whisper, usually faster, and it uses the same key.

FREE LIMITS (Groq Whisper, as of 2025):
  - Model: whisper-large-v3-turbo
  - 7,200 audio seconds (~2 hours) per day
  - Max file size: 25 MB per request
  - For a personal calendar tool, this is essentially unlimited

HOW THE FILE UPLOAD WORKS:
  We receive the audio as a Flask FileStorage object (from request.files).
  We read its raw bytes, then send (filename, bytes) to Groq's API.
  The filename tells Groq what format to expect (e.g., .m4a vs .webm).
"""
from groq import Groq


class CloudTranscriber:
    def __init__(self, api_key: str):
        self.client = Groq(api_key=api_key)

    def transcribe(self, audio_file) -> str:
        """
        Transcribes a Flask FileStorage audio file to text.

        Parameters:
            audio_file: werkzeug.FileStorage — the uploaded file from request.files["audio"]

        Returns:
            Transcript as a plain string.

        Raises:
            Exception: if Groq returns an error (bad format, file too large, etc.)
        """
        audio_bytes = audio_file.read()
        filename = audio_file.filename or "recording.m4a"

        # Groq's API accepts a (filename, bytes) tuple, just like Python's requests library.
        # The filename extension tells the API what codec to use for decoding.
        transcription = self.client.audio.transcriptions.create(
            file=(filename, audio_bytes),
            model="whisper-large-v3-turbo",
            response_format="text",  # returns a plain string instead of a JSON object
        )

        # response_format="text" returns a plain string directly on newer SDK versions
        if isinstance(transcription, str):
            return transcription.strip()
        return transcription.text.strip()

    def transcribe_bytes(self, audio_bytes: bytes, filename: str) -> str:
        """
        Transcribes raw audio bytes — used by the Telegram bot.

        Same as transcribe() but accepts bytes + a filename directly,
        instead of a Flask FileStorage object.
        The filename extension tells Groq the audio format (.ogg, .mp3, etc.)
        """
        transcription = self.client.audio.transcriptions.create(
            file=(filename, audio_bytes),
            model="whisper-large-v3-turbo",
            response_format="text",
        )
        if isinstance(transcription, str):
            return transcription.strip()
        return transcription.text.strip()
