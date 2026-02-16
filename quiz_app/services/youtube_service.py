import os
import uuid
import logging

from django.conf import settings
from yt_dlp import YoutubeDL

logger = logging.getLogger(__name__)


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
    media_dir = os.path.join(settings.MEDIA_ROOT, 'audio')
    os.makedirs(media_dir, exist_ok=True)

    unique_filename = str(uuid.uuid4())
    output_path = os.path.join(media_dir, unique_filename)

    ydl_opts = {
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

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            title = info.get('title', 'Untitled Video')

        audio_path = output_path + '.mp3'

        if not os.path.exists(audio_path):
            raise ValueError('Audio file was not created after download.')

        logger.info(f'Audio downloaded successfully: {audio_path}')
        return {
            'audio_path': audio_path,
            'title': title,
        }

    except Exception as e:
        logger.error(f'Failed to download audio from {video_url}: {e}')
        raise ValueError(f'Could not download audio from the provided URL: {e}')
