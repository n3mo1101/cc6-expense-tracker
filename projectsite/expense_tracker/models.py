import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


# Base model with common fields for all models
class BaseModel(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True


# Extended user profile information
class UserProfile(BaseModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,  # References django.contrib.auth.User
        on_delete=models.CASCADE,
        related_name='profile'
    )
    profile_picture = models.CharField(max_length=500, blank=True, null=True)
    default_currency = models.CharField(max_length=3, default='PHP')
    timezone = models.CharField(max_length=50, default='UTC')
    
    class Meta:
        db_table = 'user_profile'
    
    def __str__(self):
        return f"{self.user.username}'s Profile"


# Categories for expenses (both predefined and user-defined)
class ExpenseCategory(BaseModel):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    is_predefined = models.BooleanField(default=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        help_text="NULL for predefined categories, user for custom categories"
    )
    
    class Meta:
        db_table = 'expense_category'
        indexes = [
            models.Index(fields=['is_predefined']),
        ]
        verbose_name = "Expense Category"
        verbose_name_plural = "Expense Categories"
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # If it's predefined, ensure user is NULL
        if self.is_predefined:
            self.user = None
        super().save(*args, **kwargs)


# Budgets created by users
class Budget(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='budgets'
    )
    name = models.CharField(max_length=255)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency_code = models.CharField(max_length=3, default='PHP')
    start_date = models.DateField()
    end_date = models.DateField()
    description = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'budget'
        indexes = [
            models.Index(fields=['start_date', 'end_date']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.user.username}"
    
    @property
    def is_active(self):
    # Check if budget is currently active
        today = timezone.now().date()
        return self.start_date <= today <= self.end_date


# Categories allocated within a budget
class BudgetCategory(BaseModel):
    budget = models.ForeignKey(
        Budget,
        on_delete=models.CASCADE,
        related_name='budget_categories'
    )
    category = models.ForeignKey(
        ExpenseCategory,
        on_delete=models.CASCADE,
        related_name='budget_allocations'
    )
    allocated_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        db_table = 'budget_category'
        unique_together = ['budget', 'category']
        verbose_name = "Budget Category"
        verbose_name_plural = "Budget Categories"
    
    def __str__(self):
        return f"{self.budget.name} - {self.category.name}: {self.allocated_amount}"


# Expense transactions
class Expense(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='expenses'
    )
    category = models.ForeignKey(
        ExpenseCategory,
        on_delete=models.RESTRICT,
        related_name='expenses'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency_code = models.CharField(max_length=3, default='PHP')
    description = models.TextField(blank=True, null=True)
    expense_date = models.DateField()
    is_recurring = models.BooleanField(default=False)
    recurrence_rule = models.CharField(max_length=500, blank=True, null=True)
    parent_expense = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='recurring_instances'
    )
    
    class Meta:
        db_table = 'expense'
        indexes = [
            models.Index(fields=['public_id']),
            models.Index(fields=['expense_date']),
            models.Index(fields=['is_recurring']),
        ]
        ordering = ['-expense_date', '-created_at']
    
    def __str__(self):
        return f"{self.amount} {self.currency_code} - {self.category.name} - {self.user.username}"
    
    @property
    def is_recurring_instance(self):
    # Check if this expense is part of a recurring series
        return self.parent_expense is not None


# Income transactions
class Income(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='incomes'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency_code = models.CharField(max_length=3, default='PHP')
    source = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    income_date = models.DateField()
    is_recurring = models.BooleanField(default=False)
    recurrence_rule = models.CharField(max_length=500, blank=True, null=True)
    
    class Meta:
        db_table = 'income'
        indexes = [
            models.Index(fields=['public_id']),
            models.Index(fields=['income_date']),
        ]
        ordering = ['-income_date', '-created_at']
    
    def __str__(self):
        return f"{self.amount} {self.currency_code} - {self.source} - {self.user.username}"


# Signal to automatically create UserProfile when User is created
from django.db.models.signals import post_save
from django.dispatch import receiver

# Create user profile only when user is created
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created and not UserProfile.objects.filter(user=instance).exists():
        UserProfile.objects.create(user=instance)

# Save user profile if it exists
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()

# Function to create predefined expense categories
def create_predefined_categories():
    predefined_categories = [
        ('Food', 'Groceries, restaurants, coffee shops'),
        ('Housing', 'Rent, mortgage, utilities'),
        ('Transportation', 'Gas, public transport, car maintenance'),
        ('Entertainment', 'Movies, concerts, hobbies'),
        ('Healthcare', 'Doctor visits, medication, insurance'),
        ('Shopping', 'Clothing, electronics, personal items'),
        ('Education', 'Tuition, books, courses'),
        ('Utilities', 'Electricity, water, internet, phone'),
    ]
    
    for name, description in predefined_categories:
        ExpenseCategory.objects.get_or_create(
            name=name,
            description=description,
            is_predefined=True,
            user=None
        )