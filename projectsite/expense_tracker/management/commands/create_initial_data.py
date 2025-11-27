"""
Management command to generate sample data using Faker.
Run with: python manage.py create_sample_data

Creates:
- 5 sample users (with profiles and wallets)
- Default categories and income sources for each user
- 10 incomes, 25 expenses, 4 budgets, 4 recurring transactions per user
"""

import random
from decimal import Decimal
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from faker import Faker

from expense_tracker.models import (
    UserProfile, Wallet, Category, IncomeSource,
    Budget, RecurringTransaction, Income, Expense
)

fake = Faker()

# ============================================================================
# DEFAULT DATA
# ============================================================================

DEFAULT_CATEGORIES = [
    {'name': 'Food', 'icon': 'utensils'},
    {'name': 'Transport', 'icon': 'car'},
    {'name': 'Utilities', 'icon': 'bolt'},
    {'name': 'Entertainment', 'icon': 'film'},
    {'name': 'Shopping', 'icon': 'bag-shopping'},
    {'name': 'Health', 'icon': 'heart-pulse'},
    {'name': 'Education', 'icon': 'graduation-cap'},
    {'name': 'Bills', 'icon': 'file-invoice'},
]

DEFAULT_INCOME_SOURCES = [
    {'name': 'Salary', 'icon': 'briefcase'},
    {'name': 'Freelance', 'icon': 'laptop'},
    {'name': 'Business', 'icon': 'store'},
    {'name': 'Investment', 'icon': 'chart-line'},
    {'name': 'Gift', 'icon': 'gift'},
]

CURRENCIES = ['PHP', 'PHP', 'PHP', 'PHP', 'USD', 'EUR']  # Weighted towards PHP

# Exchange rates (approximate, for sample data only)
EXCHANGE_RATES = {
    'PHP': Decimal('1.00'),
    'USD': Decimal('56.50'),
    'EUR': Decimal('61.20'),
}


