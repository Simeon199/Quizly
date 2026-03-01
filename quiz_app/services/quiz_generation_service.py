import json
from django.conf import settings
from google import genai

QUIZ_PROMPT = """
Erstellen anhand der folgenden Transkription eines YouTube-Videos ein Quiz mit genau 10 Multiple-Choice-Fragen.

Jede Frage muss genau 4 Antwortmöglichkeiten mit genau einer richtigen Antwort enthalten.

WICHTIG: Gebe NUR ein gültiges JSON-Array ohne zusätzlichen Text, ohne Markdown und ohne Code-Fences zurück.
Jedes Objekt im Array muss genau diese Schlüssel enthalten:
- „question_title”: Der Fragetext
- „question_options”: Ein Array mit genau 4 Antwortoptionen als Zeichenketten
- „answer”: Der vollständige Text der richtigen Antwort (muss exakt mit einem der Einträge in „question_options” übereinstimmen)

Beispielformat:
[
    {
        „question_title”: „Was ist das Hauptthema der Diskussion?”,
        „question_options”: [
            „Text Option 1”,
            „Text Option 2”,
            „Text Option 3”,
            „Text Option 4”
        ],
        „answer”: „Text Option 1”
    }
]

Hier ist das Transkript:

{transcript}"""

def _ensure_api_key():
    """
    Raises ValueError if the GEMINI_API_KEY is not set in the environment.
    """
    if not settings.GEMINI_API_KEY:
        raise ValueError(
            'GEMINI_API_KEY is not configured. Please add it to your .env file.'
        )
    
def _build_prompt(transcript):
    """
    Inserts the transcript into the prompt template and returns the full prompt.
    """
    return QUIZ_PROMPT.replace('{transcript}', transcript)

def _call_gemini(prompt):
    """
    Sends the prompt to the Gemini API and returns the raw response text.
    """
    client = genai.Client()
    response = client.models.generate_content(
        model='gemini-3-flash-preview',
        contents=prompt
    )
    return response.text.strip()

def _clean_response(raw_text):
    """
    Strips markdown code fences from the response if present.
    """
    if raw_text.startswith('```'):
        raw_text = raw_text.strip('`')
        if raw_text.startswith('json'):
            raw_text = raw_text[4:]
        raw_text = raw_text.strip()
    return raw_text

def _parse_questions(json_str):
    """
    Parses a JSON string into a list of question dictionaries.
    """
    try:
        questions = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Could not parse quiz from AI response: {e}")
    if not isinstance(questions, list):
        raise ValueError('Gemini response is not a JSON array.')
    return questions

def _trim_and_validate(questions):
    """
    Truncates the list to a maximum of 10 questions.
    """
    if len(questions) > 10:
        return questions[:10]
    return questions

def _validate_required_keys(question, index):
    """
    Raises ValueError if the question is missing any required keys.
    """
    required = ('question_title', 'question_options', 'answer')
    if not all(key in question for key in required):
        raise ValueError(
            f"Question {index} is missing required fields. "
            f"Got keys: {list(question.keys())}"
        )

def _validate_options(question, index):
    """
    Raises ValueError if question_options is not a list with exactly 4 items.
    """
    options = question['question_options']
    if not isinstance(options, list) or len(options) != 4:
        raise ValueError(
            f"Question {index} must have exactly 4 answer options as a list. "
            f"Got: {options}"
        )

def _validate_answer(question, index):
    """
    Raises ValueError if the answer is not one of the question_options.
    """
    if question['answer'] not in question['question_options']:
        raise ValueError(
            f"Question {index} has invalid answer: '{question['answer']}'. "
            f"Answer must match one of the question_options."
        )

def _validate_question_structure(question, index):
    """
    Validates that a single question has all required keys, options and a valid answer.
    """
    _validate_required_keys(question, index)
    _validate_options(question, index)
    _validate_answer(question, index)
    
def generate_quiz_setup(transcript):
    """
    Runs the full pipeline: API key check, prompt building, Gemini call, parsing and trimming.
    """
    _ensure_api_key()
    prompt = _build_prompt(transcript)
    raw_text = _call_gemini(prompt)
    cleaned = _clean_response(raw_text)
    questions = _parse_questions(cleaned)
    questions = _trim_and_validate(questions)
    return questions

def generate_quiz_questions(questions):
    """
    Validates the structure of every question in the list.
    """
    for index, question in enumerate(questions):
        _validate_question_structure(question, index + 1)
    return questions
    
MAX_RETRIES = 3

def _fetch_and_validate(prompt):
    """
    Calls Gemini, cleans and parses the response, and validates all questions.
    """
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