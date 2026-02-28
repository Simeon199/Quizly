import pytest
from unittest.mock import patch
from django.contrib.auth.models import User
from rest_framework import status
from django.urls import reverse
from quiz_app.models import Quiz, Question
from .conftest import MOCK_QUESTIONS, MOCK_VIDEO_URL


# ==================== GET /api/quizzes/ ====================

@pytest.mark.django_db
def test_get_quizzes_authenticated(authenticated_client, sample_quiz):
    """
    Test retrieving all quizzes for an authenticated user.
    Verifies that an authenticated user can retrieve their quizzes with a
    200 OK response and correct quiz data.
    """
    url = reverse('quiz-list-create')
    response = authenticated_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1
    assert response.data[0]['title'] == 'Test Quiz'


@pytest.mark.django_db
def test_get_quizzes_includes_questions(authenticated_client, sample_quiz):
    """
    Test that retrieving quizzes includes all associated questions.
    Verifies that quiz list responses include all questions with correct
    titles, answer letters (A/B/C/D), and answer options as a dict.
    """
    url = reverse('quiz-list-create')
    response = authenticated_client.get(url)

    questions = response.data[0]['questions']
    assert len(questions) == 10
    assert questions[0]['question_title'] == 'Question 1'
    assert questions[0]['answer'] == 'A'
    assert isinstance(questions[0]['question_options'], dict)
    assert 'A' in questions[0]['question_options']


@pytest.mark.django_db
def test_get_quizzes_returns_expected_fields(authenticated_client, sample_quiz):
    """
    Test that quiz list response includes all required fields.
    Verifies that each quiz in the list contains all expected fields
    including id, timestamps, video URL, and questions.
    """
    url = reverse('quiz-list-create')
    response = authenticated_client.get(url)

    quiz_data = response.data[0]
    expected_fields = ['id', 'title', 'description', 'created_at', 'updated_at', 'video_url', 'questions']
    for field in expected_fields:
        assert field in quiz_data


@pytest.mark.django_db
def test_get_quizzes_unauthenticated(api_client):
    """
    Test that unauthenticated users cannot retrieve quiz list.
    Verifies that accessing the quiz list endpoint without authentication
    returns a 401 Unauthorized response.
    """
    url = reverse('quiz-list-create')
    response = api_client.get(url)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_get_quizzes_only_own_quizzes(authenticated_client, sample_quiz):
    """
    Test that users only see their own quizzes in the list.
    Verifies that when multiple users have quizzes, an authenticated user
    only sees their own quizzes, not quizzes from other users.
    """
    other_user = User.objects.create_user(
        username='otheruser',
        email='other@example.com',
        password='testpassword123'
    )
    Quiz.objects.create(
        user=other_user,
        title='Other Quiz',
        video_url=MOCK_VIDEO_URL,
        status=Quiz.Status.COMPLETED
    )

    url = reverse('quiz-list-create')
    response = authenticated_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1
    assert response.data[0]['title'] == 'Test Quiz'


@pytest.mark.django_db
def test_get_quizzes_empty_list(authenticated_client):
    """
    Test retrieving quiz list when no quizzes exist.
    Verifies that the quiz list endpoint returns 200 OK with an empty
    list when the authenticated user has no quizzes.
    """
    url = reverse('quiz-list-create')
    response = authenticated_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 0


# ==================== POST /api/quizzes/ ====================

@pytest.mark.django_db
@patch('quiz_app.api.views.generate_quiz', return_value=MOCK_QUESTIONS)
@patch('quiz_app.api.views.transcribe_audio', return_value='Mocked transcript text')
@patch('quiz_app.api.views.download_audio', return_value={
    'audio_path': '/tmp/fake_audio.mp3',
    'title': 'Mocked Video Title'
})
def test_post_quiz_success(mock_download, mock_transcribe, mock_generate, authenticated_client):
    """
    Test successfully creating a quiz from a video URL.
    Verifies that posting a valid video URL creates a new quiz with
    generated questions, returns 201 Created, and saves to the database.
    """
    url = reverse('quiz-list-create')
    response = authenticated_client.post(url, {'url': MOCK_VIDEO_URL}, format='json')

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data['title'] == 'Mocked Video Title'
    assert len(response.data['questions']) == 10
    assert Quiz.objects.count() == 1
    assert Question.objects.count() == 10


