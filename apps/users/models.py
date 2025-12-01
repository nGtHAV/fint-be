"""
Custom User model
"""
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from decimal import Decimal


class UserManager(BaseUserManager):
    """Custom user manager"""
    
    def create_user(self, email, name, password=None, **extra_fields):
        """Create and save a regular user"""
        if not email:
            raise ValueError('Email is required')
        
        email = self.normalize_email(email)
        user = self.model(email=email, name=name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, name, password=None, **extra_fields):
        """Create and save a superuser"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, name, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model using email as username"""
    
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255)
    avatar_url = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Password reset token
    reset_token = models.CharField(max_length=255, blank=True, null=True)
    reset_token_expires = models.DateTimeField(blank=True, null=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']
    
    class Meta:
        db_table = 'users'
    
    def __str__(self):
        return self.email
    
    def to_dict(self):
        """Convert user to dictionary for API response"""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'avatar_url': self.avatar_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class Budget(models.Model):
    """Budget model for spending limits"""
    
    PERIOD_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]
    
    user = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='budgets'
    )
    period = models.CharField(max_length=10, choices=PERIOD_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=100, blank=True, null=True)  # None = all categories
    is_active = models.BooleanField(default=True)
    alert_threshold = models.IntegerField(default=80)  # Alert at 80% of budget
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'budgets'
        unique_together = ['user', 'period', 'category']
    
    def __str__(self):
        cat = self.category or 'All'
        return f"{self.user.email} - {self.period} budget: ${self.amount} ({cat})"
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'period': self.period,
            'amount': float(self.amount),
            'category': self.category,
            'is_active': self.is_active,
            'alert_threshold': self.alert_threshold,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class BudgetAlert(models.Model):
    """Budget alert notifications"""
    
    ALERT_TYPE_CHOICES = [
        ('warning', 'Warning'),  # Approaching limit
        ('exceeded', 'Exceeded'),  # Over limit
    ]
    
    user = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='budget_alerts'
    )
    budget = models.ForeignKey(
        Budget,
        on_delete=models.CASCADE,
        related_name='alerts'
    )
    alert_type = models.CharField(max_length=10, choices=ALERT_TYPE_CHOICES)
    message = models.TextField()
    current_spent = models.DecimalField(max_digits=10, decimal_places=2)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'budget_alerts'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.alert_type}: {self.message[:50]}"
    
    def to_dict(self):
        return {
            'id': self.id,
            'budget_id': self.budget_id,
            'alert_type': self.alert_type,
            'message': self.message,
            'current_spent': float(self.current_spent),
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class UserCategory(models.Model):
    """Custom categories created by users"""
    
    user = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='custom_categories'
    )
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, blank=True, null=True)
    color = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_categories'
        unique_together = ['user', 'name']
    
    def __str__(self):
        return f"{self.user.email} - {self.name}"
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'icon': self.icon,
            'color': self.color,
            'is_custom': True,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
