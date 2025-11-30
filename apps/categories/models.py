"""
Category model
"""
from django.db import models


class Category(models.Model):
    """Category model for expense types"""
    
    name = models.CharField(max_length=100, unique=True)
    icon = models.CharField(max_length=50, blank=True, null=True)
    color = models.CharField(max_length=20, blank=True, null=True)
    
    class Meta:
        db_table = 'categories'
        verbose_name_plural = 'categories'
    
    def __str__(self):
        return self.name
    
    def to_dict(self):
        """Convert category to dictionary for API response"""
        return {
            'id': self.id,
            'name': self.name,
            'icon': self.icon,
            'color': self.color,
        }
