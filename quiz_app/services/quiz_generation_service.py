import json
import logging

from django.conf import settings
from google import genai

logger = logging.getLogger(__name__)

QUIZ_PROMPT = """
Based on the following transcript from a YouTube video, generate a quiz with exactly 10 multiple-choice questions.

Each question must have exactly 4 answer options (A, B, C, D), with exactly one correct answer.

IMPORTANT: Return ONLY a valid JSON array with no additional text, no markdown, no code fences.
Each object in the array must have exactly these keys:
- "question_title": The question text
- "question_options": An object with keys "A", "B", "C", "D" and their corresponding answer texts
- "answer": The letter of the correct answer ("A", "B", "C", or "D")

Example format:
[
    {
        "question_title": "What is the main topic discussed?",
        "question_options": {
            "A": "Option A text",
            "B": "Option B text",
            "C": "Option C text",
            "D": "Option D text"
        },
        "answer": "A"
    }
]

Here is the transcript:

{transcript}
"""


def generate_quiz(transcript):
    """
    Generates a quiz with 10 multiple-choice questions based on a transcript
    using the Google Gemini API.

    Args:
        transcript (str): The transcribed text from a YouTube video.

    Returns:
        list[dict]: A list of 10 question dictionaries, each containing:
            - 'question_title' (str): The question text.
            - 'question_options' (dict): A dict with keys A, B, C, D.
            - 'answer' (str): The correct answer letter.

    Raises:
        ValueError: If the API key is missing, the API call fails,
                    or the response cannot be parsed.
    """
    if not settings.GEMINI_API_KEY:
        raise ValueError(
            'GEMINI_API_KEY is not configured. '
            'Please add it to your .env file.'
        )

    try:
        client = genai.Client()

        prompt = QUIZ_PROMPT.replace('{transcript}', transcript)

        response = client.models.generate_content(
            model='gemini-3-flash-preview',
            contents=prompt,
        )

        raw_text = response.text.strip()
        logger.info(f'Gemini API response received. Length: {len(raw_text)} characters.')

        # Clean up the response in case it contains markdown code fences
        if raw_text.startswith('```'):
            raw_text = raw_text.strip('`')
            if raw_text.startswith('json'):
                raw_text = raw_text[4:]
            raw_text = raw_text.strip()

        questions = json.loads(raw_text)

        if not isinstance(questions, list):
            raise ValueError('Gemini response is not a JSON array.')

        if len(questions) != 10:
            logger.warning(
                f'Expected 10 questions, got {len(questions)}. '
                f'Truncating or padding may be needed.'
            )
            questions = questions[:10]

        # Validate the structure of each question
        for i, q in enumerate(questions):
            if not all(key in q for key in ('question_title', 'question_options', 'answer')):
                raise ValueError(
                    f'Question {i + 1} is missing required fields. '
                    f'Got keys: {list(q.keys())}'
                )

            options = q['question_options']
            if not all(letter in options for letter in ('A', 'B', 'C', 'D')):
                raise ValueError(
                    f'Question {i + 1} is missing answer options. '
                    f'Got keys: {list(options.keys())}'
                )

            if q['answer'] not in ('A', 'B', 'C', 'D'):
                raise ValueError(
                    f'Question {i + 1} has invalid answer: {q["answer"]}'
                )

        logger.info(f'Quiz generated successfully with {len(questions)} questions.')
        return questions

    except json.JSONDecodeError as e:
        logger.error(f'Failed to parse Gemini response as JSON: {e}')
        raise ValueError(f'Could not parse quiz from AI response: {e}')

    except Exception as e:
        logger.error(f'Quiz generation failed: {e}')
        raise ValueError(f'Failed to generate quiz: {e}')
