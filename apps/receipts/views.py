"""
Receipt views
"""
import base64
import os
import uuid
import csv
import io
from datetime import datetime
from django.conf import settings
from django.http import HttpResponse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Receipt
from .serializers import ReceiptCreateSerializer, ReceiptUpdateSerializer


@api_view(['GET', 'POST'])
def receipts_list(request):
    """List all receipts or create a new receipt"""
    if request.method == 'GET':
        return get_receipts(request)
    return create_receipt(request)


def get_receipts(request):
    """Get all receipts for current user"""
    user = request.user
    
    # Optional query parameters
    category = request.query_params.get('category')
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    limit = request.query_params.get('limit')
    
    queryset = Receipt.objects.filter(user=user)
    
    if category:
        queryset = queryset.filter(category=category)
    
    if start_date:
        queryset = queryset.filter(date__gte=start_date)
    
    if end_date:
        queryset = queryset.filter(date__lte=end_date)
    
    queryset = queryset.order_by('-date')
    
    if limit:
        try:
            queryset = queryset[:int(limit)]
        except ValueError:
            pass
    
    receipts = [r.to_dict() for r in queryset]
    return Response({'receipts': receipts})


def create_receipt(request):
    """Create a new receipt"""
    serializer = ReceiptCreateSerializer(data=request.data)
    
    if not serializer.is_valid():
        errors = serializer.errors
        first_error = next(iter(errors.values()))[0]
        return Response({'error': str(first_error)}, status=status.HTTP_400_BAD_REQUEST)
    
    data = serializer.validated_data
    
    # Handle image upload
    image_url = None
    image_data = data.get('imageData')
    
    if image_data:
        try:
            # Parse base64 data
            if ',' in image_data:
                header, image_data = image_data.split(',', 1)
            
            # Decode base64
            image_bytes = base64.b64decode(image_data)
            
            # Generate unique filename
            filename = f"{uuid.uuid4()}.jpg"
            
            # Create uploads directory if it doesn't exist
            os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
            
            # Save the image
            filepath = os.path.join(settings.MEDIA_ROOT, filename)
            with open(filepath, 'wb') as f:
                f.write(image_bytes)
            
            image_url = f"/uploads/{filename}"
        except Exception as e:
            print(f"Error saving image: {e}")
    
    # Create receipt
    receipt = Receipt.objects.create(
        user=request.user,
        name=data['name'],
        amount=data['amount'],
        category=data['category'],
        date=data['date'],
        image_url=image_url,
        notes=data.get('notes', '')
    )
    
    # Check budget alerts after adding a receipt
    alerts_created = check_and_create_budget_alerts(request.user, data['category'])
    
    response_data = {'receipt': receipt.to_dict()}
    if alerts_created:
        response_data['budget_alerts'] = alerts_created
    
    return Response(response_data, status=status.HTTP_201_CREATED)


def check_and_create_budget_alerts(user, category=None):
    """Check all relevant budgets and create alerts if thresholds are met"""
    from apps.users.models import Budget
    from apps.users.budget_views import check_budget_alerts
    
    alerts_created = []
    
    # Get all active budgets for this user
    budgets = Budget.objects.filter(user=user, is_active=True)
    
    for budget in budgets:
        # Check overall budgets (category=None) and category-specific budgets
        if budget.category is None or budget.category == category:
            alert = check_budget_alerts(user, budget)
            if alert:
                alerts_created.append(alert.to_dict())
    
    return alerts_created


