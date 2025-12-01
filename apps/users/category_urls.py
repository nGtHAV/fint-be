"""
Category URL routes
"""
from django.urls import path
from . import category_views

urlpatterns = [
    path('', category_views.category_list, name='category_list'),
    path('custom/', category_views.create_custom_category, name='create_custom_category'),
    path('custom/<int:category_id>/', category_views.custom_category_detail, name='custom_category_detail'),
    path('custom/<int:category_id>/migrate/', category_views.migrate_category_receipts, name='migrate_category'),
    path('custom/<int:category_id>/count/', category_views.category_receipt_count, name='category_receipt_count'),
]
