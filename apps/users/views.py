"""
Authentication views
"""
import secrets
from datetime import datetime, timedelta
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import User
from .serializers import (
    RegisterSerializer, 
    LoginSerializer, 
    PasswordResetRequestSerializer,
    PasswordResetSerializer
)
from .authentication import generate_token


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """Register a new user"""
    serializer = RegisterSerializer(data=request.data)
    
    if not serializer.is_valid():
        errors = serializer.errors
        first_error = next(iter(errors.values()))[0]
        return Response({'error': str(first_error)}, status=status.HTTP_400_BAD_REQUEST)
    
    data = serializer.validated_data
    
    # Create user
    user = User.objects.create_user(
        email=data['email'],
        name=data['name'],
        password=data['password']
    )
    
    # Generate token
    token = generate_token(user)
    
    return Response({
        'message': 'User registered successfully',
        'token': token,
        'user': user.to_dict()
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """Login user"""
    serializer = LoginSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response({'error': 'Email and password are required'}, status=status.HTTP_400_BAD_REQUEST)
    
    data = serializer.validated_data
    
    try:
        user = User.objects.get(email=data['email'])
    except User.DoesNotExist:
        return Response({'error': 'Invalid email or password'}, status=status.HTTP_401_UNAUTHORIZED)
    
    if not user.check_password(data['password']):
        return Response({'error': 'Invalid email or password'}, status=status.HTTP_401_UNAUTHORIZED)
    
    if not user.is_active:
        return Response({'error': 'Account is disabled'}, status=status.HTTP_401_UNAUTHORIZED)
    
    # Generate token
    token = generate_token(user)
    
    return Response({
        'message': 'Login successful',
        'token': token,
        'user': user.to_dict()
    })


@api_view(['GET'])
def get_current_user(request):
    """Get current user info"""
    return Response({
        'user': request.user.to_dict()
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def request_password_reset(request):
    """Request password reset email"""
    serializer = PasswordResetRequestSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    email = serializer.validated_data['email']
    
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        # Don't reveal if email exists
        return Response({'message': 'If the email exists, a reset link has been sent'})
    
    # Generate reset token
    token = secrets.token_urlsafe(32)
    user.reset_token = token
    user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
    user.save()
    
    # Send email
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
    
    try:
        send_mail(
            subject='Reset Your Fint Password',
            message=f'Click the link to reset your password: {reset_url}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=f'''
                <h2>Reset Your Password</h2>
                <p>Hi {user.name},</p>
                <p>You requested to reset your password. Click the link below:</p>
                <p><a href="{reset_url}">Reset Password</a></p>
                <p>This link expires in 1 hour.</p>
                <p>If you didn't request this, please ignore this email.</p>
            '''
        )
    except Exception as e:
        print(f"Email error: {e}")
        # Don't fail the request if email fails
    
    return Response({'message': 'If the email exists, a reset link has been sent'})


@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password(request):
    """Reset password with token"""
    serializer = PasswordResetSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response({'error': 'Token and password are required'}, status=status.HTTP_400_BAD_REQUEST)
    
    data = serializer.validated_data
    
    try:
        user = User.objects.get(reset_token=data['token'])
    except User.DoesNotExist:
        return Response({'error': 'Invalid or expired reset token'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Check if token is expired
    if user.reset_token_expires and user.reset_token_expires < datetime.utcnow():
        return Response({'error': 'Reset token has expired'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Update password
    user.set_password(data['password'])
    user.reset_token = None
    user.reset_token_expires = None
    user.save()
    
    return Response({'message': 'Password reset successfully'})
