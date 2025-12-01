from decimal import Decimal
from django.db.models import Count, Sum
from expense_tracker.models import IncomeSource


class IncomeSourceService:
    """Service for income source operations"""
    
    @staticmethod
    def get_income_sources_with_stats(user):
        # Get all income sources with transaction counts and totals
        return IncomeSource.objects.filter(user=user).annotate(
            income_count=Count('incomes'),
            total_earned=Sum('incomes__converted_amount')
        ).order_by('name')
    
    @staticmethod
    def get_income_source_detail_json(source):
        # Get income source details formatted for JSON response
        return {
            'id': str(source.id),
            'name': source.name,
            'icon': source.icon,
            'income_count': getattr(source, 'income_count', 0),
            'total_earned': str(getattr(source, 'total_earned', Decimal('0.00')) or Decimal('0.00')),
        }
    
    @staticmethod
    def create_income_source(user, data):
        # Create a new income source
        return IncomeSource.objects.create(
            user=user,
            name=data['name'],
            icon=data.get('icon') or '/static/img/icons/icon-default.png',
        )
    
    @staticmethod
    def update_income_source(source, data):
        # Update an existing income source
        source.name = data.get('name', source.name)
        source.icon = data.get('icon', source.icon)
        source.save()
        
        return source
