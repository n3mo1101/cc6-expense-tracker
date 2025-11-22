"""
Dashboard Service
Reusable functions for dashboard data and charts.

Usage:
    from expense_tracker.services.dashboard_service import DashboardService
    
    data = DashboardService.get_dashboard_data(user)
"""

from decimal import Decimal
from datetime import timedelta, date
from django.db.models import Sum, Q
from django.db.models.functions import TruncDate, TruncMonth
from django.utils import timezone

from expense_tracker.models import (
    Wallet, Income, Expense, Budget, Category
)


def safe_decimal(value):
    """Safely convert to Decimal, return 0 if None."""
    if value is None:
        return Decimal('0.00')
    return value


class DashboardService:
    """Service for dashboard-related data and calculations."""

    @classmethod
    def get_dashboard_data(cls, user):
        """Get all dashboard data in one call."""
        return {
            'wallet': cls.get_wallet_summary(user),
            'monthly_summary': cls.get_monthly_summary(user),
            'spending_trends': cls.get_spending_trends(user, months=12),
            'current_month_trends': cls.get_current_month_trends(user),
            'category_breakdown': cls.get_category_breakdown(user),
            'recent_transactions': cls.get_recent_transactions(user, limit=7),
        }

    @classmethod
    def get_wallet_summary(cls, user):
        """
        Get wallet balance and spending progress for current month.
        Balance = current month's income - expenses
        Progress = percentage of income spent this month.
        """
        # Get user's primary currency
        try:
            currency = user.profile.primary_currency
        except Exception:
            currency = 'PHP'
        
        # Get current month's income and expenses
        today = timezone.now().date()
        first_of_month = today.replace(day=1)
        
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
        
        # Balance = this month's income - expenses
        balance = monthly_income - monthly_expenses
        
        # Calculate progress (expenses as percentage of income)
        if monthly_income > 0:
            progress = min((monthly_expenses / monthly_income) * 100, 100)
        else:
            progress = 100 if monthly_expenses > 0 else 0
        
        return {
            'balance': balance,
            'currency': currency,
            'monthly_income': monthly_income,
            'monthly_expenses': monthly_expenses,
            'progress': round(progress, 1),
        }

    @classmethod
    def get_monthly_summary(cls, user):
        """
        Get the 4 summary cards data:
        - Total Income (this month)
        - Total Expenses (this month)
        - Net Savings (calculated balance)
        - Active Budgets count
        """
        today = timezone.now().date()
        first_of_month = today.replace(day=1)
        
        # Get user's primary currency
        try:
            currency = user.profile.primary_currency
        except Exception:
            currency = 'PHP'
        
        # Total Income this month
        total_income = Income.objects.filter(
            user=user,
            status='complete',
            transaction_date__gte=first_of_month,
            transaction_date__lte=today
        ).aggregate(total=Sum('converted_amount'))['total'] or Decimal('0.00')
        
        # Total Expenses this month
        total_expenses = Expense.objects.filter(
            user=user,
            status='complete',
            transaction_date__gte=first_of_month,
            transaction_date__lte=today
        ).aggregate(total=Sum('converted_amount'))['total'] or Decimal('0.00')
        
        # Net Savings (all time income - all time expenses)
        all_income = Income.objects.filter(
            user=user,
            status='complete'
        ).aggregate(total=Sum('converted_amount'))['total'] or Decimal('0.00')
        
        all_expenses = Expense.objects.filter(
            user=user,
            status='complete'
        ).aggregate(total=Sum('converted_amount'))['total'] or Decimal('0.00')
        
        net_savings = all_income - all_expenses
        
        # Active Budgets count
        active_budgets = Budget.objects.filter(user=user, status='active').count()
        
        return {
            'total_income': total_income,
            'total_expenses': total_expenses,
            'net_savings': net_savings,
            'active_budgets': active_budgets,
            'currency': currency,
        }

    @classmethod
    def get_spending_trends(cls, user, months=12):
        """
        Get monthly spending trends for the last N months.
        Returns data formatted for Chart.js line chart.
        """
        today = timezone.now().date()
        start_date = today - timedelta(days=months * 30)
        
        # Get monthly expenses grouped by month
        monthly_data = Expense.objects.filter(
            user=user,
            status='complete',
            transaction_date__gte=start_date,
            transaction_date__lte=today
        ).annotate(
            month=TruncMonth('transaction_date')
        ).values('month').annotate(
            total=Sum('converted_amount')
        ).order_by('month')
        
        # Build complete month list (fill gaps with 0)
        labels = []
        data = []
        
        current = start_date.replace(day=1)
        # Handle both datetime and date objects
        monthly_dict = {}
        for item in monthly_data:
            month_val = item['month']
            # Convert to date if it's a datetime object
            if hasattr(month_val, 'date'):
                month_key = month_val.date()
            else:
                month_key = month_val
            monthly_dict[month_key] = item['total']
        
        while current <= today:
            month_key = current.replace(day=1)
            labels.append(current.strftime('%b %Y'))
            data.append(float(monthly_dict.get(month_key, 0)))
            
            # Move to next month
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1)
            else:
                current = current.replace(month=current.month + 1)
        
        return {
            'labels': labels,
            'data': data,
        }

    @classmethod
    def get_current_month_trends(cls, user):
        """
        Get daily spending trends for the current month.
        X-axis shows weekly intervals for aesthetics.
        Returns data formatted for Chart.js line chart.
        """
        today = timezone.now().date()
        first_of_month = today.replace(day=1)
        
        # Get daily expenses for current month
        daily_data = Expense.objects.filter(
            user=user,
            status='complete',
            transaction_date__gte=first_of_month,
            transaction_date__lte=today
        ).values('transaction_date').annotate(
            total=Sum('converted_amount')
        ).order_by('transaction_date')
        
        # Build complete day list
        labels = []
        data = []
        tooltip_labels = []
        
        # Build dict with date as key
        daily_dict = {}
        for item in daily_data:
            day_key = item['transaction_date']
            daily_dict[day_key] = item['total'] or Decimal('0.00')
        
        current = first_of_month
        while current <= today:
            # Show label only on week intervals (day 1, 8, 15, 22, 29)
            if current.day in [1, 8, 15, 22, 29]:
                labels.append(current.strftime('%b %d'))
            else:
                labels.append('')
            
            tooltip_labels.append(current.strftime('%b %d, %Y'))
            data.append(float(daily_dict.get(current, 0)))
            current += timedelta(days=1)
        
        return {
            'labels': labels,
            'tooltip_labels': tooltip_labels,
            'data': data,
        }

    @classmethod
    def get_category_breakdown(cls, user, top_n=4):
        """
        Get categorized spending for current month.
        Returns top N categories + 'Others' for Chart.js donut chart.
        """
        today = timezone.now().date()
        first_of_month = today.replace(day=1)
        
        # Get expenses by category for current month
        category_data = Expense.objects.filter(
            user=user,
            status='complete',
            transaction_date__gte=first_of_month,
            transaction_date__lte=today
        ).values(
            'category__name'
        ).annotate(
            total=Sum('converted_amount')
        ).order_by('-total')
        
        labels = []
        data = []
        colors = [
            '#4F46E5',  # Indigo
            '#10B981',  # Emerald
            '#F59E0B',  # Amber
            '#EF4444',  # Red
            '#6B7280',  # Gray (for Others)
        ]
        
        others_total = Decimal('0.00')
        
        for i, item in enumerate(category_data):
            if i < top_n:
                labels.append(item['category__name'] or 'Uncategorized')
                data.append(float(item['total']))
            else:
                others_total += item['total']
        
        # Add 'Others' if there are more categories
        if others_total > 0:
            labels.append('Others')
            data.append(float(others_total))
        
        # Ensure we have enough colors
        chart_colors = colors[:len(labels)]
        
        return {
            'labels': labels,
            'data': data,
            'colors': chart_colors,
        }

    @classmethod
    def get_recent_transactions(cls, user, limit=7):
        """
        Get recent transactions (both income and expenses combined).
        Returns list sorted by transaction_date descending.
        """
        # Get recent incomes (include pending too for recent list)
        incomes = Income.objects.filter(
            user=user
        ).select_related('source').order_by('-transaction_date')[:limit]
        
        # Get recent expenses
        expenses = Expense.objects.filter(
            user=user
        ).select_related('category').order_by('-transaction_date')[:limit]
        
        # Combine and format
        transactions = []
        
        for income in incomes:
            transactions.append({
                'type': 'income',
                'name': income.source.name if income.source else 'Unknown',
                'amount': safe_decimal(income.amount),
                'converted_amount': safe_decimal(income.converted_amount) if income.converted_amount else None,
                'currency': income.currency or 'PHP',
                'date': income.transaction_date,
                'status': income.status,
                'description': income.description or '',
                'icon': income.source.icon if income.source else None,
            })
        
        for expense in expenses:
            transactions.append({
                'type': 'expense',
                'name': expense.category.name if expense.category else 'Unknown',
                'amount': safe_decimal(expense.amount),
                'converted_amount': safe_decimal(expense.converted_amount) if expense.converted_amount else None,
                'currency': expense.currency or 'PHP',
                'date': expense.transaction_date,
                'status': expense.status,
                'description': expense.description or '',
                'icon': expense.category.icon if expense.category else None,
            })
        
        # Sort by date descending and limit
        transactions.sort(key=lambda x: x['date'], reverse=True)
        
        return transactions[:limit]