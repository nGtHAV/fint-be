"""
User profile URL routes
"""
from django.urls import path
from . import profile_views

urlpatterns = [
    path('profile', profile_views.update_profile, name='update_profile'),
    path('password', profile_views.change_password, name='change_password'),
    path('delete', profile_views.delete_account, name='delete_account'),
]
