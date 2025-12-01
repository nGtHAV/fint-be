"""
Budget API views
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from .models import Budget, BudgetAlert, User


def get_period_date_range(period):
    """Get date range for the given period"""
    today = timezone.now().date()
    
    if period == 'daily':
        start_date = today
        end_date = today
    elif period == 'weekly':
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)
    elif period == 'monthly':
        start_date = today.replace(day=1)
        if today.month == 12:
            end_date = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end_date = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
    else:
        start_date = today
        end_date = today
    
    return start_date, end_date


def calculate_spent(user, period, category=None):
    """Calculate amount spent in the given period"""
    from apps.receipts.models import Receipt
    
    start_date, end_date = get_period_date_range(period)
    
    queryset = Receipt.objects.filter(
        user=user,
        date__gte=start_date,
        date__lte=end_date
    )
    
    if category:
        queryset = queryset.filter(category=category)
    
    total = queryset.aggregate(total=Sum('amount'))['total']
    return total or Decimal('0.00')


def check_budget_alerts(user, budget):
    """Check if budget alerts need to be created"""
    spent = calculate_spent(user, budget.period, budget.category)
    percentage = (spent / budget.amount * 100) if budget.amount > 0 else 0
    
    # Check if we already sent an alert today for this budget
    today = timezone.now().date()
    existing_alert = BudgetAlert.objects.filter(
        user=user,
        budget=budget,
        created_at__date=today
    ).exists()
    
    if existing_alert:
        return None
    
    alert = None
    if percentage >= 100:
        category_text = f" for {budget.category}" if budget.category else ""
        alert = BudgetAlert.objects.create(
            user=user,
            budget=budget,
            alert_type='exceeded',
            message=f"You have exceeded your {budget.period} budget{category_text}! Spent ${spent:.2f} of ${budget.amount:.2f}",
            current_spent=spent
        )
    elif percentage >= budget.alert_threshold:
        category_text = f" for {budget.category}" if budget.category else ""
        alert = BudgetAlert.objects.create(
            user=user,
            budget=budget,
            alert_type='warning',
            message=f"You have used {percentage:.0f}% of your {budget.period} budget{category_text}. Spent ${spent:.2f} of ${budget.amount:.2f}",
            current_spent=spent
        )
    
    return alert


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def budget_list(request):
    """List all budgets or create a new one"""
    if request.method == 'GET':
        budgets = Budget.objects.filter(user=request.user)
        
        # Include current spending info
        budget_data = []
        for budget in budgets:
            data = budget.to_dict()
            data['current_spent'] = float(calculate_spent(request.user, budget.period, budget.category))
            data['percentage'] = (data['current_spent'] / float(budget.amount) * 100) if budget.amount > 0 else 0
            budget_data.append(data)
        
        return Response(budget_data)
    
    elif request.method == 'POST':
        period = request.data.get('period')
        amount = request.data.get('amount')
        category = request.data.get('category')  # Optional
        alert_threshold = request.data.get('alert_threshold', 80)
        
        if not period or period not in ['daily', 'weekly', 'monthly']:
            return Response(
                {'error': 'Valid period is required (daily, weekly, monthly)'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not amount or float(amount) <= 0:
            return Response(
                {'error': 'Valid amount is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if budget already exists
        existing = Budget.objects.filter(
            user=request.user,
            period=period,
            category=category
        ).first()
        
        if existing:
            # Update existing budget
            existing.amount = Decimal(str(amount))
            existing.alert_threshold = alert_threshold
            existing.is_active = True
            existing.save()
            budget = existing
        else:
            # Create new budget
            budget = Budget.objects.create(
                user=request.user,
                period=period,
                amount=Decimal(str(amount)),
                category=category,
                alert_threshold=alert_threshold
            )
        
        data = budget.to_dict()
        data['current_spent'] = float(calculate_spent(request.user, budget.period, budget.category))
        data['percentage'] = (data['current_spent'] / float(budget.amount) * 100) if budget.amount > 0 else 0
        
        return Response(data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def budget_detail(request, budget_id):
    """Get, update, or delete a budget"""
    try:
        budget = Budget.objects.get(id=budget_id, user=request.user)
    except Budget.DoesNotExist:
        return Response(
            {'error': 'Budget not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    if request.method == 'GET':
        data = budget.to_dict()
        data['current_spent'] = float(calculate_spent(request.user, budget.period, budget.category))
        data['percentage'] = (data['current_spent'] / float(budget.amount) * 100) if budget.amount > 0 else 0
        return Response(data)
    
    elif request.method == 'PUT':
        if 'amount' in request.data:
            budget.amount = Decimal(str(request.data['amount']))
        if 'alert_threshold' in request.data:
            budget.alert_threshold = request.data['alert_threshold']
        if 'is_active' in request.data:
            budget.is_active = request.data['is_active']
        
        budget.save()
        
        data = budget.to_dict()
        data['current_spent'] = float(calculate_spent(request.user, budget.period, budget.category))
        data['percentage'] = (data['current_spent'] / float(budget.amount) * 100) if budget.amount > 0 else 0
        return Response(data)
    
    elif request.method == 'DELETE':
        budget.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def budget_alerts_list(request):
    """List all budget alerts for the user"""
    alerts = BudgetAlert.objects.filter(user=request.user)[:50]
    return Response([alert.to_dict() for alert in alerts])


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_alert_read(request, alert_id):
    """Mark a budget alert as read"""
    try:
        alert = BudgetAlert.objects.get(id=alert_id, user=request.user)
        alert.is_read = True
        alert.save()
        return Response(alert.to_dict())
    except BudgetAlert.DoesNotExist:
        return Response(
            {'error': 'Alert not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_all_alerts_read(request):
    """Mark all budget alerts as read"""
    BudgetAlert.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return Response({'message': 'All alerts marked as read'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def budget_summary(request):
    """Get budget summary with spending status"""
    budgets = Budget.objects.filter(user=request.user, is_active=True)
    
    summary = {
        'daily': None,
        'weekly': None,
        'monthly': None,
    }
    
    for budget in budgets:
        if budget.category is None:  # Overall budget
            spent = calculate_spent(request.user, budget.period)
            percentage = (spent / budget.amount * 100) if budget.amount > 0 else 0
            
            summary[budget.period] = {
                'budget': float(budget.amount),
                'spent': float(spent),
                'remaining': float(budget.amount - spent),
                'percentage': float(percentage),
                'alert_threshold': budget.alert_threshold,
                'status': 'exceeded' if percentage >= 100 else ('warning' if percentage >= budget.alert_threshold else 'ok')
            }
    
    # Get unread alerts count
    unread_alerts = BudgetAlert.objects.filter(user=request.user, is_read=False).count()
    
    return Response({
        'budgets': summary,
        'unread_alerts': unread_alerts
    })
