import os
import uuid
from django.conf import settings
from yt_dlp import YoutubeDL


def _prepare_output_path():
    """
    Creates the media/audio directory if needed and returns a unique output file path.
    """
    media_dir = os.path.join(settings.MEDIA_ROOT, 'audio')
    os.makedirs(media_dir, exist_ok=True)
    unique_filename = str(uuid.uuid4())
    return os.path.join(media_dir, unique_filename)

def _build_ydl_opts(output_path):
    """
    Builds the yt-dlp options dictionary for extracting audio as MP3.
    """
    return {
        'format': 'bestaudio/best',
        'outtmpl': output_path + '.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
        'no_warnings': True,
    }

def _extract_audio(video_url, ydl_opts):
    """
    Downloads the video audio using yt-dlp and returns the video title.
    """
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=True)
        return info.get('title', 'Untitled Video')

def _verify_audio_file(audio_path):
    """
    Raises ValueError if the expected audio file was not created.
    """
    if not os.path.exists(audio_path):
        raise ValueError('Audio file was not created after download.')

def download_audio(video_url):
    """
    Downloads the audio track of a YouTube video using yt-dlp.

    Args:
        video_url (str): The URL of the YouTube video.

    Returns:
        dict: A dictionary containing:
            - 'audio_path' (str): The absolute path to the downloaded audio file.
            - 'title' (str): The title of the YouTube video.

    Raises:
        ValueError: If the URL is invalid or the video cannot be downloaded.
    """
    try:
        output_path = _prepare_output_path()
        ydl_opts = _build_ydl_opts(output_path)
        title = _extract_audio(video_url, ydl_opts)
        audio_path = output_path + '.mp3'
        _verify_audio_file(audio_path)
        return {'audio_path': audio_path, 'title': title}
    except Exception as e:
        raise ValueError(f'Could not download audio from the provided URL: {e}')
