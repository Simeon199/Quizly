from django.urls import path
from .views import RegistrationView, CookieTokenObtainPairView, CookieTokenRefreshView

urlpatterns = [
    path('api/registration/', RegistrationView.as_view(), name='registration'),
    path('api/token/', CookieTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', CookieTokenRefreshView.as_view(), name='token_refresh'),
]