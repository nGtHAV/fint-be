"""
Receipt model
"""
from django.db import models
from django.conf import settings


class Receipt(models.Model):
    """Receipt model for tracking expenses"""
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='receipts'
    )
    name = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=100)
    date = models.DateField()
    image_url = models.CharField(max_length=500, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'receipts'
        ordering = ['-date', '-created_at']
    
    def __str__(self):
        return f"{self.name} - ${self.amount}"
    
    def to_dict(self):
        """Convert receipt to dictionary for API response"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'amount': float(self.amount),
            'category': self.category,
            'date': self.date.isoformat() if self.date else None,
            'image_url': self.image_url,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
