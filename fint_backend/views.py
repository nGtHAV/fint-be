"""
Health check and utility views
"""
from django.http import JsonResponse
from datetime import datetime


def health_check(request):
    """Health check endpoint"""
    return JsonResponse({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })
