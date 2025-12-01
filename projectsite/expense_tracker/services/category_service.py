from decimal import Decimal
from django.db.models import Count, Sum
from expense_tracker.models import Category


class CategoryService:
    """Service for category operations"""
    
    @staticmethod
    def get_categories_with_stats(user):
        # Get all categories with transaction counts and totals
        return Category.objects.filter(user=user).annotate(
            expense_count=Count('expenses'),
            total_spent=Sum('expenses__converted_amount')
        ).order_by('name')
    
    @staticmethod
    def get_category_detail_json(category):
        # Get category details formatted for JSON response
        return {
            'id': str(category.id),
            'name': category.name,
            'icon': category.icon,
            'expense_count': getattr(category, 'expense_count', 0),
            'total_spent': str(getattr(category, 'total_spent', Decimal('0.00')) or Decimal('0.00')),
        }
    
    @staticmethod
    def create_category(user, data):
        # Create a new category
        return Category.objects.create(
            user=user,
            name=data['name'],
            icon=data.get('icon') or '/static/img/icons/icon-default.png',
        )
    
    @staticmethod
    def update_category(category, data):
        # Update an existing category
        category.name = data.get('name', category.name)
        category.icon = data.get('icon', category.icon)
        category.save()
        
        return category
