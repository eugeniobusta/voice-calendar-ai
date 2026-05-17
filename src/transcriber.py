"""
transcriber.py — Converts audio files to text using OpenAI's Whisper.

WHAT IS WHISPER?
  Whisper is a speech recognition model released by OpenAI as open-source.
  Unlike the OpenAI API (which charges per minute), this version runs
  ENTIRELY on your computer — no internet needed, no cost, no data sent anywhere.

  Install: pip install openai-whisper
  This is different from the 'openai' package — it's a separate local tool.

MODEL SIZES — trade-off between speed, accuracy, and RAM:
  tiny   ~150MB  — fastest, ~60% accurate, good for quick tests
  base   ~300MB  — good balance, ~80% accurate ← default
  small  ~500MB  — very good, ~90% accurate
  medium ~1.5GB  — excellent, needs ~8GB RAM
  large  ~3GB    — near-human accuracy, needs ~16GB RAM

The model is downloaded once on first use to ~/.cache/whisper/
After that, it loads from disk (takes a few seconds, not minutes).

SUPPORTED AUDIO FORMATS:
  mp3, mp4, m4a, wav, flac, ogg, webm

COMMON USE CASE:
  Record a voice note on iPhone → AirDrop to Mac → run this script.
  Or: set up an Apple Shortcut to trigger this automatically (Phase 3).
"""
from pathlib import Path
import whisper


class Transcriber:
    def __init__(self, model_size: str = "base"):
        """
        Loads the Whisper model into memory.

        This takes 1–5 seconds depending on model size and whether
        the model is already cached. The first run also downloads it.

        Parameters:
            model_size: one of "tiny", "base", "small", "medium", "large"
        """
        print(f"  Loading Whisper '{model_size}' model...")
        # whisper.load_model() downloads the model if not cached,
        # then loads it into RAM. After this, transcription is fast.
        self.model = whisper.load_model(model_size)
        print(f"  Model ready.")

    def transcribe(self, audio_path: str) -> str:
        """
        Converts an audio file to a plain text transcript.

        Parameters:
            audio_path: path to audio file (mp3, m4a, wav, etc.)

        Returns:
            The spoken words as a plain string.

        Raises:
            FileNotFoundError: if the audio file doesn't exist at the given path
        """
        path = Path(audio_path)
        if not path.exists():
            raise FileNotFoundError(
                f"Audio file not found: {audio_path}\n"
                f"Make sure you typed the path correctly."
            )

        print(f"  Transcribing '{path.name}'...")

        # fp16=False forces CPU-mode math.
        # fp16 (16-bit floating point) requires a GPU — most laptops use CPU.
        # Without this flag, you'd get a warning on non-GPU machines.
        result = self.model.transcribe(str(path), fp16=False)

        transcript = result["text"].strip()
        print(f"  Transcript: '{transcript[:60]}{'...' if len(transcript) > 60 else ''}'")
        return transcript
