import pytest
from django.contrib.auth.models import User
from rest_framework import status
from django.urls import reverse
from quiz_app.models import Quiz, Question
from .conftest import MOCK_VIDEO_URL


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
    assert questions[0]['answer'] == 'Option A'
    assert isinstance(questions[0]['question_options'], list)
    assert 'Option A' in questions[0]['question_options']


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


# ==================== PATCH /api/quizzes/{id}/ ====================

@pytest.mark.django_db
def test_patch_quiz_success(authenticated_client, sample_quiz):
    url = reverse('quiz-detail', kwargs={'pk': sample_quiz.pk})
    update_data = {'title': 'Updated Quiz Title', 'description': 'Updated description'}
    response = authenticated_client.patch(url, update_data, format='json')

    assert response.status_code == status.HTTP_200_OK
    assert response.data['title'] == 'Updated Quiz Title'
    assert response.data['description'] == 'Updated description'

    # Verify the changes were persisted
    sample_quiz.refresh_from_db()
    assert sample_quiz.title == 'Updated Quiz Title'
    assert sample_quiz.description == 'Updated description'


@pytest.mark.django_db
def test_patch_quiz_partial_update(authenticated_client, sample_quiz):
    original_description = sample_quiz.description
    url = reverse('quiz-detail', kwargs={'pk': sample_quiz.pk})
    update_data = {'title': 'New Title Only'}
    response = authenticated_client.patch(url, update_data, format='json')

    assert response.status_code == status.HTTP_200_OK
    assert response.data['title'] == 'New Title Only'
    assert response.data['description'] == original_description

    # Verify only title was updated
    sample_quiz.refresh_from_db()
    assert sample_quiz.title == 'New Title Only'
    assert sample_quiz.description == original_description


@pytest.mark.django_db
def test_patch_quiz_update_description_only(authenticated_client, sample_quiz):
    original_title = sample_quiz.title
    url = reverse('quiz-detail', kwargs={'pk': sample_quiz.pk})
    update_data = {'description': 'A completely new description'}
    response = authenticated_client.patch(url, update_data, format='json')

    assert response.status_code == status.HTTP_200_OK
    assert response.data['title'] == original_title
    assert response.data['description'] == 'A completely new description'


@pytest.mark.django_db
def test_patch_quiz_returns_all_fields(authenticated_client, sample_quiz):
    url = reverse('quiz-detail', kwargs={'pk': sample_quiz.pk})
    update_data = {'title': 'Updated Title'}
    response = authenticated_client.patch(url, update_data, format='json')

    expected_fields = ['id', 'title', 'description', 'created_at', 'updated_at', 'video_url', 'questions']
    for field in expected_fields:
        assert field in response.data


@pytest.mark.django_db
def test_patch_quiz_unauthenticated(api_client, sample_quiz):
    url = reverse('quiz-detail', kwargs={'pk': sample_quiz.pk})
    response = api_client.patch(url, {'title': 'New Title'}, format='json')

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_patch_quiz_not_found(authenticated_client):
    url = reverse('quiz-detail', kwargs={'pk': 99999})
    response = authenticated_client.patch(url, {'title': 'New Title'}, format='json')

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_patch_quiz_other_users_quiz(authenticated_client):
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
    response = authenticated_client.patch(url, {'title': 'Updated Title'}, format='json')

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_patch_quiz_preserves_questions(authenticated_client, sample_quiz):
    original_question_count = sample_quiz.questions.count()
    url = reverse('quiz-detail', kwargs={'pk': sample_quiz.pk})
    update_data = {'title': 'Updated Title'}
    response = authenticated_client.patch(url, update_data, format='json')

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data['questions']) == original_question_count


# ==================== DELETE /api/quizzes/{id}/ ====================

@pytest.mark.django_db
def test_delete_quiz_success(authenticated_client, sample_quiz):
    quiz_id = sample_quiz.pk
    url = reverse('quiz-detail', kwargs={'pk': quiz_id})
    response = authenticated_client.delete(url)

    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verify the quiz was actually deleted
    assert Quiz.objects.filter(pk=quiz_id).count() == 0


@pytest.mark.django_db
def test_delete_quiz_cascade_deletes_questions(authenticated_client, sample_quiz):
    quiz_id = sample_quiz.pk
    original_question_count = Question.objects.filter(quiz=sample_quiz).count()
    assert original_question_count == 10

    url = reverse('quiz-detail', kwargs={'pk': quiz_id})
    response = authenticated_client.delete(url)

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert Question.objects.filter(quiz_id=quiz_id).count() == 0


@pytest.mark.django_db
def test_delete_quiz_unauthenticated(api_client, sample_quiz):
    url = reverse('quiz-detail', kwargs={'pk': sample_quiz.pk})
    response = api_client.delete(url)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # Verify the quiz was NOT deleted
    assert Quiz.objects.filter(pk=sample_quiz.pk).exists()


@pytest.mark.django_db
def test_delete_quiz_not_found(authenticated_client):
    url = reverse('quiz-detail', kwargs={'pk': 99999})
    response = authenticated_client.delete(url)

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_delete_quiz_other_users_quiz(authenticated_client):
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
    other_quiz_id = other_quiz.pk

    url = reverse('quiz-detail', kwargs={'pk': other_quiz_id})
    response = authenticated_client.delete(url)

    assert response.status_code == status.HTTP_403_FORBIDDEN

    # Verify the quiz was NOT deleted
    assert Quiz.objects.filter(pk=other_quiz_id).exists()


@pytest.mark.django_db
def test_delete_quiz_cannot_be_retrieved_after_deletion(authenticated_client, sample_quiz):
    quiz_id = sample_quiz.pk

    # First, delete the quiz
    url = reverse('quiz-detail', kwargs={'pk': quiz_id})
    delete_response = authenticated_client.delete(url)
    assert delete_response.status_code == status.HTTP_204_NO_CONTENT

    # Then try to retrieve it
    get_response = authenticated_client.get(url)
    assert get_response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_delete_quiz_does_not_affect_other_quizzes(authenticated_client, user):
    quiz1 = Quiz.objects.create(
        user=user,
        title='Quiz 1',
        video_url=MOCK_VIDEO_URL,
        status=Quiz.Status.COMPLETED
    )
    quiz2 = Quiz.objects.create(
        user=user,
        title='Quiz 2',
        video_url=MOCK_VIDEO_URL,
        status=Quiz.Status.COMPLETED
    )

    url = reverse('quiz-detail', kwargs={'pk': quiz1.pk})
    response = authenticated_client.delete(url)

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not Quiz.objects.filter(pk=quiz1.pk).exists()
    assert Quiz.objects.filter(pk=quiz2.pk).exists()
