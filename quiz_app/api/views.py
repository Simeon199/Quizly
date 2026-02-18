from rest_framework import generics, permissions, status
from rest_framework.response import Response
from quiz_app.models import Quiz, Question
from .serializers import QuizSerializer, QuizCreateSerializer
from quiz_app.services.youtube_service import download_audio
from quiz_app.services.transcription_service import transcribe_audio
from quiz_app.services.quiz_generation_service import generate_quiz


class QuizListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return QuizCreateSerializer
        return QuizSerializer

    def get_queryset(self):
        return Quiz.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        video_url = serializer.validated_data['url']

        try:
            quiz = self._run_pipeline(video_url, request.user)
        except ValueError as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        output = QuizSerializer(quiz)
        return Response(output.data, status=status.HTTP_201_CREATED)

    def _run_pipeline(self, video_url, user):
        result = download_audio(video_url)
        transcript = transcribe_audio(result['audio_path'])
        questions_data = generate_quiz(transcript)
        return self._save_quiz(
            user, result['title'], video_url,
            transcript, questions_data
        )

    def _save_quiz(self, user, title, video_url,
                   transcript, questions_data):
        quiz = Quiz.objects.create(
            user=user,
            title=title,
            video_url=video_url,
            transcript=transcript,
            status=Quiz.Status.COMPLETED
        )
        questions = [
            Question(quiz=quiz, **q) for q in questions_data
        ]
        Question.objects.bulk_create(questions)
        return quiz
