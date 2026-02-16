import os
import whisper

_model = None

def _get_model():
    """
    Lazy-load the Whisper model to avoid loading it at import time.
    """
    global _model
    if _model is None:
        _model = whisper.load_model('base')
    return _model

def transcribe_audio(audio_path):
    """
    Transcribes an audio file to text using OpenAI Whisper.

    Args:
        audio_path (str): The absolute path to the audio file.

    Returns:
        str: The transcribed text.

    Raises:
        ValueError: If the audio file does not exist or transcription fails.
        FileNotFoundError: If the audio file is not found.
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f'Audio file not found: {audio_path}')

    try:
        model = _get_model()
        result = model.transcribe(audio_path)
        transcript = result.get('text', '').strip()

        if not transcript:
            raise ValueError('Transcription returned empty text.')

        return transcript

    except Exception as e:
        raise ValueError(f'Failed to transcribe audio: {e}')

    finally:
        # Clean up the audio file after transcription
        if os.path.exists(audio_path):
            os.remove(audio_path)