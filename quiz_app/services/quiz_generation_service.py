import json
from django.conf import settings
from google import genai

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

{transcript}"""

def _ensure_api_key():
    if not settings.GEMINI_API_KEY:
        raise ValueError(
            'GEMINI_API_KEY is not configured. Please add it to your .env file.'
        )
    
def _build_prompt(transcript):
    return QUIZ_PROMPT.replace('{transcript}', transcript)

def _call_gemini(prompt):
    client = genai.Client()
    response = client.models.generate_content(
        model='gemini-3-flash-preview',
        contents=prompt
    )
    return response.text.strip()

def _clean_response(raw_text):
    if raw_text.startswith('```'):
        raw_text = raw_text.strip('`')
        if raw_text.startswith('json'):
            raw_text = raw_text[4:]
        raw_text = raw_text.strip()
    return raw_text

def _parse_questions(json_str):
    try:
        questions = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Could not parse quiz from AI response: {e}")
    if not isinstance(questions, list):
        raise ValueError('Gemini response is not a JSON array.')
    return questions

def _trim_and_validate(questions):
    if len(questions) > 10:
        return questions[:10]
    return questions

def _validate_required_keys(question, index):
    required = ('question_title', 'question_options', 'answer')
    if not all(key in question for key in required):
        raise ValueError(
            f"Question {index} is missing required fields. "
            f"Got keys: {list(question.keys())}"
        )

def _validate_options(question, index):
    options = question['question_options']
    if not all(letter in options for letter in ('A', 'B', 'C', 'D')):
        raise ValueError(
            f"Question {index} is missing answer options. "
            f"Got keys: {list(options.keys())}"
        )

def _validate_answer(question, index):
    if question['answer'] not in ('A', 'B', 'C', 'D'):
        raise ValueError(f"Question {index} has invalid answer: {question['answer']}")

def _validate_question_structure(question, index):
    _validate_required_keys(question, index)
    _validate_options(question, index)
    _validate_answer(question, index)
    
def generate_quiz_setup(transcript):
    _ensure_api_key()
    prompt = _build_prompt(transcript)
    raw_text = _call_gemini(prompt)
    cleaned = _clean_response(raw_text)
    questions = _parse_questions(cleaned)
    questions = _trim_and_validate(questions)
    return questions

def generate_quiz_questions(questions):
    for index, question in enumerate(questions):
        _validate_question_structure(question, index + 1)
    return questions
    
MAX_RETRIES = 3

def _fetch_and_validate(prompt):
    raw_text = _call_gemini(prompt)
    cleaned = _clean_response(raw_text)
    questions = _parse_questions(cleaned)
    questions = _trim_and_validate(questions)
    generate_quiz_questions(questions)
    return questions

def generate_quiz(transcript):
    """
    Generate a 10-question quiz from a transcript.
    Retries up to MAX_RETRIES times if validation fails.
    """
    _ensure_api_key()
    prompt = _build_prompt(transcript)

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return _fetch_and_validate(prompt)
        except ValueError as e:
            if attempt == MAX_RETRIES:
                raise ValueError(
                    f"Quiz generation failed after {MAX_RETRIES} attempts. "
                    f"Last error: {e}"
                )