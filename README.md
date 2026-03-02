# Quizly Backend

This project is designed as a portfolio project for further training as a backend developer. It builds on an existing frontend and is able to generate multiple-choice quizzes from YouTube videos using the Google Gemini AI. Users provide a video URL, and Quizly downloads the audio, transcribes it, and produces a 10-question quiz — all in one single API call. The respective frontend repository can be found under the following link:
[Quizly Frontend](https://github.com/Developer-Akademie-Backendkurs/project.Quizly)

## Table of Contents
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Environment Variables](#environment-variables)
- [Running the Server](#running-the-server)
- [Creating a Superuser](#creating-a-superuser)
- [API Testing with Postman](#api-testing-with-postman)
- [Quiz Generation Pipeline](#quiz-generation-pipeline)
- [Token Configuration](#token-configuration)

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

## Prerequisites
To get started with running the application locally,
ensure you have the following prerequisites:

- Python 3.11+
- A [Google Gemini API key](https://aistudio.google.com/)
- [Postman](https://www.postman.com/downloads/) (optional, for easy API testing)

## Installation

1. Clone: `git clone https://github.com/Simeon199/Quizly.git && cd Quizly`
2. Virtualenv: `python -m venv env && env\Scripts\activate` (Windows)
3. Install: `pip install -r requirements.txt`
4. Migrate: `python manage.py makemigrations && python manage.py migrate`

## Environment Variables

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

## Running the Server

1. Run: `python manage.py runserver`
2. Access the API at `http://127.0.0.1:8000/` in your browser or API client.

This launches Django's built-in development server, allowing you to test the API endpoints locallly. Note that this is for development only.

## Creating a Superuser

To access admin features or perform administrative tasks, create a superuser account:

1. Run `python manage.py createsuperuser`
2. Follow the prompts to enter a username, email, and password.
3. Use the superuser credentials to log in via the Django admin panel at `http://127.0.0.1:8000/admin/` or for API authentication.

This is useful for testing permissions, managing users, and accessing protected endpoints.

## API Testing with Postman

A [Postman Collection](postman/postman_collection.json) is included to help you test the API endpoints.

**How to use:**

1. Install Postman and import the collection from `postman/postman_collection.json`.
2. Set the base URL to `http://127.0.0.1:8000/` and adjust further environment variables if necessary.
3. Use the requests to test and explore API features.

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

## Token Configuration

| Token         | Lifetime   |
|---------------|------------|
| Access token  | 120 minutes|
| Refresh token | 3 days     |

Tokens are transmitted exclusively via HTTP-only cookies and are never exposed in the response body.