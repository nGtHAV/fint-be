"""
Receipt URL routes
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.receipts_list, name='receipts_list'),
    path('export/', views.export_receipts, name='export_receipts'),
    path('<int:receipt_id>/', views.receipt_detail, name='receipt_detail'),
]
