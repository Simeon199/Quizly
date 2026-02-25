import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from quiz_app.models import Quiz, Question


MOCK_VIDEO_URL = 'https://www.youtube.com/watch?v=test123'

MOCK_QUESTIONS = [
    {
        'question_title': f'Question {i}',
        'question_options': {
            'A': 'Option A',
            'B': 'Option B',
            'C': 'Option C',
            'D': 'Option D',
        },
        'answer': 'A',
    }
    for i in range(1, 11)
]


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user():
    return User.objects.create_user(
        username='quizuser',
        email='quiz@example.com',
        password='testpassword123'
    )


@pytest.fixture
def authenticated_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def sample_quiz(user):
    quiz = Quiz.objects.create(
        user=user,
        title='Test Quiz',
        description='A test quiz',
        video_url=MOCK_VIDEO_URL,
        transcript='Some transcript text',
        status=Quiz.Status.COMPLETED
    )
    for i in range(1, 11):
        Question.objects.create(
            quiz=quiz,
            question_title=f'Question {i}',
            question_options={
                'A': 'Option A',
                'B': 'Option B',
                'C': 'Option C',
                'D': 'Option D',
            },
            answer='A'
        )
    return quiz
