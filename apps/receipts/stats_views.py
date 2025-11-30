"""
Statistics views
"""
from datetime import datetime
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Receipt


@api_view(['GET'])
def get_stats_summary(request):
    """Get spending summary statistics"""
    user = request.user
    
    # Total spent
    total_spent = Receipt.objects.filter(user=user).aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    # This month spent
    current_month = datetime.now().replace(day=1).date()
    monthly_spent = Receipt.objects.filter(
        user=user,
        date__gte=current_month
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Total receipts count
    total_receipts = Receipt.objects.filter(user=user).count()
    
    # Spending by category
    categories = Receipt.objects.filter(user=user).values('category').annotate(
        total=Sum('amount')
    ).order_by('-total')
    
    categories_list = [
        {'category': c['category'], 'total': float(c['total'])}
        for c in categories
    ]
    
    return Response({
        'total_spent': float(total_spent),
        'monthly_spent': float(monthly_spent),
        'total_receipts': total_receipts,
        'categories': categories_list,
        'top_category': categories_list[0]['category'] if categories_list else None
    })


@api_view(['GET'])
def get_monthly_stats(request):
    """Get monthly spending breakdown"""
    user = request.user
    
    monthly_data = Receipt.objects.filter(user=user).annotate(
        month=TruncMonth('date')
    ).values('month').annotate(
        total=Sum('amount')
    ).order_by('-month')[:12]
    
    result = [
        {
            'month': m['month'].strftime('%Y-%m') if m['month'] else None,
            'total': float(m['total'])
        }
        for m in monthly_data
    ]
    
    return Response({'monthly': result})
