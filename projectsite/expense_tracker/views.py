from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import json

from expense_tracker.models import Income, Expense, Category, IncomeSource, Budget

from django.http import JsonResponse
from django.views.decorators.http import require_POST
from decimal import Decimal

from expense_tracker.services.dashboard_service import DashboardService
from expense_tracker.services.transactions_service import TransactionsService
from expense_tracker.services.currency_service import CurrencyService

# ===== AUTHENTICATION VIEWS =====
def login_view(request):
    """Handle user login"""
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'account/login.html')


def logout_view(request):
    """Handle user logout"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')


# ===== DASHBOARD/HOME VIEW =====
@login_required
def dashboard_view(request):
    """User dashboard displaying summary and key metrics"""
    user = request.user
    
    # Get all dashboard data from service
    dashboard_data = DashboardService.get_dashboard_data(user)
    
    # Get data for create modals
    from expense_tracker.models import Category, IncomeSource, Budget
    from expense_tracker.services.currency_service import CurrencyService
    
    categories = Category.objects.filter(user=user)
    income_sources = IncomeSource.objects.filter(user=user)
    budgets = Budget.objects.filter(user=user, status='active')
    currencies = CurrencyService.get_all_currencies()
    
    context = {
        # Wallet & Progress Bar
        'wallet': dashboard_data['wallet'],
        
        # 4 Summary Cards
        'summary': dashboard_data['monthly_summary'],
        
        # Charts (JSON for JavaScript)
        'spending_trends': json.dumps(dashboard_data['spending_trends']),
        'current_month_trends': json.dumps(dashboard_data['current_month_trends']),
        'category_breakdown': json.dumps(dashboard_data['category_breakdown']),
        
        # Recent Transactions
        'recent_transactions': dashboard_data['recent_transactions'],
        
        # Modal data
        'categories': categories,
        'income_sources': income_sources,
        'budgets': budgets,
        'currencies': currencies,
        'primary_currency': user.profile.primary_currency if hasattr(user, 'profile') else 'PHP',
    }
    
    return render(request, 'dashboard.html', context)


# ===== TRANSACTIONS VIEWS =====
@login_required
def transactions_view(request):
    """View and manage all transactions"""
    user = request.user
    
    # Get filter parameters
    filters = {
        'search': request.GET.get('search', ''),
        'type': request.GET.get('type', ''),
        'status': request.GET.get('status', ''),
    }
    page = request.GET.get('page', 1)
    
    # Get sorting parameter (format: 'date_desc', 'date_asc', 'amount_desc', 'amount_asc')
    sort = request.GET.get('sort', 'date_desc')
    
    # Validate sort parameter
    valid_sorts = ('date_desc', 'date_asc', 'amount_desc', 'amount_asc')
    if sort not in valid_sorts:
        sort = 'date_desc'
    
    # Check if AJAX request
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    # Get transactions - pass for_json=True for AJAX requests
    result = TransactionsService.get_combined_transactions(
        user, filters=filters, page=page, per_page=15, for_json=is_ajax, sort=sort
    )
    
    if is_ajax:
        return JsonResponse(result)
    
    # Get filter options
    filter_options = TransactionsService.get_filter_options(user)
    
    # Get categories and sources for create forms
    categories = Category.objects.filter(user=user)
    income_sources = IncomeSource.objects.filter(user=user)
    budgets = Budget.objects.filter(user=user, status='active')
    currencies = CurrencyService.get_all_currencies()
    
    context = {
        'transactions': result['transactions'],
        'page': result['page'],
        'total_pages': result['total_pages'],
        'total_count': result['total_count'],
        'has_next': result['has_next'],
        'has_previous': result['has_previous'],
        'filters': filters,
        'filter_options': filter_options,
        'categories': categories,
        'income_sources': income_sources,
        'budgets': budgets,
        'currencies': currencies,
        'primary_currency': user.profile.primary_currency if hasattr(user, 'profile') else 'PHP',
        'current_sort': sort,
    }
    
    return render(request, 'transactions.html', context)


@login_required
def analytics_view(request):
    """Analytics and data visualization"""
    user = request.user
    
    # Reuse the same chart functions for analytics page
    context = {
        'spending_trends': json.dumps(
            DashboardService.get_spending_trends(user, months=12)
        ),
        'current_month_trends': json.dumps(
            DashboardService.get_current_month_trends(user)
        ),
        'category_breakdown': json.dumps(
            DashboardService.get_category_breakdown(user)
        ),
    }
    
    return render(request, 'analytics.html', context)


@login_required
def income_view(request):
    """Manage income"""
    return render(request, 'income.html')


@login_required
def expenses_view(request):
    """Manage expenses"""
    return render(request, 'expenses.html')


# ===== BUDGETS VIEW =====
@login_required
def budgets_view(request):
    """View and manage budgets"""
    user = request.user
    
    from django.utils import timezone
    from django.db.models import Sum
    from datetime import timedelta
    
    today = timezone.now().date()
    
    # Get all budgets
    budgets = Budget.objects.filter(user=user).prefetch_related('category_filters')
    
    active_budgets = []
    inactive_budgets = []
    
    for budget in budgets:
        # Calculate spent amount from actual transactions
        spent_amount = calculate_budget_spent(budget, user)
        remaining_amount = budget.amount - spent_amount
        percentage_used = (spent_amount / budget.amount * 100) if budget.amount > 0 else 0
        is_overspent = spent_amount > budget.amount
        
        # Calculate additional fields for display
        budget_data = {
            'id': str(budget.id),
            'name': budget.name,
            'amount': budget.amount,
            'currency': budget.currency,
            'spent_amount': spent_amount,
            'remaining_amount': max(remaining_amount, 0),
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
            budget_data['daily_allowance'] = budget.remaining_amount / days_remaining if days_remaining > 0 else 0
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
    
    # Get categories and currencies for forms
    categories = Category.objects.filter(user=user)
    currencies = CurrencyService.get_all_currencies()
    
    context = {
        'active_budgets': active_budgets,
        'inactive_budgets': inactive_budgets,
        'categories': categories,
        'currencies': currencies,
        'primary_currency': user.profile.primary_currency if hasattr(user, 'profile') else 'PHP',
    }
    
    return render(request, 'budgets.html', context)


# ===== BUDGET HELPER FUNCTIONS =====
def calculate_budget_spent(budget, user):
    """Calculate total spent amount for a budget from transactions"""
    from django.db.models import Sum
    
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


# ===== BUDGET API ENDPOINTS =====
@login_required
def get_budget_detail(request, budget_id):
    """Get budget details for modal"""
    user = request.user
    
    try:
        budget = Budget.objects.prefetch_related('category_filters').get(id=budget_id, user=user)
        
        # Calculate spent from transactions
        spent_amount = calculate_budget_spent(budget, user)
        remaining_amount = budget.amount - spent_amount
        percentage_used = (spent_amount / budget.amount * 100) if budget.amount > 0 else 0
        
        data = {
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
        
        return JsonResponse({'success': True, 'data': data})
    
    except Budget.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Budget not found'}, status=404)


@login_required
@require_POST
def create_budget(request):
    """Create new budget"""
    user = request.user
    
    try:
        data = json.loads(request.body)
        
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
        
        return JsonResponse({
            'success': True,
            'message': 'Budget created successfully',
            'id': str(budget.id)
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_POST
def update_budget(request, budget_id):
    """Update existing budget"""
    user = request.user
    
    try:
        data = json.loads(request.body)
        budget = Budget.objects.get(id=budget_id, user=user)
        
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
        
        return JsonResponse({
            'success': True,
            'message': 'Budget updated successfully'
        })
    
    except Budget.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Budget not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_POST
def toggle_budget_status(request, budget_id):
    """Toggle budget active/inactive status"""
    user = request.user
    
    try:
        data = json.loads(request.body)
        budget = Budget.objects.get(id=budget_id, user=user)
        
        new_status = data.get('status', 'inactive' if budget.status == 'active' else 'active')
        budget.status = new_status
        budget.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Budget {"activated" if new_status == "active" else "deactivated"} successfully'
        })
    
    except Budget.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Budget not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_POST
def delete_budget(request, budget_id):
    """Delete budget"""
    user = request.user
    
    try:
        budget = Budget.objects.get(id=budget_id, user=user)
        budget.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Budget deleted successfully'
        })
    
    except Budget.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Budget not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)



# ===== CATEGORIES VIEW =====
@login_required
def categories_view(request):
    """View and manage categories and income sources"""
    user = request.user
    from django.db.models import Count, Sum
    
    # Get categories with transaction counts and totals
    categories = Category.objects.filter(user=user).annotate(
        expense_count=Count('expenses'),
        total_spent=Sum('expenses__converted_amount')
    ).order_by('name')
    
    # Get income sources with transaction counts and totals
    income_sources = IncomeSource.objects.filter(user=user).annotate(
        income_count=Count('incomes'),
        total_earned=Sum('incomes__converted_amount')
    ).order_by('name')
    
    context = {
        'categories': categories,
        'income_sources': income_sources,
        'primary_currency': user.profile.primary_currency if hasattr(user, 'profile') else 'PHP',
    }
    
    return render(request, 'categories.html', context)


# ===== CATEGORY API ENDPOINTS =====
@login_required
def get_category_detail(request, category_id):
    """Get category details"""
    user = request.user
    from django.db.models import Count, Sum
    
    try:
        category = Category.objects.filter(user=user).annotate(
            expense_count=Count('expenses'),
            total_spent=Sum('expenses__converted_amount')
        ).get(id=category_id)
        
        data = {
            'id': str(category.id),
            'name': category.name,
            'icon': category.icon,
            'expense_count': category.expense_count,
            'total_spent': str(category.total_spent or Decimal('0.00')),
        }
        
        return JsonResponse({'success': True, 'data': data})
    
    except Category.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Category not found'}, status=404)


@login_required
@require_POST
def create_category(request):
    """Create new category"""
    user = request.user
    
    try:
        data = json.loads(request.body)
        
        category = Category.objects.create(
            user=user,
            name=data['name'],
            icon=data.get('icon') or None,
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Category created successfully',
            'id': str(category.id)
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_POST
def update_category(request, category_id):
    """Update existing category"""
    user = request.user
    
    try:
        data = json.loads(request.body)
        category = Category.objects.get(id=category_id, user=user)
        
        category.name = data.get('name', category.name)
        category.icon = data.get('icon') or None
        category.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Category updated successfully'
        })
    
    except Category.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Category not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_POST
def delete_category(request, category_id):
    """Delete category"""
    user = request.user
    
    try:
        category = Category.objects.get(id=category_id, user=user)
        category.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Category deleted successfully'
        })
    
    except Category.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Category not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# ===== INCOME SOURCE API ENDPOINTS =====
@login_required
def get_income_source_detail(request, source_id):
    """Get income source details"""
    user = request.user
    from django.db.models import Count, Sum
    
    try:
        source = IncomeSource.objects.filter(user=user).annotate(
            income_count=Count('incomes'),
            total_earned=Sum('incomes__converted_amount')
        ).get(id=source_id)
        
        data = {
            'id': str(source.id),
            'name': source.name,
            'icon': source.icon,
            'income_count': source.income_count,
            'total_earned': str(source.total_earned or Decimal('0.00')),
        }
        
        return JsonResponse({'success': True, 'data': data})
    
    except IncomeSource.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Income source not found'}, status=404)


@login_required
@require_POST
def create_income_source(request):
    """Create new income source"""
    user = request.user
    
    try:
        data = json.loads(request.body)
        
        source = IncomeSource.objects.create(
            user=user,
            name=data['name'],
            icon=data.get('icon') or None,
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Income source created successfully',
            'id': str(source.id)
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_POST
def update_income_source(request, source_id):
    """Update existing income source"""
    user = request.user
    
    try:
        data = json.loads(request.body)
        source = IncomeSource.objects.get(id=source_id, user=user)
        
        source.name = data.get('name', source.name)
        source.icon = data.get('icon') or None
        source.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Income source updated successfully'
        })
    
    except IncomeSource.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Income source not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_POST
def delete_income_source(request, source_id):
    """Delete income source"""
    user = request.user
    
    try:
        source = IncomeSource.objects.get(id=source_id, user=user)
        source.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Income source deleted successfully'
        })
    
    except IncomeSource.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Income source not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# ===== Transaction CRUD Endpoints =====
@login_required
@require_POST
def create_income(request):
    """Create new income transaction (with optional recurring)"""
    user = request.user
    
    try:
        data = json.loads(request.body)
        
        source = IncomeSource.objects.get(id=data['source_id'], user=user)
        amount = Decimal(data['amount'])
        currency = data['currency']
        
        # Get user's primary currency safely
        try:
            primary_currency = user.profile.primary_currency
        except Exception:
            primary_currency = 'PHP'
        
        # Get conversion if different currency
        converted_amount = amount
        exchange_rate = None
        
        if currency != primary_currency:
            try:
                conversion = CurrencyService.convert(
                    amount, currency, primary_currency
                )
                converted_amount = conversion['converted_amount']
                exchange_rate = conversion['rate']
            except Exception:
                converted_amount = amount
        
        # Check if this is a recurring transaction
        is_recurring = data.get('is_recurring', False)
        recurring_transaction = None
        
        if is_recurring:
            from expense_tracker.models import RecurringTransaction
            
            recurrence_pattern = data.get('recurrence_pattern', 'monthly')
            end_date = data.get('recurrence_end_date') or None
            
            recurring_transaction = RecurringTransaction.objects.create(
                user=user,
                type='income',
                income_source=source,
                amount=amount,
                currency=currency,
                description=data.get('description', ''),
                recurrence_pattern=recurrence_pattern,
                start_date=data['transaction_date'],
                end_date=end_date,
                is_active=True,
            )
        
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
        
        return JsonResponse({
            'success': True,
            'message': 'Income created successfully' + (' (recurring)' if is_recurring else ''),
            'id': str(income.id)
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_POST
def create_expense(request):
    """Create new expense transaction (with optional recurring)"""
    user = request.user
    
    try:
        data = json.loads(request.body)
        
        category = Category.objects.get(id=data['category_id'], user=user)
        amount = Decimal(data['amount'])
        currency = data['currency']
        
        # Get user's primary currency safely
        try:
            primary_currency = user.profile.primary_currency
        except Exception:
            primary_currency = 'PHP'
        
        # Get budget if provided
        budget = None
        if data.get('budget_id'):
            budget = Budget.objects.get(id=data['budget_id'], user=user)
        
        # Get conversion if different currency
        converted_amount = amount
        exchange_rate = None
        
        if currency != primary_currency:
            try:
                conversion = CurrencyService.convert(
                    amount, currency, primary_currency
                )
                converted_amount = conversion['converted_amount']
                exchange_rate = conversion['rate']
            except Exception:
                converted_amount = amount
        
        # Check if this is a recurring transaction
        is_recurring = data.get('is_recurring', False)
        recurring_transaction = None
        
        if is_recurring:
            from expense_tracker.models import RecurringTransaction
            
            recurrence_pattern = data.get('recurrence_pattern', 'monthly')
            end_date = data.get('recurrence_end_date') or None
            
            recurring_transaction = RecurringTransaction.objects.create(
                user=user,
                type='expense',
                category=category,
                amount=amount,
                currency=currency,
                description=data.get('description', ''),
                recurrence_pattern=recurrence_pattern,
                start_date=data['transaction_date'],
                end_date=end_date,
                is_active=True,
                budget=budget,
            )
        
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
        
        return JsonResponse({
            'success': True,
            'message': 'Expense created successfully' + (' (recurring)' if is_recurring else ''),
            'id': str(expense.id)
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_POST
def update_transaction(request, transaction_type, transaction_id):
    """Update existing transaction"""
    user = request.user
    
    try:
        data = json.loads(request.body)
        
        if transaction_type == 'income':
            transaction = Income.objects.get(id=transaction_id, user=user)
            
            if 'source_id' in data:
                transaction.source = IncomeSource.objects.get(id=data['source_id'], user=user)
        else:
            transaction = Expense.objects.get(id=transaction_id, user=user)
            
            if 'category_id' in data:
                transaction.category = Category.objects.get(id=data['category_id'], user=user)
            
            if 'budget_id' in data:
                if data['budget_id']:
                    transaction.budget = Budget.objects.get(id=data['budget_id'], user=user)
                else:
                    transaction.budget = None
        
        # Update common fields
        if 'amount' in data:
            amount = Decimal(data['amount'])
            currency = data.get('currency', transaction.currency)
            
            transaction.amount = amount
            transaction.currency = currency
            
            if currency != user.profile.primary_currency:
                conversion = CurrencyService.convert(
                    amount, currency, user.profile.primary_currency
                )
                transaction.converted_amount = conversion['converted_amount']
                transaction.exchange_rate = conversion['rate']
            else:
                transaction.converted_amount = amount
                transaction.exchange_rate = None
        
        if 'transaction_date' in data:
            transaction.transaction_date = data['transaction_date']
        
        if 'description' in data:
            transaction.description = data['description']
        
        if 'status' in data:
            transaction.status = data['status']
        
        transaction.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Transaction updated successfully'
        })
    
    except (Income.DoesNotExist, Expense.DoesNotExist):
        return JsonResponse({'success': False, 'error': 'Transaction not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_POST
def delete_transaction(request, transaction_type, transaction_id):
    """Delete transaction"""
    user = request.user
    
    try:
        if transaction_type == 'income':
            transaction = Income.objects.get(id=transaction_id, user=user)
        else:
            transaction = Expense.objects.get(id=transaction_id, user=user)
        
        transaction.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Transaction deleted successfully'
        })
    
    except (Income.DoesNotExist, Expense.DoesNotExist):
        return JsonResponse({'success': False, 'error': 'Transaction not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_POST
def mark_transaction_complete(request, transaction_type, transaction_id):
    """Mark transaction as complete"""
    user = request.user
    
    try:
        if transaction_type == 'income':
            transaction = Income.objects.get(id=transaction_id, user=user)
        else:
            transaction = Expense.objects.get(id=transaction_id, user=user)
        
        transaction.status = 'complete'
        transaction.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Transaction marked as complete'
        })
    
    except (Income.DoesNotExist, Expense.DoesNotExist):
        return JsonResponse({'success': False, 'error': 'Transaction not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
def get_transaction_detail(request, transaction_type, transaction_id):
    """Get transaction details for modal"""
    user = request.user
    
    detail = TransactionsService.get_transaction_detail(user, transaction_type, transaction_id)
    
    if detail is None:
        return JsonResponse({'success': False, 'error': 'Transaction not found'}, status=404)
    
    # Convert for JSON
    detail['date'] = detail['date'].isoformat()
    detail['amount'] = str(detail['amount'])
    if detail['converted_amount']:
        detail['converted_amount'] = str(detail['converted_amount'])
    if detail['exchange_rate']:
        detail['exchange_rate'] = str(detail['exchange_rate'])
    
    if detail['type'] == 'income':
        detail['source_id'] = str(detail['source'].id)
        del detail['source']
    else:
        detail['category_id'] = str(detail['category'].id)
        del detail['category']
        if detail['budget']:
            detail['budget_id'] = str(detail['budget'].id)
        del detail['budget']
    
    return JsonResponse({'success': True, 'data': detail})


# ===== PROFILE VIEW =====
@login_required
def profile_view(request):
    """User profile page"""
    user = request.user
    from django.db.models import Sum
    from django.utils import timezone
    
    # Get wallet balance
    today = timezone.now().date()
    first_of_month = today.replace(day=1)
    
    try:
        currency = user.profile.primary_currency
    except Exception:
        currency = 'PHP'
    
    # All-time totals
    total_income = Income.objects.filter(
        user=user,
        status='complete'
    ).aggregate(total=Sum('converted_amount'))['total'] or Decimal('0.00')
    
    total_expenses = Expense.objects.filter(
        user=user,
        status='complete'
    ).aggregate(total=Sum('converted_amount'))['total'] or Decimal('0.00')
    
    balance = total_income - total_expenses
    
    # This month
    monthly_income = Income.objects.filter(
        user=user,
        status='complete',
        transaction_date__gte=first_of_month,
        transaction_date__lte=today
    ).aggregate(total=Sum('converted_amount'))['total'] or Decimal('0.00')
    
    monthly_expenses = Expense.objects.filter(
        user=user,
        status='complete',
        transaction_date__gte=first_of_month,
        transaction_date__lte=today
    ).aggregate(total=Sum('converted_amount'))['total'] or Decimal('0.00')
    
    monthly_balance = monthly_income - monthly_expenses
    
    # Quick stats
    active_budgets = Budget.objects.filter(user=user, status='active').count()
    total_transactions = Income.objects.filter(user=user).count() + Expense.objects.filter(user=user).count()
    categories_count = Category.objects.filter(user=user).count()
    
    # Get currencies
    currencies = CurrencyService.get_all_currencies()
    
    context = {
        'wallet': {
            'balance': balance,
            'currency': currency,
            'total_income': total_income,
            'total_expenses': total_expenses,
            'monthly_balance': monthly_balance,
        },
        'stats': {
            'active_budgets': active_budgets,
            'total_transactions': total_transactions,
            'categories_count': categories_count,
        },
        'currencies': currencies,
    }
    
    return render(request, 'profile.html', context)


# ===== PROFILE API ENDPOINTS =====
@login_required
@require_POST
def update_profile(request):
    """Update user profile"""
    user = request.user
    
    try:
        data = json.loads(request.body)
        
        # Update user fields
        user.first_name = data.get('first_name', user.first_name)
        user.last_name = data.get('last_name', user.last_name)
        user.email = data.get('email', user.email)
        user.save()
        
        # Update profile fields
        if hasattr(user, 'profile'):
            user.profile.primary_currency = data.get('primary_currency', user.profile.primary_currency)
            user.profile.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Profile updated successfully'
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_POST
def change_password(request):
    """Change user password"""
    from django.contrib.auth import update_session_auth_hash
    
    user = request.user
    
    try:
        data = json.loads(request.body)
        
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        # Verify current password
        if not user.check_password(current_password):
            return JsonResponse({'success': False, 'error': 'Current password is incorrect'}, status=400)
        
        # Validate new password
        if len(new_password) < 8:
            return JsonResponse({'success': False, 'error': 'Password must be at least 8 characters'}, status=400)
        
        # Set new password
        user.set_password(new_password)
        user.save()
        
        # Keep user logged in after password change
        update_session_auth_hash(request, user)
        
        return JsonResponse({
            'success': True,
            'message': 'Password changed successfully'
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)