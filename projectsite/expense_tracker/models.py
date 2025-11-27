from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db.models.signals import post_save
from django.dispatch import receiver
from decimal import Decimal
import uuid


# ============================================================================
# BASE MODEL: Abstract base model with common fields for all models.
# ============================================================================

class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ['-created_at']


# ============================================================================
# USER PROFILE: Extends Django's User model with finance-related settings.
# ============================================================================

class UserProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    primary_currency = models.CharField(max_length=3, default='PHP')
    avatar = models.CharField(max_length=255, default='/static/img/avatars/avatar1.png')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # Track if predefined data has been created for this user
    has_predefined_data = models.BooleanField(default=False)

    class Meta:
        db_table = 'user_profile'

    def __str__(self):
        return f"{self.user.username}'s Profile"


# ============================================================================
# WALLET: Tracks user's balance per currency.
# ============================================================================

class Wallet(BaseModel):
    currency = models.CharField(max_length=3)
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

    def __str__(self):
        return f"{self.user.username} - {self.currency} {self.balance}"

    def save(self, *args, **kwargs):
        if self.is_primary:
            Wallet.objects.filter(user=self.user, is_primary=True).update(is_primary=False)
        super().save(*args, **kwargs)


# ============================================================================
# CATEGORY & INCOME SOURCE: User-defined expense categories & income sources.
# ============================================================================

class Category(BaseModel):
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=255, null=True, blank=True, default='/static/img/icons/icon-default.png')
    # Track if this is a system predefined category
    is_predefined = models.BooleanField(default=False)

    class Meta:
        db_table = 'category'
        unique_together = ['user', 'name']
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name


class IncomeSource(BaseModel):
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=255, null=True, blank=True, default='/static/img/icons/icon-default.png')
    # Track if this is a system predefined income source
    is_predefined = models.BooleanField(default=False)

    class Meta:
        db_table = 'income_source'
        unique_together = ['user', 'name']

    def __str__(self):
        return self.name


# ============================================================================
# PREDEFINED DATA CONFIGURATION
# ============================================================================

class PredefinedDataManager:
    """Manager class to handle predefined categories and income sources"""
    
    # Predefined expense categories with their icons
    PREDEFINED_CATEGORIES = [
        {'name': 'Food & Dining', 'icon': 'ec-food.png'},
        {'name': 'Groceries', 'icon': 'ec-grocery.png'},
        {'name': 'Transportation', 'icon': 'ec-transport.png'},
        {'name': 'Shopping', 'icon': 'ec-shopping.png'},
        {'name': 'Entertainment', 'icon': 'ec-entertainment.png'},
        {'name': 'Bills & Utilities', 'icon': 'ec-bills.png'},
        {'name': 'Healthcare', 'icon': 'ec-health.png'},
        {'name': 'Education', 'icon': 'ec-education.png'},
        {'name': 'Games & Hobbies', 'icon': 'ec-games.png'},
        {'name': 'Other Expenses', 'icon': 'icon-other.png'},
    ]
    
    # Predefined income sources with their icons
    PREDEFINED_INCOME_SOURCES = [
        {'name': 'Salary', 'icon': 'is-salary.png'},
        {'name': 'Freelance', 'icon': 'is-freelance.png'},
        {'name': 'Business', 'icon': 'is-business.png'},
        {'name': 'Investment', 'icon': 'is-investment.png'},
        {'name': 'Gifts', 'icon': 'is-gift.png'},
        {'name': 'Savings', 'icon': 'is-savings.png'},
        {'name': 'Payment', 'icon': 'is-payment.png'},
        {'name': 'Other Income', 'icon': 'icon-other.png'},
    ]
    
    @classmethod
    def create_predefined_data_for_user(cls, user):
        """Create predefined categories and income sources for a new user"""
        
        # Create predefined categories
        for category_data in cls.PREDEFINED_CATEGORIES:
            Category.objects.create(
                user=user,
                name=category_data['name'],
                icon=f"/static/img/icons/{category_data['icon']}",
                is_predefined=True
            )
        
        # Create predefined income sources
        for income_data in cls.PREDEFINED_INCOME_SOURCES:
            IncomeSource.objects.create(
                user=user,
                name=income_data['name'],
                icon=f"/static/img/icons/{income_data['icon']}",
                is_predefined=True
            )
        
        # Mark that predefined data has been created
        profile, created = UserProfile.objects.get_or_create(user=user)
        profile.has_predefined_data = True
        profile.save()


