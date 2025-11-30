"""
Authentication URL routes
"""
from django.urls import path
from . import views

urlpatterns = [
    path('register', views.register, name='register'),
    path('login', views.login, name='login'),
    path('me', views.get_current_user, name='current_user'),
    path('forgot-password', views.request_password_reset, name='forgot_password'),
    path('reset-password', views.reset_password, name='reset_password'),
]
