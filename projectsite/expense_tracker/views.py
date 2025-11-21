from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import json

from expense_tracker.services.dashboard_service import DashboardService


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


@login_required
def transactions_view(request):
    """View and manage transactions"""
    return render(request, 'transactions.html')


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