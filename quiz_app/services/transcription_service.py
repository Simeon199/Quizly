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

def _validate_audio_path(audio_path):
    """
    Raises FileNotFoundError if the given audio file does not exist.
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f'Audio file not found: {audio_path}')

def _run_transcription(audio_path):
    """
    Runs the Whisper model on the audio file and returns the transcribed text.
    """
    model = _get_model()
    result = model.transcribe(audio_path)
    transcript = result.get('text', '').strip()
    if not transcript:
        raise ValueError('Transcription returned empty text.')
    return transcript

def _cleanup_audio_file(audio_path):
    """
    Deletes the temporary audio file if it exists.
    """
    if os.path.exists(audio_path):
        os.remove(audio_path)

def transcribe_audio(audio_path):
    """
    Transcribes an audio file to text using OpenAI Whisper.

    Args:
        audio_path (str): The absolute path to the audio file.

    Returns:
        str: The transcribed text.

    Raises:
        ValueError: If transcription fails.
        FileNotFoundError: If the audio file is not found.
    """
    _validate_audio_path(audio_path)
    try:
        return _run_transcription(audio_path)
    except Exception as e:
        raise ValueError(f'Failed to transcribe audio: {e}')
    finally:
        _cleanup_audio_file(audio_path)
