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
        """Create 10 income transactions per user (6 in current month, 4 in past months)."""
        today = timezone.now().date()
        
        # Create 6 incomes in the current month
        for _ in range(6):
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
            
            # Random date in current month
            days_in_month = today.day
            days_ago = random.randint(0, days_in_month - 1)
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
        
        # Create 4 incomes in past months
        for _ in range(4):
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
            
            # Random date in past 11 months (30-365 days ago)
            days_ago = random.randint(30, 365)
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
        """Create 25 expense transactions per user (18 in current month, 7 in past months)."""
        today = timezone.now().date()
        
        # Get budgets for linking
        budgets = list(Budget.objects.filter(user=user))
        
        # Create 18 expenses in the current month
        for _ in range(18):
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
            
            # Random date in current month
            days_in_month = today.day
            days_ago = random.randint(0, days_in_month - 1)
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
        
        # Create 7 expenses in past months
        for _ in range(7):
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
            
            # Random date in past 11 months (30-365 days ago)
            days_ago = random.randint(30, 365)
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