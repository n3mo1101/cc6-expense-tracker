from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid


# Abstract base model with common fields for all models
class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True 
        ordering = ['-created_at']


# Extends Django's built in User model for additional profile settings
class UserProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    primary_currency = models.CharField(max_length=3, default='PHP', help_text="ISO 4217 currency code")
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_profile'
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return f"{self.user.username}'s Profile ({self.primary_currency})"


# Wallet model for tracking user balances in different currencies
class Wallet(BaseModel):
    currency = models.CharField(max_length=3, help_text="ISO 4217 currency code")
    balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    is_primary = models.BooleanField(default=False)

    class Meta:
        db_table = 'wallet'
        unique_together = ['user', 'currency']
        indexes = [
            models.Index(fields=['user', 'currency']),
            models.Index(fields=['user', 'is_primary']),
        ]

    def __str__(self):
        primary_tag = " (Primary)" if self.is_primary else ""
        return f"{self.user.username} - {self.currency} {self.balance}{primary_tag}"

    def save(self, *args, **kwargs):
        # Ensure only one primary wallet per user.
        if self.is_primary:
            # Set all other wallets for this user to non-primary
            Wallet.objects.filter(user=self.user, is_primary=True).update(is_primary=False)
        
        super().save(*args, **kwargs)


# Template for recurring income/expenses.
# Auto-generates transaction entries based on recurrence pattern.
class RecurringTransaction(BaseModel):
    TRANSACTION_TYPES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
    ]
    RECURRENCE_PATTERNS = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
        ('custom', 'Custom'),
    ]
    type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    source_or_category = models.CharField(max_length=100, help_text="Source for income, Category for expense")
    
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    currency = models.CharField(max_length=3)
    description = models.TextField(null=True, blank=True)
    
    recurrence_pattern = models.CharField(max_length=10, choices=RECURRENCE_PATTERNS)
    custom_interval_days = models.IntegerField(null=True, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True, help_text="Null = no end date")
    last_generated_date = models.DateField(null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    budget = models.ForeignKey(
        'Budget',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recurring_transactions',
        help_text="For expenses only"
    )

    class Meta:
        db_table = 'recurring_transaction'
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['user', 'type']),
            models.Index(fields=['last_generated_date']),
        ]

    def __str__(self):
        return f"{self.get_type_display()} - {self.source_or_category} ({self.recurrence_pattern})"


# Model for income transactions.
class Income(BaseModel):
    TRANSACTION_STATUS = [
        ('pending', 'Pending'),
        ('complete', 'Complete'),
    ]

    source = models.CharField(max_length=100, help_text="e.g. Salary, Investment")
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    currency = models.CharField(max_length=3)

    # Currency conversion fields
    converted_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    
    transaction_date = models.DateField()
    description = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=TRANSACTION_STATUS, default='pending')

    # Income transactions can be linked to one recurring transaction (or none).
    recurring_transaction = models.ForeignKey(
        RecurringTransaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='generated_incomes'
    )

    class Meta:
        db_table = 'income'
        indexes = [
            models.Index(fields=['user', 'transaction_date']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['recurring_transaction']),
        ]
        ordering = ['-transaction_date', '-created_at']

    def __str__(self):
        return f"{self.source} - {self.currency} {self.amount} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        # Auto-calculate converted_amount if currency differs from primary.
        if self.currency != self.user.profile.primary_currency and self.exchange_rate:
            self.converted_amount = self.amount * self.exchange_rate
        elif self.currency == self.user.profile.primary_currency:
            self.converted_amount = self.amount
        super().save(*args, **kwargs)