class Command(BaseCommand):
    help = 'Generate sample data for Cashew app'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample data...\n')
        
        # Clear existing sample data (optional)
        self.clear_sample_data()
        
        # Create 5 sample users
        for i in range(5):
            user = self.create_user(i + 1)
            categories = self.create_categories(user)
            income_sources = self.create_income_sources(user)
            self.create_wallets(user)
            self.create_budgets(user, categories)
            self.create_recurring_transactions(user, categories, income_sources)
            self.create_incomes(user, income_sources)
            self.create_expenses(user, categories)
            
            self.stdout.write(f'  Created data for user: {user.username}')
        
        self.stdout.write(self.style.SUCCESS('\nSample data created successfully!'))
        self.stdout.write('\nSample users (password: "password123"):')
        for i in range(1, 6):
            self.stdout.write(f'  - testuser{i}')

    def clear_sample_data(self):
        """Remove existing sample data."""
        User.objects.filter(username__startswith='testuser').delete()
        self.stdout.write('  Cleared existing sample data')

    def create_user(self, index):
        """Create a sample user with profile."""
        user = User.objects.create_user(
            username=f'testuser{index}',
            email=f'testuser{index}@example.com',
            password='password123',
            first_name=fake.first_name(),
            last_name=fake.last_name()
        )
        # Profile is auto-created via signal, just update currency
        user.profile.primary_currency = 'PHP'
        user.profile.save()
        return user

    def create_categories(self, user):
        """Create default categories for user."""
        categories = []
        for cat_data in DEFAULT_CATEGORIES:
            cat = Category.objects.create(
                user=user,
                name=cat_data['name'],
                icon=cat_data['icon']
            )
            categories.append(cat)
        return categories

    def create_income_sources(self, user):
        """Create default income sources for user."""
        sources = []
        for src_data in DEFAULT_INCOME_SOURCES:
            src = IncomeSource.objects.create(
                user=user,
                name=src_data['name'],
                icon=src_data['icon']
            )
            sources.append(src)
        return sources

    def create_wallets(self, user):
        """Create additional wallets for USD and EUR."""
        # Primary PHP wallet is auto-created via signal
        Wallet.objects.create(user=user, currency='USD', balance=Decimal('0.00'))
        Wallet.objects.create(user=user, currency='EUR', balance=Decimal('0.00'))

    def create_budgets(self, user, categories):
        """Create 4 budgets per user."""
        today = timezone.now().date()
        
        budgets_config = [
            {
                'name': 'Monthly Groceries',
                'budget_type': 'category_filter',
                'amount': Decimal('15000.00'),
                'recurrence_pattern': 'monthly',
                'categories': [c for c in categories if c.name == 'Food'],
            },
            {
                'name': 'Entertainment Budget',
                'budget_type': 'category_filter',
                'amount': Decimal('5000.00'),
                'recurrence_pattern': 'monthly',
                'categories': [c for c in categories if c.name == 'Entertainment'],
            },
            {
                'name': 'Vacation Fund',
                'budget_type': 'manual',
                'amount': Decimal('50000.00'),
                'recurrence_pattern': 'one_time',
                'categories': [],
            },
            {
                'name': 'Utilities & Bills',
                'budget_type': 'category_filter',
                'amount': Decimal('10000.00'),
                'recurrence_pattern': 'monthly',
                'categories': [c for c in categories if c.name in ['Utilities', 'Bills']],
            },
        ]
        
        for config in budgets_config:
            budget = Budget.objects.create(
                user=user,
                name=config['name'],
                budget_type=config['budget_type'],
                amount=config['amount'],
                currency='PHP',
                recurrence_pattern=config['recurrence_pattern'],
                start_date=today.replace(day=1),
                end_date=today + timedelta(days=365) if config['recurrence_pattern'] == 'one_time' else None,
                status='active'
            )
            budget.category_filters.set(config['categories'])

    def create_recurring_transactions(self, user, categories, income_sources):
        """Create 4 recurring transactions per user."""
        today = timezone.now().date()
        
        # 2 recurring incomes
        RecurringTransaction.objects.create(
            user=user,
            type='income',
            income_source=next(s for s in income_sources if s.name == 'Salary'),
            amount=Decimal('45000.00'),
            currency='PHP',
            description='Monthly salary',
            recurrence_pattern='monthly',
            start_date=today - timedelta(days=365),
            is_active=True
        )
        
        RecurringTransaction.objects.create(
            user=user,
            type='income',
            income_source=next(s for s in income_sources if s.name == 'Freelance'),
            amount=Decimal('500.00'),
            currency='USD',
            description='Freelance retainer',
            recurrence_pattern='monthly',
            start_date=today - timedelta(days=180),
            is_active=True
        )
        
        # 2 recurring expenses
        RecurringTransaction.objects.create(
            user=user,
            type='expense',
            category=next(c for c in categories if c.name == 'Utilities'),
            amount=Decimal('2500.00'),
            currency='PHP',
            description='Electricity bill',
            recurrence_pattern='monthly',
            start_date=today - timedelta(days=365),
            is_active=True
        )
        
        RecurringTransaction.objects.create(
            user=user,
            type='expense',
            category=next(c for c in categories if c.name == 'Entertainment'),
            amount=Decimal('549.00'),
            currency='PHP',
            description='Streaming subscription',
            recurrence_pattern='monthly',
            start_date=today - timedelta(days=365),
            is_active=True
        )

    def create_incomes(self, user, income_sources):
        """Create 10 income transactions per user."""
        today = timezone.now().date()
        
        for _ in range(10):
            currency = random.choice(CURRENCIES)
            source = random.choice(income_sources)
            
            # Amount ranges based on source
            if source.name == 'Salary':
                amount = Decimal(random.randint(40000, 60000))
            elif source.name == 'Freelance':
                amount = Decimal(random.randint(5000, 20000))
            elif source.name == 'Business':
                amount = Decimal(random.randint(10000, 50000))
            elif source.name == 'Investment':
                amount = Decimal(random.randint(1000, 10000))
            else:  # Gift
                amount = Decimal(random.randint(500, 5000))
            
            # Adjust for currency
            if currency != 'PHP':
                amount = Decimal(random.randint(100, 2000))
            
            # Random date in last 12 months
            days_ago = random.randint(0, 365)
            transaction_date = today - timedelta(days=days_ago)
            
            # 90% complete, 10% pending
            status = 'complete' if random.random() < 0.9 else 'pending'
            
            # Calculate converted amount
            exchange_rate = EXCHANGE_RATES.get(currency, Decimal('1.00'))
            converted_amount = amount * exchange_rate if currency != 'PHP' else amount
            
            Income.objects.create(
                user=user,
                source=source,
                amount=amount,
                currency=currency,
                exchange_rate=exchange_rate if currency != 'PHP' else None,
                converted_amount=converted_amount,
                transaction_date=transaction_date,
                description=fake.sentence(nb_words=4),
                status=status
            )

    def create_expenses(self, user, categories):
        """Create 25 expense transactions per user."""
        today = timezone.now().date()
        
        # Get budgets for linking
        budgets = list(Budget.objects.filter(user=user))
        
        for _ in range(25):
            currency = random.choice(CURRENCIES)
            category = random.choice(categories)
            
            # Amount ranges based on category
            amount_ranges = {
                'Food': (100, 2000),
                'Transport': (50, 1500),
                'Utilities': (500, 5000),
                'Entertainment': (200, 3000),
                'Shopping': (500, 10000),
                'Health': (300, 5000),
                'Education': (1000, 15000),
                'Bills': (500, 8000),
            }
            min_amt, max_amt = amount_ranges.get(category.name, (100, 5000))
            amount = Decimal(random.randint(min_amt, max_amt))
            
            # Adjust for currency
            if currency != 'PHP':
                amount = Decimal(random.randint(10, 200))
            
            # Random date in last 12 months
            days_ago = random.randint(0, 365)
            transaction_date = today - timedelta(days=days_ago)
            
            # 90% complete, 10% pending
            status = 'complete' if random.random() < 0.9 else 'pending'
            
            # Calculate converted amount
            exchange_rate = EXCHANGE_RATES.get(currency, Decimal('1.00'))
            converted_amount = amount * exchange_rate if currency != 'PHP' else amount
            
            # Link to manual budget occasionally (20% chance)
            budget = None
            if random.random() < 0.2:
                manual_budgets = [b for b in budgets if b.budget_type == 'manual']
                if manual_budgets:
                    budget = random.choice(manual_budgets)
            
            Expense.objects.create(
                user=user,
                category=category,
                amount=amount,
                currency=currency,
                exchange_rate=exchange_rate if currency != 'PHP' else None,
                converted_amount=converted_amount,
                transaction_date=transaction_date,
                description=fake.sentence(nb_words=4),
                status=status,
                budget=budget
            )