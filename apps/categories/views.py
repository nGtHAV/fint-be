"""
Category views
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Category


@api_view(['GET'])
@permission_classes([AllowAny])
def get_categories(request):
    """Get all available categories"""
    categories = Category.objects.all()
    return Response({
        'categories': [c.to_dict() for c in categories]
    })
