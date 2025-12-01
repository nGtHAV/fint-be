"""
Budget URL routes
"""
from django.urls import path
from . import budget_views

urlpatterns = [
    path('', budget_views.budget_list, name='budget_list'),
    path('<int:budget_id>/', budget_views.budget_detail, name='budget_detail'),
    path('summary/', budget_views.budget_summary, name='budget_summary'),
    path('alerts/', budget_views.budget_alerts_list, name='budget_alerts'),
    path('alerts/<int:alert_id>/read/', budget_views.mark_alert_read, name='mark_alert_read'),
    path('alerts/read-all/', budget_views.mark_all_alerts_read, name='mark_all_alerts_read'),
]
