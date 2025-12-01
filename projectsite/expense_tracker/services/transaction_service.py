from decimal import Decimal
from expense_tracker.models import Income, Expense, IncomeSource, Category, Budget, RecurringTransaction
from expense_tracker.services.currency_service import CurrencyService


class TransactionService:
    """Service for transaction operations"""
    
    @staticmethod
    def _get_primary_currency(user):
        """Get user's primary currency with fallback"""
        try:
            return user.profile.primary_currency
        except Exception:
            return 'PHP'
    
    @staticmethod
    def _convert_currency(amount, currency, primary_currency):
        # Convert currency if needed
        if currency == primary_currency:
            return amount, None
        
        try:
            conversion = CurrencyService.convert(amount, currency, primary_currency)
            return conversion['converted_amount'], conversion['rate']
        except Exception:
            return amount, None
    
    @staticmethod
    def create_income(user, data):
        # Create a new income transaction (with optional recurring)
        source = IncomeSource.objects.get(id=data['source_id'], user=user)
        amount = Decimal(data['amount'])
        currency = data['currency']
        primary_currency = TransactionService._get_primary_currency(user)
        
        # Currency conversion
        converted_amount, exchange_rate = TransactionService._convert_currency(
            amount, currency, primary_currency
        )
        
        # Handle recurring transaction
        is_recurring = data.get('is_recurring', False)
        recurring_transaction = None
        
        if is_recurring:
            recurring_transaction = RecurringTransaction.objects.create(
                user=user,
                type='income',
                income_source=source,
                amount=amount,
                currency=currency,
                description=data.get('description', ''),
                recurrence_pattern=data.get('recurrence_pattern', 'monthly'),
                start_date=data['transaction_date'],
                end_date=data.get('recurrence_end_date') or None,
                is_active=True,
            )
        
        # Create income
        income = Income.objects.create(
            user=user,
            source=source,
            amount=amount,
            currency=currency,
            converted_amount=converted_amount,
            exchange_rate=exchange_rate,
            transaction_date=data['transaction_date'],
            description=data.get('description', ''),
            status=data.get('status', 'pending'),
            recurring_transaction=recurring_transaction,
        )
        
        return income, is_recurring
    
    @staticmethod
    def create_expense(user, data):
        # Create a new expense transaction (with optional recurring)
        category = Category.objects.get(id=data['category_id'], user=user)
        amount = Decimal(data['amount'])
        currency = data['currency']
        primary_currency = TransactionService._get_primary_currency(user)
        
        # Get budget if provided
        budget = None
        if data.get('budget_id'):
            budget = Budget.objects.get(id=data['budget_id'], user=user)
        
        # Currency conversion
        converted_amount, exchange_rate = TransactionService._convert_currency(
            amount, currency, primary_currency
        )
        
        # Handle recurring transaction
        is_recurring = data.get('is_recurring', False)
        recurring_transaction = None
        
        if is_recurring:
            recurring_transaction = RecurringTransaction.objects.create(
                user=user,
                type='expense',
                category=category,
                amount=amount,
                currency=currency,
                description=data.get('description', ''),
                recurrence_pattern=data.get('recurrence_pattern', 'monthly'),
                start_date=data['transaction_date'],
                end_date=data.get('recurrence_end_date') or None,
                is_active=True,
                budget=budget,
            )
        
        # Create expense
        expense = Expense.objects.create(
            user=user,
            category=category,
            amount=amount,
            currency=currency,
            converted_amount=converted_amount,
            exchange_rate=exchange_rate,
            transaction_date=data['transaction_date'],
            description=data.get('description', ''),
            status=data.get('status', 'pending'),
            budget=budget,
            recurring_transaction=recurring_transaction,
        )
        
        return expense, is_recurring
    
    @staticmethod
    def update_income(income, user, data):
        # Update an existing income transaction
        if 'source_id' in data:
            income.source = IncomeSource.objects.get(id=data['source_id'], user=user)
        
        if 'amount' in data:
            amount = Decimal(data['amount'])
            currency = data.get('currency', income.currency)
            primary_currency = TransactionService._get_primary_currency(user)
            
            income.amount = amount
            income.currency = currency
            
            converted_amount, exchange_rate = TransactionService._convert_currency(
                amount, currency, primary_currency
            )
            income.converted_amount = converted_amount
            income.exchange_rate = exchange_rate
        
        if 'transaction_date' in data:
            income.transaction_date = data['transaction_date']
        
        if 'description' in data:
            income.description = data['description']
        
        if 'status' in data:
            income.status = data['status']
        
        income.save()
        return income
    
    @staticmethod
    def update_expense(expense, user, data):
        # Update an existing expense transaction
        if 'category_id' in data:
            expense.category = Category.objects.get(id=data['category_id'], user=user)
        
        if 'budget_id' in data:
            if data['budget_id']:
                expense.budget = Budget.objects.get(id=data['budget_id'], user=user)
            else:
                expense.budget = None
        
        if 'amount' in data:
            amount = Decimal(data['amount'])
            currency = data.get('currency', expense.currency)
            primary_currency = TransactionService._get_primary_currency(user)
            
            expense.amount = amount
            expense.currency = currency
            
            converted_amount, exchange_rate = TransactionService._convert_currency(
                amount, currency, primary_currency
            )
            expense.converted_amount = converted_amount
            expense.exchange_rate = exchange_rate
        
        if 'transaction_date' in data:
            expense.transaction_date = data['transaction_date']
        
        if 'description' in data:
            expense.description = data['description']
        
        if 'status' in data:
            expense.status = data['status']
        
        expense.save()
        return expense
    
    @staticmethod
    def mark_complete(transaction):
        # Mark transaction as complete
        transaction.status = 'complete'
        transaction.save()
        return transaction
