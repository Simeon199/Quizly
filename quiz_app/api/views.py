from django.http import Http404
from rest_framework import generics, permissions, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from quiz_app.models import Quiz, Question
from .serializers import QuizSerializer, QuizCreateSerializer, QuizUpdateSerializer
from quiz_app.services.youtube_service import download_audio
from quiz_app.services.transcription_service import transcribe_audio
from quiz_app.services.quiz_generation_service import generate_quiz


class QuizDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API view for retrieving, updating, and deleting individual quizzes.
    Provides GET (retrieve), PATCH (partial update), and DELETE operations
    on user-owned quizzes. Enforces ownership-based access control.
    """

    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'patch', 'delete']

    def get_serializer_class(self):
        """
        Return appropriate serializer based on request method.
        Returns:
            Serializer class for the current request (QuizUpdateSerializer for PATCH,
            QuizSerializer for other methods).
        """

        if self.request.method == 'PATCH':
            return QuizUpdateSerializer
        return QuizSerializer

    def get_object(self):
        """
        Retrieve quiz with ownership verification.
        Returns:
            Quiz: The requested quiz object if owned by the current user.
        Raises:
            Http404: If quiz not found or user is not the owner (for GET requests).
            PermissionDenied: If user attempts to modify a quiz they don't own.
        """

        quiz = generics.get_object_or_404(Quiz, pk=self.kwargs['pk'])
        if quiz.user != self.request.user:
            if self.request.method == 'GET':
                raise Http404
            raise PermissionDenied()
        return quiz

    def partial_update(self, request, *args, **kwargs):
        """
        Partially update quiz title and/or description.
        Args:
            request: HTTP request containing partial update data.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        Returns:
            Response: Updated quiz data with HTTP 200 status.
        """
        quiz = self.get_object()
        serializer = self.get_serializer(quiz, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(QuizSerializer(quiz).data, status=status.HTTP_200_OK)


class QuizListCreateView(generics.ListCreateAPIView):
    """
    API view for listing user quizzes and creating new quizzes from videos.
    Provides GET (list all user quizzes) and POST (create quiz from video URL)
    operations. Handles the complete quiz generation pipeline including audio
    download, transcription, and AI-powered question generation.
    """
    
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        """
        Return appropriate serializer based on request method.
        Returns:
            QuizCreateSerializer for POST requests, QuizSerializer for GET.
        """

        if self.request.method == 'POST':
            return QuizCreateSerializer
        return QuizSerializer

    def get_queryset(self):
        """
        Return quizzes belonging to the authenticated user.
        Returns:
            QuerySet: All Quiz objects owned by the current user.
        """

        return Quiz.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        """
        Create a new quiz from a video URL.
        Validates the video URL and executes the quiz generation pipeline
        (download, transcribe, generate questions).
        Args:
            request: HTTP request containing video URL.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        Returns:
            Response: Created quiz data with HTTP 201 status or 400 error.
        """

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
        """
        Execute the complete quiz generation pipeline.
        Orchestrates audio download, transcription, and AI-powered question
        generation from a video URL.
        Args:
            video_url (str): URL of the video to process.
            user: The user requesting the quiz.
        Returns:
            Quiz: Saved quiz object with generated questions.
        Raises:
            ValueError: If any step in the pipeline fails.
        """

        result = download_audio(video_url)
        transcript = transcribe_audio(result['audio_path'])
        questions_data = generate_quiz(transcript)
        return self._save_quiz(
            user, result['title'], video_url,
            transcript, questions_data
        )

    def _save_quiz(self, user, title, video_url,
                   transcript, questions_data):
        """
        Save quiz and associated questions to database.
        Creates a Quiz object and bulk creates related Question objects
        with all metadata and generated content.
        Args:
            user: The user who owns the quiz.
            title (str): Quiz title from video metadata.
            video_url (str): URL of the source video.
            transcript (str): Full transcribed text from audio.
            questions_data (list): List of dictionaries containing question data.
        Returns:
            Quiz: The created quiz object with associated questions.
        """

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