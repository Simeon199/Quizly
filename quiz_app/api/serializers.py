from rest_framework import serializers
from quiz_app.models import Quiz, Question


class QuestionSerializer(serializers.ModelSerializer):
    question_options = serializers.SerializerMethodField()
    answer = serializers.SerializerMethodField()

    def get_question_options(self, obj):
        return list(obj.question_options.values())

    def get_answer(self, obj):
        return obj.question_options.get(obj.answer, obj.answer)

    class Meta:
        model = Question
        fields = [
            'id', 'question_title', 'question_options',
            'answer', 'created_at', 'updated_at'
        ]


class QuizSerializer(serializers.ModelSerializer):
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
    url = serializers.URLField()


class QuizUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quiz
        fields = ['title', 'description']
        extra_kwargs = {
            'title': {'required': False},
            'description': {'required': False},
        }
