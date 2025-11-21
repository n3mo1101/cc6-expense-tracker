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
    }
    
    return render(request, 'dashboard.html', context)


# ===== TRANSACTIONS VIEW =====
@login_required
def transactions_view(request):
    """View and manage all transactions"""
    user = request.user
    
    # Get filter parameters
    filters = {
        'search': request.GET.get('search', ''),
        'category': request.GET.get('category', ''),
        'status': request.GET.get('status', ''),
        'sort_by': request.GET.get('sort_by', 'date'),
        'sort_order': request.GET.get('sort_order', 'desc'),
    }
    page = request.GET.get('page', 1)
    
    # Get transactions
    result = TransactionsService.get_combined_transactions(
        user, filters=filters, page=page, per_page=15
    )
    
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
        'primary_currency': user.profile.primary_currency,
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


@login_required
def budgets_view(request):
    """Manage budgets"""
    return render(request, 'budgets.html')


@login_required
def categories_view(request):
    """Manage categories"""
    return render(request, 'categories.html')


# ===== CRUD FUNCTIONS =====
@login_required
@require_POST
def create_income(request):
    """Create new income transaction"""
    user = request.user
    
    try:
        data = json.loads(request.body)
        
        source = IncomeSource.objects.get(id=data['source_id'], user=user)
        amount = Decimal(data['amount'])
        currency = data['currency']
        
        # Get conversion if different currency
        converted_amount = amount
        exchange_rate = None
        
        if currency != user.profile.primary_currency:
            conversion = CurrencyService.convert(
                amount, currency, user.profile.primary_currency
            )
            converted_amount = conversion['converted_amount']
            exchange_rate = conversion['rate']
        
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
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Income created successfully',
            'id': str(income.id)
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_POST
def create_expense(request):
    """Create new expense transaction"""
    user = request.user
    
    try:
        data = json.loads(request.body)
        
        category = Category.objects.get(id=data['category_id'], user=user)
        amount = Decimal(data['amount'])
        currency = data['currency']
        
        # Get budget if provided
        budget = None
        if data.get('budget_id'):
            budget = Budget.objects.get(id=data['budget_id'], user=user)
        
        # Get conversion if different currency
        converted_amount = amount
        exchange_rate = None
        
        if currency != user.profile.primary_currency:
            conversion = CurrencyService.convert(
                amount, currency, user.profile.primary_currency
            )
            converted_amount = conversion['converted_amount']
            exchange_rate = conversion['rate']
        
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
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Expense created successfully',
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