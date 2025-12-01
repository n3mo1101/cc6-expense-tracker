from decimal import Decimal
from django.db.models import Sum
from django.utils import timezone
from expense_tracker.models import Budget, Expense, Category


class BudgetService:
    """Service for budget operations"""
    
    @staticmethod
    def calculate_spent_amount(budget, user):
        # Calculate total spent amount for a budget from transactions

        # Base query for expenses in budget period
        expenses_query = Expense.objects.filter(
            user=user,
            status='complete',
            transaction_date__gte=budget.start_date,
        )
        
        # Add end date filter if exists
        if budget.end_date:
            expenses_query = expenses_query.filter(transaction_date__lte=budget.end_date)
        
        # Filter by budget type
        if budget.budget_type == 'category_filter':
            # Only count expenses in the filtered categories
            category_ids = budget.category_filters.values_list('id', flat=True)
            expenses_query = expenses_query.filter(category_id__in=category_ids)
        elif budget.budget_type == 'manual':
            # Only count expenses explicitly linked to this budget
            expenses_query = expenses_query.filter(budget=budget)
        
        # Sum converted amounts (normalized to user's primary currency)
        total = expenses_query.aggregate(total=Sum('converted_amount'))['total']
        
        return total or Decimal('0.00')
    
    @staticmethod
    def get_budget_display_data(budget, user):
        # Calculate all display data for a budget
        today = timezone.now().date()
        
        # Calculate spent amount from actual transactions
        spent_amount = BudgetService.calculate_spent_amount(budget, user)
        remaining_amount = budget.amount - spent_amount
        percentage_used = (spent_amount / budget.amount * 100) if budget.amount > 0 else 0
        is_overspent = spent_amount > budget.amount
        
        budget_data = {
            'id': str(budget.id),
            'name': budget.name,
            'amount': budget.amount,
            'currency': budget.currency,
            'spent_amount': spent_amount,
            'remaining_amount': max(remaining_amount, Decimal('0.00')),
            'percentage_used': min(percentage_used, 100),
            'actual_percentage': percentage_used,
            'is_overspent': is_overspent,
            'overspent_amount': abs(remaining_amount) if is_overspent else 0,
            'start_date': budget.start_date,
            'end_date': budget.end_date,
            'recurrence_pattern': budget.recurrence_pattern,
            'budget_type': budget.budget_type,
            'status': budget.status,
        }
        
        # Calculate days remaining and daily allowance
        if budget.end_date and budget.end_date >= today:
            days_remaining = (budget.end_date - today).days + 1
            budget_data['days_remaining'] = days_remaining
            budget_data['daily_allowance'] = remaining_amount / days_remaining if days_remaining > 0 else 0
        else:
            budget_data['days_remaining'] = 0
            budget_data['daily_allowance'] = 0
        
        # Calculate time progress (how far through the budget period)
        if budget.start_date and budget.end_date:
            total_days = (budget.end_date - budget.start_date).days + 1
            days_passed = (today - budget.start_date).days
            budget_data['time_progress'] = min(max((days_passed / total_days) * 100, 0), 100) if total_days > 0 else 0
        else:
            budget_data['time_progress'] = 0
        
        return budget_data
    
    @staticmethod
    def get_all_budgets_display(user):
        # Get all budgets with display data, separated by active/inactive 
        budgets = Budget.objects.filter(user=user).prefetch_related('category_filters')
        
        active_budgets = []
        inactive_budgets = []
        
        for budget in budgets:
            budget_data = BudgetService.get_budget_display_data(budget, user)
            
            # Convert to object-like dict for template access
            class BudgetDisplay:
                def __init__(self, data):
                    for key, value in data.items():
                        setattr(self, key, value)
            
            budget_obj = BudgetDisplay(budget_data)
            
            if budget.status == 'active':
                active_budgets.append(budget_obj)
            else:
                inactive_budgets.append(budget_obj)
        
        return active_budgets, inactive_budgets
    
    @staticmethod
    def get_budget_detail_json(budget, user):
        # Get budget details formatted for JSON response
        spent_amount = BudgetService.calculate_spent_amount(budget, user)
        remaining_amount = budget.amount - spent_amount
        percentage_used = (spent_amount / budget.amount * 100) if budget.amount > 0 else 0
        
        return {
            'id': str(budget.id),
            'name': budget.name,
            'amount': str(budget.amount),
            'currency': budget.currency,
            'spent_amount': str(spent_amount),
            'remaining_amount': str(max(remaining_amount, Decimal('0.00'))),
            'percentage_used': percentage_used,
            'is_overspent': spent_amount > budget.amount,
            'start_date': budget.start_date.isoformat(),
            'end_date': budget.end_date.isoformat() if budget.end_date else None,
            'recurrence_pattern': budget.recurrence_pattern,
            'budget_type': budget.budget_type,
            'status': budget.status,
            'category_ids': [str(c.id) for c in budget.category_filters.all()],
            'category_names': [c.name for c in budget.category_filters.all()],
        }
    
    @staticmethod
    def create_budget(user, data):
        # Create a new budget
        budget = Budget.objects.create(
            user=user,
            name=data['name'],
            amount=Decimal(data['amount']),
            currency=data['currency'],
            start_date=data['start_date'],
            end_date=data.get('end_date') or None,
            recurrence_pattern=data.get('recurrence_pattern', 'monthly'),
            budget_type=data.get('budget_type', 'manual'),
            status='active',
        )
        
        # Add category filters if applicable
        if data.get('budget_type') == 'category_filter' and data.get('category_ids'):
            categories = Category.objects.filter(id__in=data['category_ids'], user=user)
            budget.category_filters.set(categories)
        
        return budget
    
    @staticmethod
    def update_budget(budget, user, data):
        # Update an existing budget
        budget.name = data.get('name', budget.name)
        budget.amount = Decimal(data['amount']) if 'amount' in data else budget.amount
        budget.currency = data.get('currency', budget.currency)
        budget.start_date = data.get('start_date', budget.start_date)
        budget.end_date = data.get('end_date') or None
        budget.recurrence_pattern = data.get('recurrence_pattern', budget.recurrence_pattern)
        budget.budget_type = data.get('budget_type', budget.budget_type)
        budget.save()
        
        # Update category filters if applicable
        if data.get('budget_type') == 'category_filter':
            if 'category_ids' in data:
                categories = Category.objects.filter(id__in=data['category_ids'], user=user)
                budget.category_filters.set(categories)
        else:
            budget.category_filters.clear()
        
        return budget
    
    @staticmethod
    def toggle_budget_status(budget, new_status=None):
        # Toggle budget active/inactive status
        if new_status is None:
            new_status = 'inactive' if budget.status == 'active' else 'active'
        
        budget.status = new_status
        budget.save()
        
        message = f'Budget {"activated" if new_status == "active" else "deactivated"} successfully'
        return budget, message