# Budget model to track user spending limits
class Budget(BaseModel):
    BUDGET_TYPES = [
        ('manual', 'Manual'),
        ('category_filter', 'Category Filter'),
    ]
    RECURRENCE_PATTERNS = [
        ('one_time', 'One Time'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]

    name = models.CharField(max_length=200)
    budget_type = models.CharField(max_length=20, choices=BUDGET_TYPES)
    
    """
    This model manages spending budgets with two types: 
    1. Manual: Expenses explicitly linked   
    2. Category Filter: Auto-subtract expenses with matching categories 
    """

    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    currency = models.CharField(max_length=3)
    spent_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))

    recurrence_pattern = models.CharField(max_length=10, choices=RECURRENCE_PATTERNS)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True, help_text="For one_time budgets")
    last_reset_date = models.DateField(null=True, blank=True, help_text="For recurring budgets")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')

    # JSON field for category filters (for category_filter type)
    category_filters = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = 'budget'
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['user', 'recurrence_pattern']),
        ]

    def __str__(self):
        return f"{self.name} - {self.currency} {self.spent_amount}/{self.amount}"

    @property
    def remaining_amount(self):
        # Calculate remaining budget.
        return self.amount - self.spent_amount

    @property
    def percentage_used(self):
        # Calculate percentage of budget used.
        if self.amount == 0:
            return 0
        return (self.spent_amount / self.amount) * 100


# Model for expense transactions.
class Expense(BaseModel):
    TRANSACTION_STATUS = [
        ('pending', 'Pending'),
        ('complete', 'Complete'),
    ]

    category = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    currency = models.CharField(max_length=3)

    # Currency conversion fields
    converted_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, help_text="Amount in user's primary currency")
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)

    transaction_date = models.DateField()
    description = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=TRANSACTION_STATUS, default='pending')

    budget = models.ForeignKey(
        Budget,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='expenses',
        help_text="Optional: link to one budget"
    )

    # Expense transactions can be linked to one budget (or none).
    recurring_transaction = models.ForeignKey(
        RecurringTransaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='generated_expenses'
    )

    class Meta:
        db_table = 'expense'
        indexes = [
            models.Index(fields=['user', 'transaction_date']),
            models.Index(fields=['user', 'category']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['budget']),
            models.Index(fields=['recurring_transaction']),
        ]
        ordering = ['-transaction_date', '-created_at']

    def __str__(self):
        return f"{self.category} - {self.currency} {self.amount} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        # Auto-calculate converted_amount if currency differs from primary.
        if self.currency != self.user.profile.primary_currency and self.exchange_rate:
            self.converted_amount = self.amount * self.exchange_rate
        elif self.currency == self.user.profile.primary_currency:
            self.converted_amount = self.amount
        super().save(*args, **kwargs)


from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    # Automatically create UserProfile when User is created.
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=UserProfile)
def create_primary_wallet(sender, instance, created, **kwargs):
    # Automatically create primary wallet when UserProfile is created.
    if created:
        Wallet.objects.create(
            user=instance.user,
            currency=instance.primary_currency,
            is_primary=True
        )
        
@receiver(pre_save, sender=Income)
def handle_income_status_change(sender, instance, **kwargs):
    # Update wallet when income status changes to complete.
    if instance.pk:  # Only for updates, not new records
        try:
            old_instance = Income.objects.get(pk=instance.pk)
            # If status changed from pending to complete
            if old_instance.status == 'pending' and instance.status == 'complete':
                wallet = Wallet.objects.get(
                    user=instance.user,
                    currency=instance.user.profile.primary_currency
                )
                amount_to_add = instance.converted_amount or instance.amount
                wallet.balance += amount_to_add
                wallet.save()
        except Income.DoesNotExist:
            pass

@receiver(pre_save, sender=Expense)
def handle_expense_status_change(sender, instance, **kwargs):
    # Update wallet and budget when expense status changes to complete.
    if instance.pk:  # Only for updates
        try:
            old_instance = Expense.objects.get(pk=instance.pk)
            # If status changed from pending to complete
            if old_instance.status == 'pending' and instance.status == 'complete':
                # Update wallet
                wallet = Wallet.objects.get(
                user=instance.user,
                currency=instance.user.profile.primary_currency
                )
                amount_to_subtract = instance.converted_amount or instance.amount
                wallet.balance -= amount_to_subtract
                wallet.save()

            # Update budget (if linked)
            if instance.budget:
                instance.budget.spent_amount += amount_to_subtract
                instance.budget.save()
            else:
                # Check for category_filter budgets
                category_budgets = Budget.objects.filter(
                    user=instance.user,
                    budget_type='category_filter',
                    status='active',
                    category_filters__contains=[instance.category]
                )
                for budget in category_budgets:
                    budget.spent_amount += amount_to_subtract
                    budget.save()
                    break  # Only apply to first matching budget
        except Expense.DoesNotExist:
            pass