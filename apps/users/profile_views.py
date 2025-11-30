"""
User profile views
"""
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import User
from .serializers import PasswordChangeSerializer, ProfileUpdateSerializer


@api_view(['PUT'])
def update_profile(request):
    """Update user profile"""
    serializer = ProfileUpdateSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response({'error': 'Invalid data'}, status=status.HTTP_400_BAD_REQUEST)
    
    user = request.user
    data = serializer.validated_data
    
    if 'name' in data:
        user.name = data['name']
    
    if 'avatar_url' in data:
        user.avatar_url = data['avatar_url'] if data['avatar_url'] else None
    
    user.save()
    
    return Response({'user': user.to_dict()})


@api_view(['PUT'])
def change_password(request):
    """Change user password"""
    serializer = PasswordChangeSerializer(data=request.data)
    
    if not serializer.is_valid():
        errors = serializer.errors
        first_error = next(iter(errors.values()))[0]
        return Response({'error': str(first_error)}, status=status.HTTP_400_BAD_REQUEST)
    
    data = serializer.validated_data
    user = request.user
    
    if not user.check_password(data['currentPassword']):
        return Response({'error': 'Current password is incorrect'}, status=status.HTTP_401_UNAUTHORIZED)
    
    user.set_password(data['newPassword'])
    user.save()
    
    return Response({'message': 'Password changed successfully'})


@api_view(['DELETE'])
def delete_account(request):
    """Delete user account and all data"""
    user = request.user
    
    # Delete all user's receipts (cascade should handle this)
    user.delete()
    
    return Response({'message': 'Account deleted successfully'})
