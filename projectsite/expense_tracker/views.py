# expense_tracker/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .models import UserProfile, ExpenseCategory, Budget, Expense, Income
from .quickchart import QuickChartService

def home(request):
    """Simple home page that just says 'Home Page'"""
    return render(request, 'expense_tracker/home.html')

@login_required
def quickchart_dashboard(request):
    """Dashboard with QuickChart visualizations"""
    user = request.user
    
    # Get user data
    expenses = user.expenses.select_related('category')
    budgets = user.budgets.prefetch_related('budget_categories__category')
    incomes = user.incomes.all()
    
    # Generate QuickChart URLs
    chart_urls = {
        'monthly_trend': QuickChartService.generate_monthly_trend_chart(expenses),
        'category_pie': QuickChartService.generate_category_pie_chart(expenses),
        'budget_comparison': QuickChartService.generate_budget_comparison_chart(budgets, expenses),
        'income_vs_expenses': QuickChartService.generate_income_vs_expenses_chart(expenses, incomes),
    }
    
    # Basic statistics
    stats = {
        'total_expenses': sum(float(exp.amount) for exp in expenses),
        'total_income': sum(float(inc.amount) for inc in incomes),
        'expense_count': expenses.count(),
        'income_count': incomes.count(),
        'budget_count': budgets.count(),
    }
    stats['net_balance'] = stats['total_income'] - stats['total_expenses']
    
    context = {
        'user': user,
        'chart_urls': chart_urls,
        'stats': stats,
        'has_data': any(chart_urls.values()),
    }
    
    return render(request, 'expense_tracker/quickchart_dashboard.html', context)

@login_required
def view_data(request):
    """View to display all test data for the logged-in user"""
    user = request.user
    
    # Get all data for the current user
    try:
        profile = UserProfile.objects.get(user=user)
    except UserProfile.DoesNotExist:
        profile = None
    
    categories = ExpenseCategory.objects.all()
    budgets = Budget.objects.filter(user=user)
    expenses = Expense.objects.filter(user=user)
    incomes = Income.objects.filter(user=user)
    
    context = {
        'user': user,
        'profile': profile,
        'categories': categories,
        'budgets': budgets,
        'expenses': expenses,
        'incomes': incomes,
    }
    
    return render(request, 'expense_tracker/view_data.html', context)

from django.shortcuts import redirect
from django.contrib.auth import logout

def logout_view(request):
    """Simple logout view"""
    logout(request)
    return redirect('home')