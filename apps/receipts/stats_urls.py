"""
Statistics URL routes
"""
from django.urls import path
from . import stats_views

urlpatterns = [
    path('summary', stats_views.get_stats_summary, name='stats_summary'),
    path('monthly', stats_views.get_monthly_stats, name='stats_monthly'),
]
