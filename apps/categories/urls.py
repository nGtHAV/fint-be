"""
Category URL routes
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.get_categories, name='categories_list'),
]
