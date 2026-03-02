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
git clone <repository-url>
cd Quizly

python -m venv env
source env/bin/activate        # Windows: env\Scripts\activate

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

## API Reference

### Authentication

All quiz endpoints require authentication. Tokens are stored in HTTP-only cookies and are set automatically on login.

| Method | Endpoint              | Description                          | Auth required |
|--------|-----------------------|--------------------------------------|---------------|
| POST   | `/api/register/`      | Register a new user account          | No            |
| POST   | `/api/login/`         | Login and receive JWT cookies        | No            |
| POST   | `/api/logout/`        | Logout and invalidate tokens         | Yes           |
| POST   | `/api/token/refresh/` | Refresh the access token via cookie  | No            |

**Register** — `POST /api/register/`
```json
{
  "username": "alice",
  "email": "alice@example.com",
  "password": "secret123",
  "confirmed_password": "secret123"
}
```

**Login** — `POST /api/login/`
```json
{
  "username": "alice",
  "password": "secret123"
}
```

### Quizzes

| Method | Endpoint              | Description                          |
|--------|-----------------------|--------------------------------------|
| GET    | `/api/quizzes/`       | List all quizzes of the current user |
| POST   | `/api/quizzes/`       | Create a quiz from a YouTube URL     |
| GET    | `/api/quizzes/{id}/`  | Retrieve a specific quiz             |
| PATCH  | `/api/quizzes/{id}/`  | Update quiz title and/or description |
| DELETE | `/api/quizzes/{id}/`  | Delete a quiz                        |

**Create a quiz** — `POST /api/quizzes/`
```json
{
  "url": "https://www.youtube.com/watch?v=example"
}
```

**Quiz response** (GET)
```json
{
  "id": 1,
  "title": "Video Title",
  "description": "",
  "video_url": "https://www.youtube.com/watch?v=example",
  "created_at": "2026-03-01T19:32:01.275353Z",
  "updated_at": "2026-03-01T19:32:01.275372Z",
  "questions": [
    {
      "id": 1,
      "question_title": "What is the main topic of the video?",
      "question_options": [
        "Option A",
        "Option B",
        "Option C",
        "Option D"
      ],
      "answer": "Option A",
      "created_at": "2026-03-01T19:32:01.291121Z",
      "updated_at": "2026-03-01T19:32:01.291302Z"
    }
  ]
}
```

**Update a quiz** — `PATCH /api/quizzes/{id}/`
```json
{
  "title": "New Title",
  "description": "An optional description"
}
```

### Error Responses

| Status | Meaning                                          |
|--------|--------------------------------------------------|
| 400    | Invalid input or quiz generation failure         |
| 401    | Missing or expired authentication token          |
| 403    | Attempting to modify another user's quiz         |
| 404    | Quiz not found                                   |

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