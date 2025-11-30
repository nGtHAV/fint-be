"""
Initial data for categories
Run after migrations: python manage.py loaddata initial_categories
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fint_backend.settings')
django.setup()

from apps.categories.models import Category


def create_default_categories():
    """Create default expense categories"""
    default_categories = [
        ('Food & Dining', 'utensils', '#f59e0b'),
        ('Transportation', 'car', '#3b82f6'),
        ('Entertainment', 'film', '#8b5cf6'),
        ('Shopping', 'shopping-bag', '#ec4899'),
        ('Healthcare', 'heart', '#ef4444'),
        ('Utilities', 'zap', '#6366f1'),
        ('Education', 'book', '#14b8a6'),
        ('Other', 'more-horizontal', '#6b7280'),
    ]
    
    for name, icon, color in default_categories:
        Category.objects.get_or_create(
            name=name,
            defaults={'icon': icon, 'color': color}
        )
    
    print("✅ Default categories created")


if __name__ == '__main__':
    create_default_categories()
