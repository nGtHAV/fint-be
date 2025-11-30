"""
User serializers
"""
from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer):
    """User serializer for API responses"""
    
    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'avatar_url', 'created_at']
        read_only_fields = ['id', 'created_at']


class RegisterSerializer(serializers.Serializer):
    """Serializer for user registration"""
    name = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    password = serializers.CharField(min_length=6, write_only=True)
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Email already registered')
        return value


class LoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for password change"""
    currentPassword = serializers.CharField(write_only=True)
    newPassword = serializers.CharField(min_length=6, write_only=True)


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer for password reset request"""
    email = serializers.EmailField()


class PasswordResetSerializer(serializers.Serializer):
    """Serializer for password reset"""
    token = serializers.CharField()
    password = serializers.CharField(min_length=6, write_only=True)


class ProfileUpdateSerializer(serializers.Serializer):
    """Serializer for profile update"""
    name = serializers.CharField(max_length=255, required=False)
    avatar_url = serializers.URLField(required=False, allow_blank=True)
