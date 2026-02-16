"""
Sanity Check: Tests the full quiz generation pipeline.
Usage: python sanity_check.py <youtube_url>
"""
import sys
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from quiz_app.services.youtube_service import download_audio
from quiz_app.services.transcription_service import transcribe_audio
from quiz_app.services.quiz_generation_service import generate_quiz


def run(video_url):
    print(f'\n[1/3] Downloading audio from: {video_url}')
    result = download_audio(video_url)
    print(f'  Title: {result["title"]}')
    print(f'  Audio: {result["audio_path"]}')

    print('\n[2/3] Transcribing audio (this may take a moment)...')
    transcript = transcribe_audio(result['audio_path'])
    print(f'  Transcript length: {len(transcript)} characters')
    print(f'  Preview: {transcript[:200]}...')

    print('\n[3/3] Generating quiz via Gemini...')
    questions = generate_quiz(transcript)

    print(f'\n  Quiz generated with {len(questions)} questions:\n')
    for i, q in enumerate(questions, 1):
        print(f'  Frage {i}: {q["question_title"]}')
        for letter, option in q['question_options'].items():
            print(f'    {letter}: {option}')
        print(f'    Richtige Antwort: {q["answer"]}\n')

    print('Pipeline completed successfully!')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: python sanity_check.py <youtube_url>')
        sys.exit(1)
    run(sys.argv[1])
