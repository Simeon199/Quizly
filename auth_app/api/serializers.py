from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User

User = get_user_model()

class RegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration validation and account creation.
    Validates that passwords match and email is unique before saving a new user account.
    """
    confirmed_password = serializers.CharField(write_only=True)
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'confirmed_password']
        extra_kwargs = {
            'password': {
                'write_only': True
            },
            'email': {
                'required': True
            }
        }

    def validate(self, attrs):
        """
        Validate that password and confirmed_password fields match.
        Args:
            attrs (dict): Dictionary of field values to validate.
        Returns:
            dict: Validated attributes if passwords match.
        Raises:
            ValidationError: If password and confirmed_password do not match.
        """
        password = attrs.get('password')
        confirmed_password = attrs.get('confirmed_password')
        if password != confirmed_password:
            raise serializers.ValidationError({'password': 'Passwords do not match.'})
        return attrs

    def validate_email(self, value):
        """
        Validate that the email address is not already registered.
        Args:
            value (str): Email address to validate.    
        Returns:
            str: The email address if it is unique.
        Raises:
            ValidationError: If email already exists in the database.
        """
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Email already exists')
        return value

    def save(self):
        """
        Create and save a new user account with hashed password.
        Returns:
            User: The newly created user instance with hashed password.
        """
        pw = self.validated_data['password']
        account = User(email=self.validated_data['email'], username=self.validated_data['username'])
        account.set_password(pw)
        account.save()
        return account
    
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom token serializer that includes user information in the response.
    Extends TokenObtainPairSerializer to add user id, username, and email data
    to the token response for better client-side user context.
    """

    def validate(self, attrs):
        """
        Validate credentials and enhance token response with user data.
        Args:
            attrs (dict): Dictionary containing 'username' and 'password'.
        Returns:
            dict: Token data with added 'user' key containing id, username, and email.
        """
        data = super().validate(attrs)
        data.update({'user': {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email
        }})
        return data