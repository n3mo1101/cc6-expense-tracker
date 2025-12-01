from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json

from expense_tracker.models import Income, Expense, Category, IncomeSource, Budget

# Import services
from expense_tracker.services.dashboard_service import DashboardService
from expense_tracker.services.transactions_service import TransactionsService
from expense_tracker.services.currency_service import CurrencyService
from expense_tracker.services.budget_service import BudgetService
from expense_tracker.services.category_service import CategoryService
from expense_tracker.services.income_source_service import IncomeSourceService
from expense_tracker.services.transaction_service import TransactionService
from expense_tracker.services.profile_service import ProfileService


# ===== LANDING PAGE VIEW =====
def landing_view(request):
    """Landing page - redirects to dashboard if authenticated"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'landing-page.html')


# ===== AUTHENTICATION VIEWS =====
def logout_view(request):
    """Handle user logout"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('account_login')


# ===== DASHBOARD/HOME VIEW =====
@login_required
def dashboard_view(request):
    """User dashboard displaying summary and key metrics"""
    user = request.user
    
    # Get all dashboard data from service
    dashboard_data = DashboardService.get_dashboard_data(user)
    
    # Get data for create modals
    categories = Category.objects.filter(user=user)
    income_sources = IncomeSource.objects.filter(user=user)
    budgets = Budget.objects.filter(user=user, status='active')
    currencies = CurrencyService.get_all_currencies()
    
    context = {
        'wallet': dashboard_data['wallet'],
        'summary': dashboard_data['monthly_summary'],
        'spending_trends': json.dumps(dashboard_data['spending_trends']),
        'current_month_trends': json.dumps(dashboard_data['current_month_trends']),
        'category_breakdown': json.dumps(dashboard_data['category_breakdown']),
        'recent_transactions': dashboard_data['recent_transactions'],
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
    sort = request.GET.get('sort', 'date_desc')
    
    # Validate sort parameter
    valid_sorts = ('date_desc', 'date_asc', 'amount_desc', 'amount_asc')
    if sort not in valid_sorts:
        sort = 'date_desc'
    
    # Check if AJAX request
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    # Get transactions
    result = TransactionsService.get_combined_transactions(
        user, filters=filters, page=page, per_page=15, for_json=is_ajax, sort=sort
    )
    
    if is_ajax:
        return JsonResponse(result)
    
    # Get filter options and form data
    filter_options = TransactionsService.get_filter_options(user)
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
    
    # Get budgets with display data
    active_budgets, inactive_budgets = BudgetService.get_all_budgets_display(user)
    
    # Get form data
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


# ===== BUDGET API ENDPOINTS =====
@login_required
def get_budget_detail(request, budget_id):
    """Get budget details for modal"""
    try:
        budget = Budget.objects.prefetch_related('category_filters').get(
            id=budget_id, user=request.user
        )
        data = BudgetService.get_budget_detail_json(budget, request.user)
        return JsonResponse({'success': True, 'data': data})
    except Budget.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Budget not found'}, status=404)


@login_required
@require_POST
def create_budget(request):
    """Create new budget"""
    try:
        data = json.loads(request.body)
        budget = BudgetService.create_budget(request.user, data)
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
    try:
        data = json.loads(request.body)
        budget = Budget.objects.get(id=budget_id, user=request.user)
        BudgetService.update_budget(budget, request.user, data)
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
    try:
        data = json.loads(request.body)
        budget = Budget.objects.get(id=budget_id, user=request.user)
        new_status = data.get('status')
        _, message = BudgetService.toggle_budget_status(budget, new_status)
        return JsonResponse({'success': True, 'message': message})
    except Budget.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Budget not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_POST
def delete_budget(request, budget_id):
    """Delete budget"""
    try:
        budget = Budget.objects.get(id=budget_id, user=request.user)
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
    
    # Get categories and income sources with stats
    categories = CategoryService.get_categories_with_stats(user)
    income_sources = IncomeSourceService.get_income_sources_with_stats(user)
    
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
    try:
        category = CategoryService.get_categories_with_stats(request.user).get(id=category_id)
        data = CategoryService.get_category_detail_json(category)
        return JsonResponse({'success': True, 'data': data})
    except Category.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Category not found'}, status=404)


@login_required
@require_POST
def create_category(request):
    """Create new category"""
    try:
        data = json.loads(request.body)
        category = CategoryService.create_category(request.user, data)
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
    try:
        data = json.loads(request.body)
        category = Category.objects.get(id=category_id, user=request.user)
        CategoryService.update_category(category, data)
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
    try:
        category = Category.objects.get(id=category_id, user=request.user)
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
    try:
        source = IncomeSourceService.get_income_sources_with_stats(request.user).get(id=source_id)
        data = IncomeSourceService.get_income_source_detail_json(source)
        return JsonResponse({'success': True, 'data': data})
    except IncomeSource.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Income source not found'}, status=404)


@login_required
@require_POST
def create_income_source(request):
    """Create new income source"""
    try:
        data = json.loads(request.body)
        source = IncomeSourceService.create_income_source(request.user, data)
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
    try:
        data = json.loads(request.body)
        source = IncomeSource.objects.get(id=source_id, user=request.user)
        IncomeSourceService.update_income_source(source, data)
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
    try:
        source = IncomeSource.objects.get(id=source_id, user=request.user)
        source.delete()
        return JsonResponse({
            'success': True,
            'message': 'Income source deleted successfully'
        })
    except IncomeSource.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Income source not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# ===== TRANSACTION CRUD ENDPOINTS =====
@login_required
@require_POST
def create_income(request):
    """Create new income transaction (with optional recurring)"""
    try:
        data = json.loads(request.body)
        income, is_recurring = TransactionService.create_income(request.user, data)
        message = 'Income created successfully' + (' (recurring)' if is_recurring else '')
        return JsonResponse({
            'success': True,
            'message': message,
            'id': str(income.id)
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_POST
def create_expense(request):
    """Create new expense transaction (with optional recurring)"""
    try:
        data = json.loads(request.body)
        expense, is_recurring = TransactionService.create_expense(request.user, data)
        message = 'Expense created successfully' + (' (recurring)' if is_recurring else '')
        return JsonResponse({
            'success': True,
            'message': message,
            'id': str(expense.id)
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_POST
def update_transaction(request, transaction_type, transaction_id):
    """Update existing transaction"""
    try:
        data = json.loads(request.body)
        
        if transaction_type == 'income':
            transaction = Income.objects.get(id=transaction_id, user=request.user)
            TransactionService.update_income(transaction, request.user, data)
        else:
            transaction = Expense.objects.get(id=transaction_id, user=request.user)
            TransactionService.update_expense(transaction, request.user, data)
        
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
    try:
        if transaction_type == 'income':
            transaction = Income.objects.get(id=transaction_id, user=request.user)
        else:
            transaction = Expense.objects.get(id=transaction_id, user=request.user)
        
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
    try:
        if transaction_type == 'income':
            transaction = Income.objects.get(id=transaction_id, user=request.user)
        else:
            transaction = Expense.objects.get(id=transaction_id, user=request.user)
        
        TransactionService.mark_complete(transaction)
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
    detail = TransactionsService.get_transaction_detail(
        request.user, transaction_type, transaction_id
    )
    
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
    
    # Get wallet and stats from service
    wallet = ProfileService.get_wallet_data(user)
    stats = ProfileService.get_profile_stats(user)
    current_avatar = ProfileService.get_current_avatar(user)
    
    # Get currencies
    currencies = CurrencyService.get_all_currencies()
    
    context = {
        'wallet': wallet,
        'stats': stats,
        'currencies': currencies,
        'current_avatar': current_avatar,
    }
    
    return render(request, 'profile.html', context)


# ===== PROFILE API ENDPOINTS =====
@login_required
@require_POST
def update_profile(request):
    """Update user profile"""
    try:
        data = json.loads(request.body)
        ProfileService.update_profile(request.user, data)
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
    try:
        data = json.loads(request.body)
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        success, error = ProfileService.change_password(
            request.user, current_password, new_password
        )
        
        if not success:
            return JsonResponse({'success': False, 'error': error}, status=400)
        
        # Keep user logged in after password change
        update_session_auth_hash(request, request.user)
        
        return JsonResponse({
            'success': True,
            'message': 'Password changed successfully'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)