import pytest
from unittest.mock import patch
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from quiz_app.models import Quiz, Question


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

MOCK_VIDEO_URL = 'https://www.youtube.com/watch?v=test123'


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


# ==================== GET /api/quizzes/ ====================

@pytest.mark.django_db
def test_get_quizzes_authenticated(authenticated_client, sample_quiz):
    url = reverse('quiz-list-create')
    response = authenticated_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1
    assert response.data[0]['title'] == 'Test Quiz'


@pytest.mark.django_db
def test_get_quizzes_includes_questions(authenticated_client, sample_quiz):
    url = reverse('quiz-list-create')
    response = authenticated_client.get(url)

    questions = response.data[0]['questions']
    assert len(questions) == 10
    assert questions[0]['question_title'] == 'Question 1'
    assert questions[0]['answer'] == 'A'
    assert 'A' in questions[0]['question_options']


@pytest.mark.django_db
def test_get_quizzes_returns_expected_fields(authenticated_client, sample_quiz):
    url = reverse('quiz-list-create')
    response = authenticated_client.get(url)

    quiz_data = response.data[0]
    expected_fields = ['id', 'title', 'description', 'created_at', 'updated_at', 'video_url', 'questions']
    for field in expected_fields:
        assert field in quiz_data


@pytest.mark.django_db
def test_get_quizzes_unauthenticated(api_client):
    url = reverse('quiz-list-create')
    response = api_client.get(url)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_get_quizzes_only_own_quizzes(authenticated_client, sample_quiz):
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
    url = reverse('quiz-list-create')
    response = api_client.post(url, {'url': MOCK_VIDEO_URL}, format='json')

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_post_quiz_invalid_url(authenticated_client):
    url = reverse('quiz-list-create')
    response = authenticated_client.post(url, {'url': 'not-a-valid-url'}, format='json')

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_post_quiz_missing_url(authenticated_client):
    url = reverse('quiz-list-create')
    response = authenticated_client.post(url, {}, format='json')

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
@patch('quiz_app.api.views.download_audio', side_effect=ValueError('Download failed'))
def test_post_quiz_download_failure(mock_download, authenticated_client):
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
    url = reverse('quiz-list-create')
    response = authenticated_client.post(url, {'url': MOCK_VIDEO_URL}, format='json')

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'Quiz generation failed' in response.data['detail']


# ==================== GET /api/quizzes/{id}/ ====================

@pytest.mark.django_db
def test_get_quiz_by_id_authenticated(authenticated_client, sample_quiz):
    url = reverse('quiz-detail', kwargs={'pk': sample_quiz.pk})
    response = authenticated_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data['id'] == sample_quiz.pk
    assert response.data['title'] == 'Test Quiz'


@pytest.mark.django_db
def test_get_quiz_by_id_includes_questions(authenticated_client, sample_quiz):
    url = reverse('quiz-detail', kwargs={'pk': sample_quiz.pk})
    response = authenticated_client.get(url)

    questions = response.data['questions']
    assert len(questions) == 10
    assert questions[0]['question_title'] == 'Question 1'
    assert questions[0]['answer'] == 'A'
    assert 'A' in questions[0]['question_options']


@pytest.mark.django_db
def test_get_quiz_by_id_returns_expected_fields(authenticated_client, sample_quiz):
    url = reverse('quiz-detail', kwargs={'pk': sample_quiz.pk})
    response = authenticated_client.get(url)

    expected_quiz_fields = ['id', 'title', 'description', 'created_at', 'updated_at', 'video_url', 'questions']
    for field in expected_quiz_fields:
        assert field in response.data

    expected_question_fields = ['id', 'question_title', 'question_options', 'answer']
    for field in expected_question_fields:
        assert field in response.data['questions'][0]


@pytest.mark.django_db
def test_get_quiz_by_id_unauthenticated(api_client, sample_quiz):
    url = reverse('quiz-detail', kwargs={'pk': sample_quiz.pk})
    response = api_client.get(url)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_get_quiz_by_id_not_found(authenticated_client):
    url = reverse('quiz-detail', kwargs={'pk': 99999})
    response = authenticated_client.get(url)

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_get_quiz_by_id_other_users_quiz(authenticated_client, sample_quiz):
    other_user = User.objects.create_user(
        username='otheruser',
        email='other@example.com',
        password='testpassword123'
    )
    other_quiz = Quiz.objects.create(
        user=other_user,
        title='Other Quiz',
        video_url=MOCK_VIDEO_URL,
        status=Quiz.Status.COMPLETED
    )

    url = reverse('quiz-detail', kwargs={'pk': other_quiz.pk})
    response = authenticated_client.get(url)

    assert response.status_code == status.HTTP_404_NOT_FOUND
