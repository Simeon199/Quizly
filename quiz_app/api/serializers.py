from rest_framework import serializers
from quiz_app.models import Quiz, Question


class QuestionSerializer(serializers.ModelSerializer):
    """
    Serializer for Question model instances.
    Serializes question data including title, multiple choice options,
    correct answer, and timestamp fields for API responses.
    """

    class Meta:
        model = Question
        fields = [
            'id', 'question_title', 'question_options',
            'answer', 'created_at', 'updated_at'
        ]


class QuizSerializer(serializers.ModelSerializer):
    """
    Serializer for Quiz model with nested questions.
    Provides a complete quiz representation including metadata, video URL,
    and all associated questions as nested serialized objects. Read-only for dates.
    """

    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = [
            'id', 'title', 'description',
            'created_at', 'updated_at',
            'video_url', 'questions'
        ]
        read_only_fields = ['created_at', 'updated_at']


class QuizCreateSerializer(serializers.Serializer):
    """
    Serializer for creating a quiz from a video URL.
    Accepts a video URL and handles quiz generation from the video content.
    Used as input validation for quiz creation endpoint.
    """

    url = serializers.URLField()


class QuizUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating quiz title and description.
    Allows partial updates to quiz metadata. Both title and description
    are optional fields to support PATCH requests.
    """

    class Meta:
        model = Quiz
        fields = ['title', 'description']
        extra_kwargs = {
            'title': {'required': False},
            'description': {'required': False},
        }