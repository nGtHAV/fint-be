"""
Receipt serializers
"""
from rest_framework import serializers
from .models import Receipt


class ReceiptSerializer(serializers.ModelSerializer):
    """Receipt serializer for API responses"""
    
    class Meta:
        model = Receipt
        fields = ['id', 'user_id', 'name', 'amount', 'category', 'date', 'image_url', 'notes', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user_id', 'created_at', 'updated_at']


class ReceiptCreateSerializer(serializers.Serializer):
    """Serializer for creating receipts"""
    name = serializers.CharField(max_length=255)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    category = serializers.CharField(max_length=100)
    date = serializers.DateField()
    imageData = serializers.CharField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)


class ReceiptUpdateSerializer(serializers.Serializer):
    """Serializer for updating receipts"""
    name = serializers.CharField(max_length=255, required=False)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    category = serializers.CharField(max_length=100, required=False)
    date = serializers.DateField(required=False)
    imageUrl = serializers.CharField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)
