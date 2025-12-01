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
    
    return Response({'receipt': receipt.to_dict()}, status=status.HTTP_201_CREATED)


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
    """Export receipts as CSV"""
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
        return export_csv(queryset)
    elif format_type == 'json':
        return export_json(queryset)
    else:
        return Response({'error': 'Invalid format. Use csv or json'}, status=status.HTTP_400_BAD_REQUEST)


def export_csv(queryset):
    """Export receipts as CSV file"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Date', 'Name', 'Category', 'Amount', 'Notes'])
    
    # Write data
    for receipt in queryset:
        writer.writerow([
            receipt.date.isoformat() if receipt.date else '',
            receipt.name,
            receipt.category,
            float(receipt.amount),
            receipt.notes or ''
        ])
    
    # Create response
    output.seek(0)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'receipts_export_{timestamp}.csv'
    
    response = HttpResponse(output.getvalue(), content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
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
