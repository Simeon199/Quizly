from django.urls import path
from .views import QuizListCreateView, QuizRetrieveView, QuizUpdateView, QuizDestroyView

urlpatterns = [
    path('quizzes/', QuizListCreateView.as_view(), name='quiz-list-create'),
    path('quizzes/<int:pk>/', QuizRetrieveView.as_view(), name='quiz-detail'),
    path('quizzes/<int:pk>/update/', QuizUpdateView.as_view(), name='quiz-update'),
    path('quizzes/<int:pk>/delete/', QuizDestroyView.as_view(), name='quiz-delete'),
]
