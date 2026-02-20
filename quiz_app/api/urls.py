from django.urls import path
from .views import QuizListCreateView, QuizRetrieveView

urlpatterns = [
    path('quizzes/', QuizListCreateView.as_view(), name='quiz-list-create'),
    path('quizzes/<int:pk>/', QuizRetrieveView.as_view(), name='quiz-detail'),
]
