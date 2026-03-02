from django.db import models
from django.conf import settings


class Quiz(models.Model):
    """
    Model representing a quiz generated from a video.
    Stores quiz metadata, video URL, transcribed content, and processing status.
    A quiz contains multiple questions generated from the video transcript.
    Attributes:
        user: Foreign key to the user who created the quiz.
        title: Quiz title extracted from video metadata.
        description: Optional user-provided quiz description.
        video_url: URL of the source video.
        transcript: Full transcribed text from the video audio.
        status: Processing status (processing, completed, or failed).
        created_at: Timestamp when the quiz was created.
        updated_at: Timestamp when the quiz was last updated.
    """

    class Status(models.TextChoices):
        """
        Processing status choices for quiz generation pipeline.
        """

        PROCESSING = 'processing', 'Processing'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='quizzes'
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    video_url = models.URLField()
    transcript = models.TextField(blank=True, default='')
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PROCESSING
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'quizzes'

    def __str__(self):
        """
        Return the quiz title as string representation.
        Returns:
            str: The title of the quiz.
        """

        return self.title


class Question(models.Model):
    """
    Model representing a single question within a quiz.
    Stores question content, multiple choice options, and the correct answer.
    Questions are generated from the video transcript using AI.
    Attributes:
        quiz: Foreign key to the parent Quiz object.
        question_title: The question text.
        question_options: JSON field containing list of answer choices.
        answer: The correct answer for the question.
        created_at: Timestamp when the question was created.
        updated_at: Timestamp when the question was last updated.
    """

    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name='questions'
    )
    question_title = models.CharField(max_length=500)
    question_options = models.JSONField(default=list)
    answer = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        """
        Return the question title as string representation.
        Returns:
            str: The question text.
        """

        return self.question_title