@pytest.mark.django_db
@patch('quiz_app.api.views.generate_quiz', return_value=MOCK_QUESTIONS)
@patch('quiz_app.api.views.transcribe_audio', return_value='Mocked transcript text')
@patch('quiz_app.api.views.download_audio', return_value={
    'audio_path': '/tmp/fake_audio.mp3',
    'title': 'Mocked Video Title'
})
def test_post_quiz_returns_expected_fields(mock_download, mock_transcribe, mock_generate, authenticated_client):
    """
    Test that created quiz response includes all required fields.
    Verifies that the POST response contains all expected quiz and question
    fields, including timestamps and video URL.
    """
    url = reverse('quiz-list-create')
    response = authenticated_client.post(url, {'url': MOCK_VIDEO_URL}, format='json')

    expected_quiz_fields = ['id', 'title', 'description', 'created_at', 'updated_at', 'video_url', 'questions']
    for field in expected_quiz_fields:
        assert field in response.data

    expected_question_fields = ['id', 'question_title', 'question_options', 'answer', 'created_at', 'updated_at']
    for field in expected_question_fields:
        assert field in response.data['questions'][0]


@pytest.mark.django_db
def test_post_quiz_unauthenticated(api_client):
    """
    Test that unauthenticated users cannot create quizzes.
    Verifies that attempting to create a quiz without authentication
    returns a 401 Unauthorized response.
    """
    url = reverse('quiz-list-create')
    response = api_client.post(url, {'url': MOCK_VIDEO_URL}, format='json')

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_post_quiz_invalid_url(authenticated_client):
    """
    Test that posting an invalid URL returns 400.
    Verifies that providing a malformed URL to create a quiz
    returns a 400 Bad Request response.
    """
    url = reverse('quiz-list-create')
    response = authenticated_client.post(url, {'url': 'not-a-valid-url'}, format='json')

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_post_quiz_missing_url(authenticated_client):
    """
    Test that posting without a URL returns 400.
    Verifies that omitting the required URL parameter
    returns a 400 Bad Request response.
    """
    url = reverse('quiz-list-create')
    response = authenticated_client.post(url, {}, format='json')

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
@patch('quiz_app.api.views.download_audio', side_effect=ValueError('Download failed'))
def test_post_quiz_download_failure(mock_download, authenticated_client):
    """
    Test quiz creation when audio download fails.
    Verifies that when the video audio download fails, the endpoint
    returns 400 Bad Request with error details.
    """
    url = reverse('quiz-list-create')
    response = authenticated_client.post(url, {'url': MOCK_VIDEO_URL}, format='json')

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'Download failed' in response.data['detail']


@pytest.mark.django_db
@patch('quiz_app.api.views.transcribe_audio', side_effect=ValueError('Transcription failed'))
@patch('quiz_app.api.views.download_audio', return_value={
    'audio_path': '/tmp/fake_audio.mp3',
    'title': 'Mocked Video Title'
})
def test_post_quiz_transcription_failure(mock_download, mock_transcribe, authenticated_client):
    """
    Test quiz creation when audio transcription fails.
    Verifies that when transcribing the audio fails, the endpoint
    returns 400 Bad Request with error details.
    """
    url = reverse('quiz-list-create')
    response = authenticated_client.post(url, {'url': MOCK_VIDEO_URL}, format='json')

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'Transcription failed' in response.data['detail']


@pytest.mark.django_db
@patch('quiz_app.api.views.generate_quiz', side_effect=ValueError('Quiz generation failed'))
@patch('quiz_app.api.views.transcribe_audio', return_value='Mocked transcript text')
@patch('quiz_app.api.views.download_audio', return_value={
    'audio_path': '/tmp/fake_audio.mp3',
    'title': 'Mocked Video Title'
})
def test_post_quiz_generation_failure(mock_download, mock_transcribe, mock_generate, authenticated_client):
    """
    Test quiz creation when quiz generation fails.
    Verifies that when generating quiz questions fails, the endpoint
    returns 400 Bad Request with error details.
    """
    url = reverse('quiz-list-create')
    response = authenticated_client.post(url, {'url': MOCK_VIDEO_URL}, format='json')

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'Quiz generation failed' in response.data['detail']
