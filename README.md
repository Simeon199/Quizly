# Quizly

A REST API that automatically generates multiple-choice quizzes from YouTube videos using Google Gemini AI. Users provide a video URL, and Quizly downloads the audio, transcribes it, and produces a 10-question quiz — all in a single API call.

## Features

- AI-powered quiz generation from any YouTube video
- 10 multiple-choice questions per quiz, each with 4 answer options
- Cookie-based JWT authentication (HTTP-only, CSRF-safe)
- Full CRUD on quizzes (retrieve, update title/description, delete)
- Automatic retry logic if the AI response fails validation

## Tech Stack

| Layer          | Technology                          |
|----------------|-------------------------------------|
| Framework      | Django 6 · Django REST Framework    |
| Authentication | SimpleJWT (HTTP-only cookie tokens) |
| AI             | Google Gemini API                   |
| Database       | SQLite                              |
| Testing        | pytest · pytest-django              |

## Project Structure

```
Quizly/
├── core/               # Django project settings & root URLs
├── auth_app/           # Registration, login, logout, token refresh
│   └── api/
├── quiz_app/           # Quiz & question models, views, serializers
│   ├── api/
│   ├── services/
│   │   ├── youtube_service.py        # Audio download
│   │   ├── transcription_service.py  # Speech-to-text
│   │   └── quiz_generation_service.py# Gemini prompt & validation
│   └── tests/
└── manage.py
```

## Getting Started

### Prerequisites

- Python 3.11+
- A [Google Gemini API key](https://aistudio.google.com/)

### Installation

```bash
git clone https://github.com/Simeon199/Quizly.git
cd Quizly
python -m venv env
env\Scripts\activate  # For Windows:
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### Database Setup

```bash
python manage.py migrate
```

### Run the Development Server

```bash
python manage.py runserver
```

The API is available at `http://127.0.0.1:8000`.

## Quiz Generation Pipeline

```
YouTube URL
    │
    ▼
Download audio (youtube_service)
    │
    ▼
Transcribe audio (transcription_service)
    │
    ▼
Send transcript to Gemini (quiz_generation_service)
    │
    ▼
Validate & retry (up to 3 attempts)
    │
    ▼
Save Quiz + 10 Questions to database
```

## Running Tests

```bash
pytest
```

```bash
pytest quiz_app/tests/ -v      # verbose output
pytest auth_app/tests/ -v
```

## Token Configuration

| Token         | Lifetime   |
|---------------|------------|
| Access token  | 120 minutes|
| Refresh token | 3 days     |

Tokens are transmitted exclusively via HTTP-only cookies and are never exposed in the response body.
