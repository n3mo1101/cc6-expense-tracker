from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Sum, Count, Q, F, Value, CharField
from django.utils import timezone
from datetime import timedelta, datetime
from django.db import models
import json

from expense_tracker.models import (
    Expense, Income, Budget, BudgetCategory, 
    ExpenseCategory, UserProfile
)


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
    """Main dashboard with financial overview"""
    user = request.user
    today = timezone.now().date()
    
    # Get active budget
    active_budget = Budget.objects.filter(
        user=user,
        start_date__lte=today,
        end_date__gte=today
    ).first()
    
    # Calculate budget metrics
    total_budget = float(active_budget.total_amount) if active_budget else 0
    
    # Get expenses for current budget period
    if active_budget:
        expenses_in_period = Expense.objects.filter(
            user=user,
            expense_date__gte=active_budget.start_date,
            expense_date__lte=active_budget.end_date
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        days_remaining = (active_budget.end_date - today).days
    else:
        # If no active budget, use current month
        start_of_month = today.replace(day=1)
        expenses_in_period = Expense.objects.filter(
            user=user,
            expense_date__gte=start_of_month,
            expense_date__lte=today
        ).aggregate(total=Sum('amount'))['total'] or 0
        days_remaining = 0
    
    total_spent = float(expenses_in_period)
    available_budget = total_budget - total_spent
    budget_percentage = (total_spent / total_budget * 100) if total_budget > 0 else 0
    
    # Determine budget status
    if budget_percentage >= 90:
        budget_status = 'danger'
    elif budget_percentage >= 70:
        budget_status = 'warning'
    else:
        budget_status = 'success'
    
    # Get summary statistics (current month)
    start_of_month = today.replace(day=1)
    
    total_income = Income.objects.filter(
        user=user,
        income_date__gte=start_of_month
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    total_expenses = Expense.objects.filter(
        user=user,
        expense_date__gte=start_of_month
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    net_savings = float(total_income) - float(total_expenses)
    
    total_transactions = (
        Expense.objects.filter(user=user, expense_date__gte=start_of_month).count() +
        Income.objects.filter(user=user, income_date__gte=start_of_month).count()
    )
    
    # Get top spending categories
    top_categories = Expense.objects.filter(
        user=user,
        expense_date__gte=start_of_month
    ).values(
        'category__name'
    ).annotate(
        total=Sum('amount')
    ).order_by('-total')[:5]
    
    # Assign colors to categories
    category_colors = ['#667eea', '#f59e0b', '#10b981', '#ef4444', '#8b5cf6']
    categories_with_colors = []
    for idx, cat in enumerate(top_categories):
        categories_with_colors.append({
            'name': cat['category__name'],
            'amount': float(cat['total']),
            'color': category_colors[idx % len(category_colors)]
        })
    
    # Get recent transactions (last 10)
    recent_expenses = Expense.objects.filter(
        user=user
    ).select_related('category')[:5]
    
    recent_income = Income.objects.filter(
        user=user
    )[:5]
    
    # Combine and sort transactions
    transactions = []
    for expense in recent_expenses:
        transactions.append({
            'type': 'expense',
            'category': expense.category.name,
            'amount': float(expense.amount),
            'date': expense.expense_date,
            'description': expense.description
        })
    
    for income in recent_income:
        transactions.append({
            'type': 'income',
            'source': income.source,
            'amount': float(income.amount),
            'date': income.income_date,
            'description': income.description
        })
    
    # Sort by date descending
    transactions.sort(key=lambda x: x['date'], reverse=True)
    recent_transactions = transactions[:7]
    
    # # Prepare chart data (last 30 days)
    # chart_data = prepare_chart_data(user, days=30)
    
    # Prepare category data for donut chart
    category_chart_data = []
    category_chart_labels = []
    for cat in categories_with_colors:
        category_chart_data.append(cat['amount'])
        category_chart_labels.append(cat['name'])
    
    # Prepare monthly chart data (last 12 months)
    chart_data = prepare_chart_data(user, months=12)
    
    context = {
        'total_budget': f"{total_budget:.2f}",
        'total_spent': f"{total_spent:.2f}",
        'available_budget': f"{available_budget:.2f}",
        'budget_percentage': int(budget_percentage),
        'budget_status': budget_status,
        'days_remaining': days_remaining,
        'total_income': f"{float(total_income):.2f}",
        'total_expenses': f"{float(total_expenses):.2f}",
        'net_savings': f"{net_savings:.2f}",
        'total_transactions': total_transactions,
        'top_categories': categories_with_colors,
        'recent_transactions': recent_transactions,
        'monthly_labels': json.dumps(chart_data['labels']),
        'monthly_expenses': json.dumps(chart_data['expenses']),
        'category_data': json.dumps(category_chart_data),
        'category_labels': json.dumps(category_chart_labels),
    }
    
    return render(request, 'dashboard.html', context)


def prepare_chart_data(user, months=12):
    """Prepare monthly data for spending trend chart"""
    today = timezone.now().date()
    
    # Initialize data structures
    labels = []
    expenses_data = []
    
    # Generate last 12 months
    for i in range(months - 1, -1, -1):
        # Calculate the month
        month_date = today.replace(day=1) - timedelta(days=i * 30)
        month_start = month_date.replace(day=1)
        
        # Get last day of month
        if month_date.month == 12:
            month_end = month_date.replace(year=month_date.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            month_end = month_date.replace(month=month_date.month + 1, day=1) - timedelta(days=1)
        
        labels.append(month_start.strftime('%b'))
        
        # Get expenses for this month
        monthly_expenses = Expense.objects.filter(
            user=user,
            expense_date__gte=month_start,
            expense_date__lte=month_end
        ).aggregate(total=Sum('amount'))['total'] or 0
        expenses_data.append(float(monthly_expenses))
    
    return {
        'labels': labels,
        'expenses': expenses_data
    }


# ===== TRANSACTIONS VIEW =====
@login_required
def transactions_view(request):
    """View all transactions with filtering, sorting, and pagination (AJAX-enabled)"""
    user = request.user
    
    # Start with all transactions for the user
    from django.db.models import Value, CharField
    
    # Get expenses with type annotation
    expenses_qs = Expense.objects.filter(user=user).annotate(
        type=Value('expense', output_field=CharField()),
        category_name=F('category__name'),
        source_name=Value('', output_field=CharField())
    ).values(
        'id', 'amount', 'expense_date', 'type', 'category_name', 'source_name', 'description'
    )
    
    # Get income with type annotation
    income_qs = Income.objects.filter(user=user).annotate(
        type=Value('income', output_field=CharField()),
        category_name=Value('', output_field=CharField()),
        source_name=F('source')
    ).values(
        'id', 'amount', 'income_date', 'type', 'category_name', 'source_name', 'description'
    )
    
    # Combine querysets
    transactions = []
    
    for expense in expenses_qs:
        transactions.append({
            'id': expense['id'],
            'type': 'expense',
            'category': expense['category_name'],
            'source': '',
            'amount': expense['amount'],
            'date': expense['expense_date'],
            'description': expense.get('description', '')
        })
    
    for income in income_qs:
        transactions.append({
            'id': income['id'],
            'type': 'income',
            'category': '',
            'source': income['source_name'],
            'amount': income['amount'],
            'date': income['income_date'],
            'description': income.get('description', '')
        })
    
    # Apply filters
    search_query = request.GET.get('search', '').strip()
    type_filter = request.GET.get('type', '')
    
    # Filter by search query
    if search_query:
        transactions = [t for t in transactions if 
                       search_query.lower() in t['category'].lower() or 
                       search_query.lower() in t['source'].lower()]
    
    # Filter by type
    if type_filter:
        transactions = [t for t in transactions if t['type'] == type_filter]
    
    # Apply sorting
    sort_by = request.GET.get('sort', 'date_desc')
    
    if sort_by == 'date_asc':
        transactions.sort(key=lambda x: x['date'])
    elif sort_by == 'date_desc':
        transactions.sort(key=lambda x: x['date'], reverse=True)
    elif sort_by == 'amount_asc':
        transactions.sort(key=lambda x: float(x['amount']))
    elif sort_by == 'amount_desc':
        transactions.sort(key=lambda x: float(x['amount']), reverse=True)
    
    # Calculate summary stats
    total_income = sum(float(t['amount']) for t in transactions if t['type'] == 'income')
    total_expenses = sum(float(t['amount']) for t in transactions if t['type'] == 'expense')
    net_balance = total_income - total_expenses
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(transactions, 20)  # 20 transactions per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get all categories for filter dropdown
    categories = ExpenseCategory.objects.filter(
        Q(is_predefined=True) | Q(user=user)
    ).order_by('name')
    
    # Check if AJAX request
    if request.GET.get('ajax'):
        from django.http import JsonResponse
        from django.template.loader import render_to_string
        
        # Render partials
        html = render_to_string('partials/transaction_list.html', {
            'transactions': page_obj,
            'request': request
        })
        
        pagination_html = render_to_string('partials/pagination.html', {
            'page_obj': page_obj,
            'paginator': paginator,
            'is_paginated': paginator.num_pages > 1
        })
        
        return JsonResponse({
            'html': html,
            'pagination_html': pagination_html,
            'total_income': f"{total_income:.2f}",
            'total_expenses': f"{total_expenses:.2f}",
            'net_balance': f"{net_balance:.2f}",
            'total_count': len(transactions),
        })
    
    context = {
        'transactions': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'is_paginated': paginator.num_pages > 1,
        'categories': categories,
        'total_income': f"{total_income:.2f}",
        'total_expenses': f"{total_expenses:.2f}",
        'net_balance': f"{net_balance:.2f}",
        'total_count': len(transactions),
    }
    
    return render(request, 'transactions.html', context)


@login_required
def analytics_view(request):
    """Analytics and data visualization"""
    return render(request, 'analytics.html')


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