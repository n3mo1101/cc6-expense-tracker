from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import UserProfile, ExpenseCategory, Budget, Expense, Income

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
    
    return render(request, 'expense_tracker/viewdata.html', context)