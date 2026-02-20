from django.urls import path
from .views import QuizListCreateView, QuizRetrieveView, QuizUpdateView

urlpatterns = [
    path('quizzes/', QuizListCreateView.as_view(), name='quiz-list-create'),
    path('quizzes/<int:pk>/', QuizRetrieveView.as_view(), name='quiz-detail'),
    path('quizzes/<int:pk>/update/', QuizUpdateView.as_view(), name='quiz-update'),
]
