"""
Receipt URL routes
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.receipts_list, name='receipts_list'),
    path('<int:receipt_id>', views.receipt_detail, name='receipt_detail'),
]
