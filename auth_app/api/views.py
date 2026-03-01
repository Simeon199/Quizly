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
        return Response({
            "detail": "Login successfully!",
            "user": user
        })
    
    def _set_access_token_cookie(self, response, access):
        response.set_cookie(
            key='access_token',
            value=str(access),
            httponly=True,
            secure=False,
            samesite='Lax'
        )
    
    def _set_refresh_token_cookie(self, response, refresh):
        response.set_cookie(
            key='refresh_token',
            value=str(refresh),
            httponly=True,
            secure=False,
            samesite='Lax'
        )
    
class CookieTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
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
        try:
            serializer = self.get_serializer(data={'refresh': refresh_token})
            serializer.is_valid(raise_exception=True)
            return serializer.validated_data.get('access')
        except Exception:
            return None
    
    def _set_access_token_cookie(self, response, access_token):
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
        self._blacklist_refresh_token(request)
        response = self._create_logout_response()
        self._delete_auth_cookies(response)
        return response
    
    def _blacklist_refresh_token(self, request):
        try:
            refresh_token = request.COOKIES.get('refresh_token')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
        except Exception:
            pass
    
    def _create_logout_response(self):
        return Response(
            {"detail": "Log-Out successfully! All Tokens will be deleted. Refresh token is now invalid."},
            status=status.HTTP_200_OK
        )
    
    def _delete_auth_cookies(self, response):
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')