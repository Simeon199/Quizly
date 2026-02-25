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
    """
    Provide a REST framework API test client.
    
    Returns:
        APIClient: An unauthenticated API client for making test requests.
    """
    return APIClient()


@pytest.fixture
def user():
    """
    Create and return a test user.
    Creates a Django User object with predefined credentials for use in tests.
    
    Returns:
        User: A Django User instance with username 'quizuser'.
    """
    return User.objects.create_user(
        username='quizuser',
        email='quiz@example.com',
        password='testpassword123'
    )


@pytest.fixture
def authenticated_client(api_client, user):
    """
    Provide an authenticated REST API test client.
    Returns an APIClient that is authenticated as the test user, allowing
    protected endpoints to be tested.
    
    Args:
        api_client: The unauthenticated API client fixture.
        user: The test user fixture.
    
    Returns:
        APIClient: An API client authenticated as the test user.
    """
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def sample_quiz(user):
    """
    Create and return a sample quiz with 10 questions.
    Creates a Quiz object associated with the test user and populates it with
    10 Question objects, each having 4 multiple choice options.
    
    Args:
        user: The test user fixture to associate with the quiz.
    
    Returns:
        Quiz: A Quiz instance with 10 associated Question objects.
    """
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