@api_view(['GET', 'PUT', 'DELETE'])
def receipt_detail(request, receipt_id):
    """Get, update or delete a specific receipt"""
    try:
        receipt = Receipt.objects.get(id=receipt_id, user=request.user)
    except Receipt.DoesNotExist:
        return Response({'error': 'Receipt not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        return Response({'receipt': receipt.to_dict()})
    
    elif request.method == 'PUT':
        serializer = ReceiptUpdateSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({'error': 'Invalid data'}, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        
        if 'name' in data:
            receipt.name = data['name']
        if 'amount' in data:
            receipt.amount = data['amount']
        if 'category' in data:
            receipt.category = data['category']
        if 'date' in data:
            receipt.date = data['date']
        if 'imageUrl' in data:
            receipt.image_url = data['imageUrl'] if data['imageUrl'] else None
        if 'notes' in data:
            receipt.notes = data['notes']
        
        receipt.save()
        return Response({'receipt': receipt.to_dict()})
    
    elif request.method == 'DELETE':
        receipt.delete()
        return Response({'message': 'Receipt deleted successfully'})


@api_view(['GET'])
def export_receipts(request):
    """Export receipts as CSV or PDF"""
    user = request.user
    
    # Optional query parameters for filtering
    category = request.query_params.get('category')
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    format_type = request.query_params.get('format', 'csv')
    
    queryset = Receipt.objects.filter(user=user)
    
    if category:
        queryset = queryset.filter(category=category)
    
    if start_date:
        queryset = queryset.filter(date__gte=start_date)
    
    if end_date:
        queryset = queryset.filter(date__lte=end_date)
    
    queryset = queryset.order_by('-date')
    
    if format_type == 'csv':
        return export_csv(queryset, start_date, end_date)
    elif format_type == 'pdf':
        return export_pdf(queryset, start_date, end_date)
    elif format_type == 'json':
        return export_json(queryset)
    else:
        return Response({'error': 'Invalid format. Use csv, pdf, or json'}, status=status.HTTP_400_BAD_REQUEST)


def export_csv(queryset, start_date=None, end_date=None):
    """Export receipts as CSV file"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Date', 'Name', 'Category', 'Amount', 'Notes'])
    
    # Write data
    total = 0
    for receipt in queryset:
        writer.writerow([
            receipt.date.isoformat() if receipt.date else '',
            receipt.name,
            receipt.category,
            float(receipt.amount),
            receipt.notes or ''
        ])
        total += float(receipt.amount)
    
    # Write summary
    writer.writerow([])
    writer.writerow(['', '', 'Total:', total, ''])
    
    # Create response
    output.seek(0)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Add date range to filename if specified
    date_range = ''
    if start_date and end_date:
        date_range = f'_{start_date}_to_{end_date}'
    elif start_date:
        date_range = f'_from_{start_date}'
    elif end_date:
        date_range = f'_to_{end_date}'
    
    filename = f'receipts_export{date_range}_{timestamp}.csv'
    
    response = HttpResponse(output.getvalue(), content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    response['Access-Control-Expose-Headers'] = 'Content-Disposition'
    
    return response


def export_pdf(queryset, start_date=None, end_date=None):
    """Export receipts as PDF file"""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    
    # Create PDF buffer
    buffer = io.BytesIO()
    
    # Create document
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=12,
        textColor=colors.HexColor('#10b981')
    )
    elements.append(Paragraph('Fint - Receipt Export', title_style))
    
    # Date range subtitle
    if start_date or end_date:
        date_text = f"Period: {start_date or 'Beginning'} to {end_date or 'Present'}"
        elements.append(Paragraph(date_text, styles['Normal']))
    
    elements.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # Table data
    data = [['Date', 'Name', 'Category', 'Amount', 'Notes']]
    total = 0
    
    for receipt in queryset:
        data.append([
            receipt.date.strftime('%Y-%m-%d') if receipt.date else '',
            receipt.name[:30] + '...' if len(receipt.name) > 30 else receipt.name,
            receipt.category,
            f"${float(receipt.amount):.2f}",
            (receipt.notes or '')[:20] + '...' if receipt.notes and len(receipt.notes) > 20 else (receipt.notes or '')
        ])
        total += float(receipt.amount)
    
    # Add total row
    data.append(['', '', '', f"${total:.2f}", 'TOTAL'])
    
    # Create table
    table = Table(data, colWidths=[1.2*inch, 1.8*inch, 1.3*inch, 1*inch, 1.5*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#10b981')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -2), colors.white),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f0fdf4')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
    ]))
    elements.append(table)
    
    # Add summary
    elements.append(Spacer(1, 20))
    summary_text = f"Total Receipts: {len(list(queryset))} | Total Amount: ${total:.2f}"
    elements.append(Paragraph(summary_text, styles['Normal']))
    
    # Build PDF
    doc.build(elements)
    
    # Create response
    buffer.seek(0)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    date_range = ''
    if start_date and end_date:
        date_range = f'_{start_date}_to_{end_date}'
    elif start_date:
        date_range = f'_from_{start_date}'
    elif end_date:
        date_range = f'_to_{end_date}'
    
    filename = f'receipts_export{date_range}_{timestamp}.pdf'
    
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    response['Access-Control-Expose-Headers'] = 'Content-Disposition'
    
    return response


def export_json(queryset):
    """Export receipts as JSON"""
    receipts = [r.to_dict() for r in queryset]
    
    # Calculate summary
    total_amount = sum(r['amount'] for r in receipts)
    categories = {}
    for r in receipts:
        cat = r['category']
        categories[cat] = categories.get(cat, 0) + r['amount']
    
    export_data = {
        'export_date': datetime.now().isoformat(),
        'total_receipts': len(receipts),
        'total_amount': total_amount,
        'by_category': categories,
        'receipts': receipts
    }
    
    return Response(export_data)
