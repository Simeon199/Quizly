from django.urls import path
from .views import RegistrationView

urlpatterns = [
    path('api/registration/', RegistrationView.as_view(), name='registration'),
]