# ============================================================================
# BUDGET: Manages spending limits (manual or category-based).
# ============================================================================

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
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    currency = models.CharField(max_length=3)
    spent_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    recurrence_pattern = models.CharField(max_length=10, choices=RECURRENCE_PATTERNS)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    last_reset_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')

    # Category filters for category_filter budget type (stores category IDs)
    category_filters = models.ManyToManyField(
        Category,
        blank=True,
        related_name='budgets'
    )

    class Meta:
        db_table = 'budget'

    def __str__(self):
        return f"{self.name} - {self.spent_amount}/{self.amount}"

    @property
    def remaining_amount(self):
        return self.amount - self.spent_amount

    @property
    def percentage_used(self):
        if self.amount == 0:
            return 0
        return (self.spent_amount / self.amount) * 100


# ============================================================================
# RECURRING TRANSACTION: Template for auto-generating recurring income/expenses.
# ============================================================================

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
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recurring_expenses'
    )
    income_source = models.ForeignKey(
        IncomeSource,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recurring_incomes'
    )
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
    end_date = models.DateField(null=True, blank=True)
    last_generated_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    budget = models.ForeignKey(
        Budget,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recurring_transactions'
    )

    class Meta:
        db_table = 'recurring_transaction'

    def __str__(self):
        name = self.category.name if self.category else self.income_source.name if self.income_source else 'Unknown'
        return f"{self.get_type_display()} - {name} ({self.recurrence_pattern})"


# ============================================================================
# INCOME: Records income transactions.
# ============================================================================

class Income(BaseModel):
    TRANSACTION_STATUS = [
        ('pending', 'Pending'),
        ('complete', 'Complete'),
    ]

    source = models.ForeignKey(
        IncomeSource,
        on_delete=models.PROTECT,
        related_name='incomes'
    )
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    currency = models.CharField(max_length=3)
    converted_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    transaction_date = models.DateField()
    description = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=TRANSACTION_STATUS, default='pending')
    recurring_transaction = models.ForeignKey(
        RecurringTransaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='generated_incomes'
    )

    class Meta:
        db_table = 'income'
        ordering = ['-transaction_date', '-created_at']

    def __str__(self):
        return f"{self.source.name} - {self.currency} {self.amount}"

    def save(self, *args, **kwargs):
        try:
            primary_currency = self.user.profile.primary_currency
            if self.currency != primary_currency and self.exchange_rate:
                self.converted_amount = self.amount * self.exchange_rate
            elif self.currency == primary_currency:
                self.converted_amount = self.amount
        except Exception:
            # If profile doesn't exist or other error, just save amount as converted
            if self.converted_amount is None:
                self.converted_amount = self.amount
        super().save(*args, **kwargs)

# ============================================================================
# EXPENSE: Records expense transactions.
# ============================================================================

class Expense(BaseModel):
    TRANSACTION_STATUS = [
        ('pending', 'Pending'),
        ('complete', 'Complete'),
    ]

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='expenses'
    )
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    currency = models.CharField(max_length=3)
    converted_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    transaction_date = models.DateField()
    description = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=TRANSACTION_STATUS, default='pending')
    budget = models.ForeignKey(
        Budget,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='expenses'
    )
    recurring_transaction = models.ForeignKey(
        RecurringTransaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='generated_expenses'
    )

    class Meta:
        db_table = 'expense'
        ordering = ['-transaction_date', '-created_at']

    def __str__(self):
        return f"{self.category.name} - {self.currency} {self.amount}"

    def save(self, *args, **kwargs):
        if self.currency != self.user.profile.primary_currency and self.exchange_rate:
            self.converted_amount = self.amount * self.exchange_rate
        elif self.currency == self.user.profile.primary_currency:
            self.converted_amount = self.amount
        super().save(*args, **kwargs)


# ============================================================================
# CURRENCY CACHE: Cached currency codes and exchange rates.
# ============================================================================

# Rates are stored relative to USD as base currency.
class CurrencyCache(models.Model):
    code = models.CharField(max_length=3, primary_key=True)
    name = models.CharField(max_length=100)
    exchange_rate = models.DecimalField(max_digits=15, decimal_places=6)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'currency_cache'
        verbose_name = 'Currency'
        verbose_name_plural = 'Currencies'

    def __str__(self):
        return f"{self.code} - {self.name}"


# ============================================================================
# SIGNALS
# ============================================================================

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    # Auto-create UserProfile when User is created.
    if created:
        profile = UserProfile.objects.create(user=instance)
        
        # Create predefined data for new users
        PredefinedDataManager.create_predefined_data_for_user(instance)


@receiver(post_save, sender=UserProfile)
def create_primary_wallet(sender, instance, created, **kwargs):
    # Auto-create primary Wallet when UserProfile is created.
    if created:
        Wallet.objects.create(
            user=instance.user,
            currency=instance.primary_currency,
            is_primary=True
        )