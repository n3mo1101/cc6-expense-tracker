from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta, datetime
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
    recent_transactions = transactions[:10]
    
    # Prepare chart data (last 30 days)
    chart_data = prepare_chart_data(user, days=30)
    
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
        'chart_labels': json.dumps(chart_data['labels']),
        'chart_expenses': json.dumps(chart_data['expenses']),
        'chart_income': json.dumps(chart_data['income']),
    }
    
    return render(request, 'dashboard.html', context)


def prepare_chart_data(user, days=30):
    """Prepare data for spending trend chart"""
    today = timezone.now().date()
    start_date = today - timedelta(days=days)
    
    # Initialize data structures
    labels = []
    expenses_data = []
    income_data = []
    
    # Generate date range
    current_date = start_date
    while current_date <= today:
        labels.append(current_date.strftime('%b %d'))
        
        # Get expenses for this date
        daily_expenses = Expense.objects.filter(
            user=user,
            expense_date=current_date
        ).aggregate(total=Sum('amount'))['total'] or 0
        expenses_data.append(float(daily_expenses))
        
        # Get income for this date
        daily_income = Income.objects.filter(
            user=user,
            income_date=current_date
        ).aggregate(total=Sum('amount'))['total'] or 0
        income_data.append(float(daily_income))
        
        current_date += timedelta(days=1)
    
    return {
        'labels': labels,
        'expenses': expenses_data,
        'income': income_data
    }


# ===== PLACEHOLDER VIEWS FOR OTHER PAGES =====
@login_required
def transactions_view(request):
    """View all transactions (income + expenses)"""
    return render(request, 'transactions.html')


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