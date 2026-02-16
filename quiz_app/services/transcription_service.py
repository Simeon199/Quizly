import os
import logging

import whisper

logger = logging.getLogger(__name__)

# Load the Whisper model once at module level to avoid reloading on every request.
# Available models: 'tiny', 'base', 'small', 'medium', 'large'
# 'base' offers a good balance between speed and accuracy.
_model = None


def _get_model():
    """Lazy-load the Whisper model to avoid loading it at import time."""
    global _model
    if _model is None:
        logger.info('Loading Whisper model (base)...')
        _model = whisper.load_model('base')
        logger.info('Whisper model loaded successfully.')
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
        logger.info(f'Starting transcription of: {audio_path}')
        result = model.transcribe(audio_path)
        transcript = result.get('text', '').strip()

        if not transcript:
            raise ValueError('Transcription returned empty text.')

        logger.info(f'Transcription completed. Length: {len(transcript)} characters.')
        return transcript

    except Exception as e:
        logger.error(f'Transcription failed for {audio_path}: {e}')
        raise ValueError(f'Failed to transcribe audio: {e}')

    finally:
        # Clean up the audio file after transcription
        if os.path.exists(audio_path):
            os.remove(audio_path)
            logger.info(f'Temporary audio file deleted: {audio_path}')
