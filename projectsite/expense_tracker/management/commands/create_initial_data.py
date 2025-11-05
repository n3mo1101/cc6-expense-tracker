import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.models import User
from expense_tracker.models import UserProfile, ExpenseCategory, Budget, Expense, Income, BudgetCategory


class Command(BaseCommand):
    help = 'Generate sample data for expense tracker application'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--delete',
            action='store_true',
            help='Delete all sample data instead of creating',
        )
        parser.add_argument(
            '--users',
            type=int,
            default=4,
            help='Number of sample users to create (default: 4)',
        )
    
    def handle(self, *args, **options):
        if options['delete']:
            self.delete_all_data()
        else:
            self.create_sample_data(options['users'])
    
    def create_sample_data(self, num_users=4):
        """Generate comprehensive sample data for testing"""
        self.stdout.write(self.style.SUCCESS('🚀 Starting to generate sample data...'))
        
        # Create sample users
        users = self.create_sample_users(num_users)
        
        # Create predefined categories
        predefined_categories = self.create_predefined_categories()
        
        # Create user-specific categories and data for each user
        for user in users:
            self.stdout.write(f'📊 Creating data for user: {user.username}')
            
            # Create user profile if it doesn't exist
            profile, created = UserProfile.objects.get_or_create(user=user)
            if created:
                profile.default_currency = random.choice(['USD', 'EUR', 'PHP', 'GBP'])
                profile.timezone = random.choice(['UTC', 'US/Eastern', 'Europe/London', 'Asia/Manila'])
                
                # Assign random avatar from AVATAR_CHOICES
                avatar_choices = [choice[0] for choice in UserProfile.AVATAR_CHOICES]
                profile.profile_picture = random.choice(avatar_choices)
                profile.save()
                self.stdout.write(f"   🎨 Assigned avatar: {profile.profile_picture}")
            
            # Create user-specific categories
            user_categories = self.create_user_categories(user)
            all_categories = predefined_categories + user_categories
            
            # Create budgets
            budgets = self.create_sample_budgets(user, all_categories)
            
            # Create expenses
            self.create_sample_expenses(user, all_categories)
            
            # Create income
            self.create_sample_income(user)
        
        self.stdout.write(self.style.SUCCESS('✅ Sample data generation completed!'))
        self.print_summary()
    
    def create_sample_users(self, num_users):
        """Create sample users"""
        first_names = ['John', 'Jane', 'Mike', 'Sarah', 'David', 'Lisa', 'Robert', 'Emily']
        last_names = ['Doe', 'Smith', 'Wilson', 'Jones', 'Brown', 'Davis', 'Miller', 'Taylor']
        
        users = []
        for i in range(num_users):
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            username = f"{first_name.lower()}_{last_name.lower()}"
            email = f"{username}@example.com"
            
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': first_name,
                    'last_name': last_name,
                    'is_active': True
                }
            )
            if created:
                user.set_password('password123')
                user.save()
                self.stdout.write(f"👤 Created user: {user.username}")
            users.append(user)
        
        return users
    
    def create_predefined_categories(self):
        """Create predefined expense categories"""
        predefined_categories = [
            ('Food & Dining', 'Groceries, restaurants, coffee shops'),
            ('Housing', 'Rent, mortgage, utilities'),
            ('Transportation', 'Gas, public transport, car maintenance'),
            ('Entertainment', 'Movies, concerts, hobbies'),
            ('Healthcare', 'Doctor visits, medication, insurance'),
            ('Shopping', 'Clothing, electronics, personal items'),
            ('Travel', 'Flights, hotels, vacation expenses'),
            ('Education', 'Tuition, books, courses'),
            ('Utilities', 'Electricity, water, internet, phone'),
            ('Personal Care', 'Haircuts, cosmetics, gym'),
        ]
        
        categories = []
        for name, description in predefined_categories:
            category, created = ExpenseCategory.objects.get_or_create(
                name=name,
                defaults={
                    'description': description,
                    'is_predefined': True,
                    'user': None
                }
            )
            if created:
                self.stdout.write(f"📁 Created predefined category: {name}")
            categories.append(category)
        
        return categories
    
    def create_user_categories(self, user):
        """Create user-specific categories"""
        user_categories_data = [
            ('Side Projects', 'Income from freelance work or side projects'),
            ('Investment Returns', 'Dividends, interest, or capital gains'),
            ('Gifts Received', 'Monetary gifts from family or friends'),
            ('Business Expenses', 'Work-related expenses'),
            ('Home Improvement', 'Renovations and home maintenance'),
        ]
        
        categories = []
        for name, description in user_categories_data:
            category, created = ExpenseCategory.objects.get_or_create(
                name=name,
                user=user,
                defaults={
                    'description': description,
                    'is_predefined': False
                }
            )
            if created:
                self.stdout.write(f"📁 Created user category for {user.username}: {name}")
            categories.append(category)
        
        return categories
    
    def create_sample_budgets(self, user, categories):
        """Create sample budgets for a user"""
        current_date = timezone.now().date()
        
        budgets_data = [
            {
                'name': 'Monthly Budget',
                'total_amount': random.randint(2000, 5000),
                'start_date': current_date.replace(day=1),
                'end_date': (current_date.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            },
            {
                'name': 'Quarterly Savings Goal',
                'total_amount': random.randint(4000, 8000),
                'start_date': current_date.replace(day=1),
                'end_date': (current_date.replace(day=1) + timedelta(days=93)).replace(day=1) - timedelta(days=1)
            }
        ]
        
        budgets = []
        for budget_data in budgets_data:
            budget, created = Budget.objects.get_or_create(
                user=user,
                name=budget_data['name'],
                defaults={
                    'total_amount': budget_data['total_amount'],
                    'currency_code': 'USD',
                    'start_date': budget_data['start_date'],
                    'end_date': budget_data['end_date'],
                    'description': f"{budget_data['name']} for {user.username}"
                }
            )
            
            if created:
                self.stdout.write(f"💰 Created budget for {user.username}: {budget.name}")
                
                # Create budget categories
                selected_categories = random.sample(categories, min(5, len(categories)))
                total_allocated = 0
                
                for category in selected_categories:
                    # Allocate random amount (10-40% of budget)
                    allocated_amount = round(budget.total_amount * random.uniform(0.1, 0.4), 2)
                    total_allocated += allocated_amount
                    
                    # Adjust if we're over budget
                    if total_allocated > budget.total_amount:
                        allocated_amount -= (total_allocated - budget.total_amount)
                    
                    BudgetCategory.objects.create(
                        budget=budget,
                        category=category,
                        allocated_amount=allocated_amount
                    )
            
            budgets.append(budget)
        
        return budgets
    
    def create_sample_expenses(self, user, categories):
        """Create sample expenses for a user"""
        expense_descriptions = [
            "Weekly grocery shopping",
            "Dinner at restaurant", 
            "Gas refill",
            "Movie tickets",
            "Online shopping",
            "Coffee with friends",
            "Monthly subscription",
            "Public transport pass",
            "Phone bill",
            "Electricity bill",
            "Doctor appointment",
            "Gym membership",
            "Book purchase",
            "Home supplies",
            "Work lunch",
            "Uber ride",
            "Amazon purchase",
            "Netflix subscription",
            "Haircut",
            "Car maintenance"
        ]
        
        # Create 15-30 random expenses
        num_expenses = random.randint(15, 30)
        
        for i in range(num_expenses):
            # Random date within last 90 days
            days_ago = random.randint(0, 90)
            expense_date = timezone.now().date() - timedelta(days=days_ago)
            
            # Random category
            category = random.choice(categories)
            
            # Random amount based on category
            if category.name in ['Housing', 'Utilities']:
                amount = round(random.uniform(100, 500), 2)
            elif category.name in ['Food & Dining', 'Shopping']:
                amount = round(random.uniform(20, 150), 2)
            else:
                amount = round(random.uniform(5, 100), 2)
            
            Expense.objects.create(
                user=user,
                category=category,
                amount=amount,
                currency_code='USD',
                description=random.choice(expense_descriptions),
                expense_date=expense_date,
                is_recurring=random.choice([True, False, False, False])  # 25% chance of recurring
            )
        
        self.stdout.write(f"💸 Created {num_expenses} expenses for {user.username}")
    
    def create_sample_income(self, user):
        """Create sample income for a user"""
        income_sources = [
            "Salary",
            "Freelance Work", 
            "Investment Returns",
            "Bonus",
            "Side Business",
            "Consulting Fee",
            "Part-time Job",
            "Royalties"
        ]
        
        # Create 3-8 income records
        num_incomes = random.randint(3, 8)
        
        for i in range(num_incomes):
            # Random date within last 90 days
            days_ago = random.randint(0, 90)
            income_date = timezone.now().date() - timedelta(days=days_ago)
            
            source = random.choice(income_sources)
            
            # Random amount based on source
            if source == 'Salary':
                amount = round(random.uniform(2000, 5000), 2)
            elif source in ['Bonus', 'Investment Returns']:
                amount = round(random.uniform(500, 2000), 2)
            else:
                amount = round(random.uniform(100, 800), 2)
            
            Income.objects.create(
                user=user,
                amount=amount,
                currency_code='USD',
                source=source,
                description=f"Monthly {source}",
                income_date=income_date,
                is_recurring=source in ['Salary', 'Investment Returns']
            )
        
        self.stdout.write(f"💰 Created {num_incomes} income records for {user.username}")
    
    def print_summary(self):
        """Print summary of generated data"""
        self.stdout.write("\n📊 DATA GENERATION SUMMARY:")
        self.stdout.write(f"   Users: {User.objects.count()}")
        self.stdout.write(f"   User Profiles: {UserProfile.objects.count()}")
        self.stdout.write(f"   Expense Categories: {ExpenseCategory.objects.count()}")
        self.stdout.write(f"   Budgets: {Budget.objects.count()}")
        self.stdout.write(f"   Budget Categories: {BudgetCategory.objects.count()}")
        self.stdout.write(f"   Expenses: {Expense.objects.count()}")
        self.stdout.write(f"   Income: {Income.objects.count()}")
        
        # Print user-specific summary
        self.stdout.write("\n👥 USER BREAKDOWN:")
        for user in User.objects.all():
            expenses = Expense.objects.filter(user=user).count()
            income = Income.objects.filter(user=user).count()
            budgets = Budget.objects.filter(user=user).count()
            self.stdout.write(f"   {user.username}: {expenses} expenses, {income} income, {budgets} budgets")
    
    def delete_all_data(self):
        """Delete all sample data (cleanup function)"""
        self.stdout.write('🧹 Deleting all sample data...')
        
        # Delete in proper order to avoid foreign key constraints
        Income.objects.all().delete()
        Expense.objects.all().delete()
        BudgetCategory.objects.all().delete()
        Budget.objects.all().delete()
        
        # Only delete user-specific categories, keep predefined ones
        ExpenseCategory.objects.filter(is_predefined=False).delete()
        UserProfile.objects.all().delete()
        
        # Delete sample users (keep superusers)
        User.objects.filter(is_superuser=False).delete()
        
        self.stdout.write(self.style.SUCCESS('✅ All sample data deleted!'))