from decimal import Decimal
from django.db.models import Sum
from django.utils import timezone
from expense_tracker.models import Income, Expense, Budget, Category


class ProfileService:
    """Service for user profile operations"""
    
    @staticmethod
    def get_wallet_data(user):
        # Get wallet balance and totals
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
        
        return {
            'balance': balance,
            'currency': currency,
            'total_income': total_income,
            'total_expenses': total_expenses,
            'monthly_balance': monthly_balance,
        }
    
    @staticmethod
    def get_profile_stats(user):
        # Get quick stats for profile page
        active_budgets = Budget.objects.filter(user=user, status='active').count()
        total_transactions = (
            Income.objects.filter(user=user).count() + 
            Expense.objects.filter(user=user).count()
        )
        categories_count = Category.objects.filter(user=user).count()
        
        return {
            'active_budgets': active_budgets,
            'total_transactions': total_transactions,
            'categories_count': categories_count,
        }
    
    @staticmethod
    def get_current_avatar(user):
        if hasattr(user, 'profile') and user.profile.avatar:
            return user.profile.avatar
        return '/static/img/avatars/avatar1.png'
    
    @staticmethod
    def update_profile(user, data):
        # Update user fields
        user.first_name = data.get('first_name', user.first_name)
        user.last_name = data.get('last_name', user.last_name)
        user.email = data.get('email', user.email)
        user.save()
        
        # Update profile fields
        if hasattr(user, 'profile'):
            user.profile.primary_currency = data.get(
                'primary_currency', 
                user.profile.primary_currency
            )
            if 'avatar' in data:
                user.profile.avatar = data['avatar']
            user.profile.save()
        
        return user
    
    @staticmethod
    def change_password(user, current_password, new_password):
        # Verify current password
        if not user.check_password(current_password):
            return False, 'Current password is incorrect'
        
        # Validate new password
        if len(new_password) < 8:
            return False, 'Password must be at least 8 characters'
        
        # Set new password
        user.set_password(new_password)
        user.save()
        
        return True, None