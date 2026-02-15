import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def user_data():
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123",
        "confirmed_password": "testpassword123"
    }

@pytest.fixture
def created_user(user_data):
    return User.objects.create_user(
        username=user_data['username'],
        email=user_data['email'],
        password=user_data['password']
    )

@pytest.mark.django_db
def test_registration(api_client, user_data):
    url = reverse('registration')
    response = api_client.post(url, user_data)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data['detail'] == "User created successfully!"
    assert User.objects.filter(username=user_data['username']).exists()

@pytest.mark.django_db
def test_registration_password_mismatch(api_client, user_data):
    url = reverse('registration')
    user_data['confirmed_password'] = "wrongpassword"
    response = api_client.post(url, user_data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'password' in response.data

@pytest.mark.django_db
def test_login(api_client, created_user, user_data):
    url = reverse('token_obtain_pair')
    login_data = {
        "username": user_data['username'],
        "password": user_data['password']
    }
    response = api_client.post(url, login_data)
    assert response.status_code == status.HTTP_200_OK
    assert response.data['detail'] == "Login successfully!"
    assert response.data['user']['username'] == user_data['username']
    assert 'access_token' in response.cookies
    assert 'refresh_token' in response.cookies

@pytest.mark.django_db
def test_refresh_token(api_client, created_user):
    # First login to get a refresh token
    login_url = reverse('token_obtain_pair')
    login_response = api_client.post(login_url, {
        "username": created_user.username,
        "password": "testpassword123"
    })
    refresh_token = login_response.cookies['refresh_token'].value

    # Refresh
    refresh_url = reverse('token_refresh')
    api_client.cookies['refresh_token'] = refresh_token
    response = api_client.post(refresh_url)
    
    assert response.status_code == status.HTTP_200_OK
    assert response.data['detail'] == "Token refreshed"
    assert 'access_token' in response.cookies

@pytest.mark.django_db
def test_logout(api_client, created_user):
     # First login to get a refresh token
    login_url = reverse('token_obtain_pair')
    login_response = api_client.post(login_url, {
        "username": created_user.username,
        "password": "testpassword123"
    })
    refresh_token = login_response.cookies['refresh_token'].value
    access_token = login_response.cookies['access_token'].value

    # Logout
    logout_url = reverse('logout')
    api_client.cookies['refresh_token'] = refresh_token
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}') 
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
    response = api_client.post(logout_url)
    
    assert response.status_code == status.HTTP_200_OK
    assert "Log-Out successfully" in response.data['detail']
    assert response.cookies['access_token'].value == ''
    assert response.cookies['refresh_token'].value == ''
