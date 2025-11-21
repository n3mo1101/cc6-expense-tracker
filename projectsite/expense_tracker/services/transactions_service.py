"""
Transactions Service
Reusable functions for transactions data.
"""

from django.db.models import Q, Value, CharField
from django.db.models.functions import Concat
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from expense_tracker.models import Income, Expense, Category, IncomeSource


class TransactionsService:
    """Service for handling transaction operations."""

    @classmethod
    def get_combined_transactions(cls, user, filters=None, page=1, per_page=15):
        """
        Get combined income and expense transactions with filtering,
        sorting, and pagination.
        
        Args:
            user: User object
            filters: dict with keys: search, category, status, sort_by, sort_order
            page: Page number
            per_page: Items per page
        
        Returns:
            dict with transactions, pagination info, and filter options
        """
        filters = filters or {}
        
        # Get incomes
        incomes = Income.objects.filter(user=user).select_related('source')
        
        # Get expenses
        expenses = Expense.objects.filter(user=user).select_related('category')
        
        # Apply search filter
        search = filters.get('search', '').strip()
        if search:
            incomes = incomes.filter(
                Q(source__name__icontains=search) |
                Q(description__icontains=search)
            )
            expenses = expenses.filter(
                Q(category__name__icontains=search) |
                Q(description__icontains=search)
            )
        
        # Apply category/source filter
        category_filter = filters.get('category', '')
        if category_filter:
            if category_filter.startswith('income:'):
                source_id = category_filter.replace('income:', '')
                incomes = incomes.filter(source_id=source_id)
                expenses = expenses.none()
            elif category_filter.startswith('expense:'):
                cat_id = category_filter.replace('expense:', '')
                expenses = expenses.filter(category_id=cat_id)
                incomes = incomes.none()
        
        # Apply status filter
        status_filter = filters.get('status', '')
        if status_filter:
            incomes = incomes.filter(status=status_filter)
            expenses = expenses.filter(status=status_filter)
        
        # Convert to list of dicts for combined sorting
        transactions = []
        
        for income in incomes:
            transactions.append({
                'id': str(income.id),
                'type': 'income',
                'name': income.source.name,
                'source_id': str(income.source.id),
                'amount': income.converted_amount or income.amount,
                'original_amount': income.amount,
                'currency': income.currency,
                'date': income.transaction_date,
                'status': income.status,
                'description': income.description,
                'icon': income.source.icon,
            })
        
        for expense in expenses:
            transactions.append({
                'id': str(expense.id),
                'type': 'expense',
                'name': expense.category.name,
                'category_id': str(expense.category.id),
                'amount': expense.converted_amount or expense.amount,
                'original_amount': expense.amount,
                'currency': expense.currency,
                'date': expense.transaction_date,
                'status': expense.status,
                'description': expense.description,
                'icon': expense.category.icon,
                'budget_id': str(expense.budget_id) if expense.budget_id else None,
            })
        
        # Sort transactions
        sort_by = filters.get('sort_by', 'date')
        sort_order = filters.get('sort_order', 'desc')
        reverse = sort_order == 'desc'
        
        if sort_by == 'date':
            transactions.sort(key=lambda x: x['date'], reverse=reverse)
        elif sort_by == 'amount':
            transactions.sort(key=lambda x: x['amount'], reverse=reverse)
        
        # Pagination
        paginator = Paginator(transactions, per_page)
        
        try:
            paginated = paginator.page(page)
        except PageNotAnInteger:
            paginated = paginator.page(1)
        except EmptyPage:
            paginated = paginator.page(paginator.num_pages)
        
        return {
            'transactions': paginated.object_list,
            'page': paginated.number,
            'total_pages': paginator.num_pages,
            'total_count': paginator.count,
            'has_next': paginated.has_next(),
            'has_previous': paginated.has_previous(),
        }

    @classmethod
    def get_filter_options(cls, user):
        """Get available filter options for the user."""
        categories = Category.objects.filter(user=user).values('id', 'name')
        income_sources = IncomeSource.objects.filter(user=user).values('id', 'name')
        
        return {
            'categories': list(categories),
            'income_sources': list(income_sources),
            'statuses': [
                {'value': 'pending', 'label': 'Pending'},
                {'value': 'complete', 'label': 'Complete'},
            ],
        }

    @classmethod
    def get_transaction_detail(cls, user, transaction_type, transaction_id):
        """Get single transaction details."""
        if transaction_type == 'income':
            try:
                income = Income.objects.select_related('source').get(
                    id=transaction_id, user=user
                )
                return {
                    'id': str(income.id),
                    'type': 'income',
                    'name': income.source.name,
                    'source': income.source,
                    'amount': income.amount,
                    'converted_amount': income.converted_amount,
                    'currency': income.currency,
                    'exchange_rate': income.exchange_rate,
                    'date': income.transaction_date,
                    'status': income.status,
                    'description': income.description,
                }
            except Income.DoesNotExist:
                return None
        else:
            try:
                expense = Expense.objects.select_related('category', 'budget').get(
                    id=transaction_id, user=user
                )
                return {
                    'id': str(expense.id),
                    'type': 'expense',
                    'name': expense.category.name,
                    'category': expense.category,
                    'budget': expense.budget,
                    'amount': expense.amount,
                    'converted_amount': expense.converted_amount,
                    'currency': expense.currency,
                    'exchange_rate': expense.exchange_rate,
                    'date': expense.transaction_date,
                    'status': expense.status,
                    'description': expense.description,
                }
            except Expense.DoesNotExist:
                return None