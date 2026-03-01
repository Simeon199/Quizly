from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import RegistrationSerializer, CustomTokenObtainPairSerializer

class RegistrationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        """
        Register a new user account.  
        Args:
            request: HTTP request containing user registration data.
        Returns:
            Response: 201 Created with success message or 400 Bad Request with validation errors.
        """
        serializer = RegistrationSerializer(data=request.data)

        data = {}
        if serializer.is_valid():
            saved_account = serializer.save()
            data = {
                'detail': "User created successfully!"
            }
            return Response(data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
class CookieTokenObtainPairView(TokenObtainPairView):

    serializer_class = CustomTokenObtainPairSerializer
    
    def post(self, request, *args, **kwargs):
        """
        Authenticate user and set JWT tokens in secure cookies.
        Args:
            request: HTTP request containing user credentials.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        Returns:
            Response: 200 OK with login success message and user data, tokens set in cookies.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        refresh = serializer.validated_data['refresh']
        access = serializer.validated_data['access']
        user = serializer.validated_data['user']
        
        response = self._create_login_response(user)
        self._set_access_token_cookie(response, access)
        self._set_refresh_token_cookie(response, refresh)
        
        return response
    
    def _create_login_response(self, user):
        """Create a login success response with user data.
        Args:
            user: Authenticated user object.
        Returns:
            Response: Response object with success message and user information.
        """
        return Response({
            "detail": "Login successfully!",
            "user": user
        })
    
    def _set_access_token_cookie(self, response, access):
        """
        Set the access token in an HTTP-only, secure cookie.
        Args:
            response: Response object to set the cookie on.
            access: JWT access token string.
        """
        response.set_cookie(
            key='access_token',
            value=str(access),
            httponly=True,
            secure=False,
            samesite='Lax'
        )
    
    def _set_refresh_token_cookie(self, response, refresh):
        """
        Set the refresh token in an HTTP-only, secure cookie.
        Args:
            response: Response object to set the cookie on.
            refresh: JWT refresh token string.
        """
        response.set_cookie(
            key='refresh_token',
            value=str(refresh),
            httponly=True,
            secure=False,
            samesite='Lax'
        )
    
class CookieTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        """
        Refresh the access token using the refresh token from cookies.
        Args:
            request: HTTP request containing refresh token in cookies.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        Returns:
            Response: 200 OK with refreshed access token in cookie, or 400/401 error responses.
        """
        refresh_token = request.COOKIES.get('refresh_token')
        if refresh_token is None:
            return Response(
                {'detail': 'Refresh token not found!'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        access_token = self._refresh_access_token(refresh_token)
        if access_token is None:
            return Response(
                {'detail': 'Refresh token invalid!'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        response = Response({'detail': 'Token refreshed'})
        self._set_access_token_cookie(response, access_token)
        return response
    
    def _refresh_access_token(self, refresh_token):
        """
        Validate refresh token and return new access token.
        Args:
            refresh_token: JWT refresh token string.
        Returns:
            str: New access token if successful, None if token is invalid.
        """
        try:
            serializer = self.get_serializer(data={'refresh': refresh_token})
            serializer.is_valid(raise_exception=True)
            return serializer.validated_data.get('access')
        except Exception:
            return None
    
    def _set_access_token_cookie(self, response, access_token):
        """
        Set the refreshed access token in an HTTP-only, secure cookie.
        Args:
            response: Response object to set the cookie on.
            access_token: JWT access token string.
        """
        response.set_cookie(
            key='access_token',
            value=access_token,
            httponly=True,
            secure=False,
            samesite='Lax'
        )

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Logout user by blacklisting refresh token and clearing auth cookies.
        Args:
            request: Authenticated HTTP request.
        Returns:
            Response: 200 OK with logout success message, cookies deleted.
        """
        self._blacklist_refresh_token(request)
        response = self._create_logout_response()
        self._delete_auth_cookies(response)
        return response
    
    def _blacklist_refresh_token(self, request):
        """
        Add refresh token to blacklist to invalidate it.
        Args:
            request: HTTP request containing refresh token in cookies.
        """
        try:
            refresh_token = request.COOKIES.get('refresh_token')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
        except Exception:
            pass
    
    def _create_logout_response(self):
        """
        Create a logout success response.
        Returns:
            Response: 200 OK response with logout success message.
        """
        return Response(
            {"detail": "Log-Out successfully! All Tokens will be deleted. Refresh token is now invalid."},
            status=status.HTTP_200_OK
        )
    
    def _delete_auth_cookies(self, response):
        """
        Remove authentication cookies from the response.
        Args:
            response: Response object to delete cookies from.
        """
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')