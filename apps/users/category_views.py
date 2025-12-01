"""
Custom Category API views
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import transaction

from .models import UserCategory


# Default system categories
DEFAULT_CATEGORIES = [
    {'name': 'Food & Dining', 'icon': 'utensils', 'color': 'orange'},
    {'name': 'Shopping', 'icon': 'shopping-bag', 'color': 'pink'},
    {'name': 'Transportation', 'icon': 'car', 'color': 'blue'},
    {'name': 'Entertainment', 'icon': 'film', 'color': 'purple'},
    {'name': 'Healthcare', 'icon': 'heart', 'color': 'red'},
    {'name': 'Bills & Utilities', 'icon': 'file-text', 'color': 'gray'},
    {'name': 'Education', 'icon': 'book', 'color': 'indigo'},
    {'name': 'Travel', 'icon': 'plane', 'color': 'cyan'},
    {'name': 'Groceries', 'icon': 'shopping-cart', 'color': 'green'},
    {'name': 'Personal Care', 'icon': 'smile', 'color': 'rose'},
    {'name': 'Gifts & Donations', 'icon': 'gift', 'color': 'amber'},
    {'name': 'Investments', 'icon': 'trending-up', 'color': 'emerald'},
    {'name': 'Insurance', 'icon': 'shield', 'color': 'slate'},
    {'name': 'Subscriptions', 'icon': 'repeat', 'color': 'violet'},
    {'name': 'Home', 'icon': 'home', 'color': 'brown'},
]


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def category_list(request):
    """List all categories (default + user's custom categories)"""
    # Get user's custom categories
    custom_categories = UserCategory.objects.filter(user=request.user)
    
    # Combine default and custom categories
    categories = []
    
    # Add default categories
    for cat in DEFAULT_CATEGORIES:
        categories.append({
            'id': None,
            'name': cat['name'],
            'icon': cat['icon'],
            'color': cat['color'],
            'is_custom': False,
        })
    
    # Add custom categories
    for cat in custom_categories:
        categories.append(cat.to_dict())
    
    # Add "Other" option at the end
    categories.append({
        'id': None,
        'name': 'Other',
        'icon': 'more-horizontal',
        'color': 'gray',
        'is_custom': False,
        'is_other': True,
    })
    
    return Response(categories)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_custom_category(request):
    """Create a new custom category"""
    name = request.data.get('name', '').strip()
    icon = request.data.get('icon', 'tag')
    color = request.data.get('color', 'gray')
    
    if not name:
        return Response(
            {'error': 'Category name is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if len(name) > 100:
        return Response(
            {'error': 'Category name must be 100 characters or less'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if category already exists (case-insensitive)
    if UserCategory.objects.filter(user=request.user, name__iexact=name).exists():
        return Response(
            {'error': 'You already have a category with this name'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if it's a default category name
    default_names = [cat['name'].lower() for cat in DEFAULT_CATEGORIES]
    if name.lower() in default_names:
        return Response(
            {'error': 'This is a default category name'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    category = UserCategory.objects.create(
        user=request.user,
        name=name,
        icon=icon,
        color=color
    )
    
    return Response(category.to_dict(), status=status.HTTP_201_CREATED)


@api_view(['PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def custom_category_detail(request, category_id):
    """Update or delete a custom category"""
    try:
        category = UserCategory.objects.get(id=category_id, user=request.user)
    except UserCategory.DoesNotExist:
        return Response(
            {'error': 'Category not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    if request.method == 'PUT':
        if 'name' in request.data:
            name = request.data['name'].strip()
            if name and name != category.name:
                # Check for duplicates
                if UserCategory.objects.filter(user=request.user, name__iexact=name).exclude(id=category_id).exists():
                    return Response(
                        {'error': 'You already have a category with this name'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                category.name = name
        
        if 'icon' in request.data:
            category.icon = request.data['icon']
        if 'color' in request.data:
            category.color = request.data['color']
        
        category.save()
        return Response(category.to_dict())
    
    elif request.method == 'DELETE':
        # Check if migrate_to is provided
        migrate_to = request.data.get('migrate_to')
        
        if migrate_to:
            # Migrate receipts to another category
            from apps.receipts.models import Receipt
            Receipt.objects.filter(
                user=request.user,
                category=category.name
            ).update(category=migrate_to)
        
        category.delete()
        return Response({'message': 'Category deleted successfully'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def migrate_category_receipts(request, category_id):
    """Migrate all receipts from one category to another"""
    try:
        category = UserCategory.objects.get(id=category_id, user=request.user)
    except UserCategory.DoesNotExist:
        return Response(
            {'error': 'Category not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    migrate_to = request.data.get('migrate_to')
    if not migrate_to:
        return Response(
            {'error': 'migrate_to category is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    from apps.receipts.models import Receipt
    
    count = Receipt.objects.filter(
        user=request.user,
        category=category.name
    ).update(category=migrate_to)
    
    return Response({
        'message': f'Migrated {count} receipts from "{category.name}" to "{migrate_to}"',
        'count': count
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def category_receipt_count(request, category_id):
    """Get the count of receipts in a custom category"""
    try:
        category = UserCategory.objects.get(id=category_id, user=request.user)
    except UserCategory.DoesNotExist:
        return Response(
            {'error': 'Category not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    from apps.receipts.models import Receipt
    
    count = Receipt.objects.filter(
        user=request.user,
        category=category.name
    ).count()
    
    return Response({
        'category': category.name,
        'receipt_count': count
    })
