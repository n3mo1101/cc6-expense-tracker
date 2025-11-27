"""
Management command to generate sample data using Faker.
Run with: python manage.py create_initial_data

Creates:
- 5 sample users (with profiles and wallets)
- Predefined categories and income sources are auto-created via signal
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
            # Categories and income sources are auto-created via signal
            categories = list(Category.objects.filter(user=user))
            income_sources = list(IncomeSource.objects.filter(user=user))
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
        # Delete in correct order to avoid ProtectedError
        # First delete transactions (Income and Expense reference Category/IncomeSource with PROTECT)
        sample_users = User.objects.filter(username__startswith='testuser')
        
        Income.objects.filter(user__in=sample_users).delete()
        Expense.objects.filter(user__in=sample_users).delete()
        RecurringTransaction.objects.filter(user__in=sample_users).delete()
        Budget.objects.filter(user__in=sample_users).delete()
        
        # Then delete categories and income sources
        Category.objects.filter(user__in=sample_users).delete()
        IncomeSource.objects.filter(user__in=sample_users).delete()
        
        # Then delete wallets and profiles
        Wallet.objects.filter(user__in=sample_users).delete()
        UserProfile.objects.filter(user__in=sample_users).delete()
        
        # Finally delete users
        sample_users.delete()
        
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
        # Profile and predefined data are auto-created via signal
        # Just ensure primary currency is set
        user.profile.primary_currency = 'PHP'
        user.profile.save()
        return user

    def create_wallets(self, user):
        """Create additional wallets for USD and EUR."""
        # Primary PHP wallet is auto-created via signal
        Wallet.objects.create(user=user, currency='USD', balance=Decimal('0.00'))
        Wallet.objects.create(user=user, currency='EUR', balance=Decimal('0.00'))

    def create_budgets(self, user, categories):
        """Create 4 budgets per user."""
        today = timezone.now().date()
        
        # Map predefined category names
        budgets_config = [
            {
                'name': 'Monthly Groceries',
                'budget_type': 'category_filter',
                'amount': Decimal('15000.00'),
                'recurrence_pattern': 'monthly',
                'category_names': ['Groceries'],
            },
            {
                'name': 'Entertainment Budget',
                'budget_type': 'category_filter',
                'amount': Decimal('5000.00'),
                'recurrence_pattern': 'monthly',
                'category_names': ['Entertainment'],
            },
            {
                'name': 'Vacation Fund',
                'budget_type': 'manual',
                'amount': Decimal('50000.00'),
                'recurrence_pattern': 'one_time',
                'category_names': [],
            },
            {
                'name': 'Utilities & Bills',
                'budget_type': 'category_filter',
                'amount': Decimal('10000.00'),
                'recurrence_pattern': 'monthly',
                'category_names': ['Bills & Utilities'],
            },
        ]
        
        for config in budgets_config:
            # Find matching categories
            matching_categories = [c for c in categories if c.name in config['category_names']]
            
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
            if matching_categories:
                budget.category_filters.set(matching_categories)

    def create_recurring_transactions(self, user, categories, income_sources):
        """Create 4 recurring transactions per user."""
        today = timezone.now().date()
        
        # Find specific predefined sources
        salary_source = next((s for s in income_sources if s.name == 'Salary'), None)
        freelance_source = next((s for s in income_sources if s.name == 'Freelance'), None)
        utilities_category = next((c for c in categories if c.name == 'Bills & Utilities'), None)
        entertainment_category = next((c for c in categories if c.name == 'Entertainment'), None)
        
        # 2 recurring incomes
        if salary_source:
            RecurringTransaction.objects.create(
                user=user,
                type='income',
                income_source=salary_source,
                amount=Decimal('45000.00'),
                currency='PHP',
                description='Monthly salary',
                recurrence_pattern='monthly',
                start_date=today - timedelta(days=365),
                is_active=True
            )
        
        if freelance_source:
            RecurringTransaction.objects.create(
                user=user,
                type='income',
                income_source=freelance_source,
                amount=Decimal('500.00'),
                currency='USD',
                description='Freelance retainer',
                recurrence_pattern='monthly',
                start_date=today - timedelta(days=180),
                is_active=True
            )
        
        # 2 recurring expenses
        if utilities_category:
            RecurringTransaction.objects.create(
                user=user,
                type='expense',
                category=utilities_category,
                amount=Decimal('2500.00'),
                currency='PHP',
                description='Electricity bill',
                recurrence_pattern='monthly',
                start_date=today - timedelta(days=365),
                is_active=True
            )
        
        if entertainment_category:
            RecurringTransaction.objects.create(
                user=user,
                type='expense',
                category=entertainment_category,
                amount=Decimal('549.00'),
                currency='PHP',
                description='Streaming subscription',
                recurrence_pattern='monthly',
                start_date=today - timedelta(days=365),
                is_active=True
            )

    def create_incomes(self, user, income_sources):
        """Create 10 income transactions per user distributed across 12 months with gradual increase."""
        today = timezone.now().date()
        current_month_start = today.replace(day=1)
        
        # Distribution: gradually increasing toward current month
        # Months 12-9 ago: 0-1 income each
        # Months 8-5 ago: 1 income each
        # Months 4-2 ago: 1-2 incomes each
        # Last month: 2 incomes
        # Current month: 3 incomes
        
        monthly_distribution = [
            (11, 0),  # 11 months ago
            (10, 1),  # 10 months ago
            (9, 0),   # 9 months ago
            (8, 1),   # 8 months ago
            (7, 1),   # 7 months ago
            (6, 1),   # 6 months ago
            (5, 1),   # 5 months ago
            (4, 2),   # 4 months ago
            (3, 1),   # 3 months ago
            (2, 2),   # 2 months ago
            (1, 2),   # last month
            (0, 3),   # current month
        ]
        
        for months_ago, count in monthly_distribution:
            for _ in range(count):
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
                elif source.name == 'Gifts':
                    amount = Decimal(random.randint(500, 5000))
                else:  # Other sources
                    amount = Decimal(random.randint(1000, 8000))
                
                # Adjust for currency
                if currency != 'PHP':
                    amount = Decimal(random.randint(100, 2000))
                
                # Calculate transaction date for the target month
                if months_ago == 0:
                    # Current month: random day from 1st to today
                    days_in_range = today.day
                    random_day = random.randint(1, days_in_range)
                    transaction_date = today.replace(day=random_day)
                else:
                    # Past months: random day in that month
                    target_month = current_month_start - timedelta(days=months_ago * 30)
                    # Get last day of target month
                    if target_month.month == 12:
                        next_month = target_month.replace(year=target_month.year + 1, month=1, day=1)
                    else:
                        next_month = target_month.replace(month=target_month.month + 1, day=1)
                    last_day = (next_month - timedelta(days=1)).day
                    random_day = random.randint(1, last_day)
                    transaction_date = target_month.replace(day=random_day)
                
                # 95% complete, 5% pending (pending only for current month)
                if months_ago == 0:
                    status = 'complete' if random.random() < 0.9 else 'pending'
                else:
                    status = 'complete'
                
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
        """Create 25 expense transactions per user distributed across 12 months with gradual increase."""
        today = timezone.now().date()
        current_month_start = today.replace(day=1)
        
        # Get budgets for linking
        budgets = list(Budget.objects.filter(user=user))
        
        # Distribution: gradually increasing toward current month
        # Months 12-10 ago: 1 expense each
        # Months 9-7 ago: 1 expense each
        # Months 6-4 ago: 2 expenses each
        # Month 3 ago: 2 expenses
        # Month 2 ago: 3 expenses
        # Last month: 4 expenses
        # Current month: 8 expenses
        
        monthly_distribution = [
            (11, 1),  # 11 months ago
            (10, 1),  # 10 months ago
            (9, 1),   # 9 months ago
            (8, 1),   # 8 months ago
            (7, 1),   # 7 months ago
            (6, 2),   # 6 months ago
            (5, 2),   # 5 months ago
            (4, 2),   # 4 months ago
            (3, 2),   # 3 months ago
            (2, 3),   # 2 months ago
            (1, 4),   # last month
            (0, 8),   # current month
        ]
        
        for months_ago, count in monthly_distribution:
            for _ in range(count):
                currency = random.choice(CURRENCIES)
                category = random.choice(categories)
                
                # Amount ranges based on category (using predefined category names)
                amount_ranges = {
                    'Food & Dining': (100, 2000),
                    'Groceries': (500, 3000),
                    'Transportation': (50, 1500),
                    'Bills & Utilities': (500, 5000),
                    'Entertainment': (200, 3000),
                    'Shopping': (500, 10000),
                    'Healthcare': (300, 5000),
                    'Education': (1000, 15000),
                    'Games & Hobbies': (200, 4000),
                    'Other Expenses': (100, 5000),
                }
                min_amt, max_amt = amount_ranges.get(category.name, (100, 5000))
                amount = Decimal(random.randint(min_amt, max_amt))
                
                # Adjust for currency
                if currency != 'PHP':
                    amount = Decimal(random.randint(10, 200))
                
                # Calculate transaction date for the target month
                if months_ago == 0:
                    # Current month: random day from 1st to today
                    days_in_range = today.day
                    random_day = random.randint(1, days_in_range)
                    transaction_date = today.replace(day=random_day)
                else:
                    # Past months: random day in that month
                    target_month = current_month_start - timedelta(days=months_ago * 30)
                    # Get last day of target month
                    if target_month.month == 12:
                        next_month = target_month.replace(year=target_month.year + 1, month=1, day=1)
                    else:
                        next_month = target_month.replace(month=target_month.month + 1, day=1)
                    last_day = (next_month - timedelta(days=1)).day
                    random_day = random.randint(1, last_day)
                    transaction_date = target_month.replace(day=random_day)
                
                # 95% complete, 5% pending (pending only for current month)
                if months_ago == 0:
                    status = 'complete' if random.random() < 0.9 else 'pending'
                else:
                    status = 'complete'
                
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