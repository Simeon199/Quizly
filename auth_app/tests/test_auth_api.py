import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse

@pytest.fixture
def api_client():
    """
    Provide a REST API client for making test requests.
    Returns:
        APIClient: Django REST framework test client instance.
    """
    return APIClient()

@pytest.fixture
def user_data():
    """
    Provide test user registration data.
    Returns:
        dict: Dictionary containing username, email, password, and confirmed_password.
    """
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123",
        "confirmed_password": "testpassword123"
    }

@pytest.fixture
def created_user(user_data):
    """
    Create a test user in the database.
    Args:
        user_data: Fixture providing test user credentials.
    Returns:
        User: A Django User instance with test credentials saved to database.
    """
    return User.objects.create_user(
        username=user_data['username'],
        email=user_data['email'],
        password=user_data['password']
    )

@pytest.mark.django_db
def test_registration(api_client, user_data):
    """
    Test successful user registration.
    Verifies that a new user can register with valid credentials and that
    the user is saved to the database.
    """
    url = reverse('registration')
    response = api_client.post(url, user_data)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data['detail'] == "User created successfully!"
    assert User.objects.filter(username=user_data['username']).exists()

@pytest.mark.django_db
def test_registration_password_mismatch(api_client, user_data):
    """
    Test registration fails when passwords do not match.
    Verifies that the registration endpoint rejects credentials where
    password and confirmed_password fields do not match.
    """
    url = reverse('registration')
    user_data['confirmed_password'] = "wrongpassword"
    response = api_client.post(url, user_data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'password' in response.data

@pytest.mark.django_db
def test_login(api_client, created_user, user_data):
    """
    Test successful user login with token generation.
    Verifies that a registered user can login with correct credentials,
    tokens are set in cookies, and user data is returned in response.
    """
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
    """
    Test access token refresh using refresh token.
    Verifies that a user can obtain a new access token by providing
    a valid refresh token from a previous login.
    """
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
    """
    Test user logout with token blacklisting and cookie deletion.
    Verifies that an authenticated user can logout, refresh token is blacklisted,
    and authentication cookies are deleted from the response.
    """
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

@pytest.mark.django_db
def test_registration_duplicate_email(api_client, user_data, created_user):
    """
    Test registration fails when email is already registered.
    Verifies that the registration endpoint rejects attempts to register
    with an email address that already exists in the system.
    """
    url = reverse('registration')
    response = api_client.post(url, user_data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'email' in response.data

@pytest.mark.django_db
def test_login_invalid_credentials(api_client, created_user, user_data):
    """
    Test login fails with incorrect password.
    Verifies that the login endpoint rejects credentials when the password
    does not match the registered user's password.
    """
    url = reverse('token_obtain_pair')
    login_data = {
        "username": user_data['username'],
        "password": "wrongpassword"
    }
    response = api_client.post(url, login_data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data['detail'] == "No active account found with the given credentials"

@pytest.mark.django_db
def test_refresh_token_invalid(api_client):
    """
    Test token refresh fails with invalid refresh token.
    Verifies that the token refresh endpoint rejects requests with
    an invalid or malformed refresh token.
    """
    refresh_url = reverse('token_refresh')
    api_client.cookies['refresh_token'] = 'invalid_token'
    response = api_client.post(refresh_url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data['detail'] == "Refresh token invalid!"
