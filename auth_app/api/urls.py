from django.urls import path
from .views import RegistrationView, CookieTokenObtainPairView, CookieTokenRefreshView, LogoutView

urlpatterns = [
    path('api/register/', RegistrationView.as_view(), name='registration'),
    path('api/login/', CookieTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/logout/', LogoutView.as_view(), name='logout'),
    path('api/token/refresh/', CookieTokenRefreshView.as_view(), name='token_refresh'),
]