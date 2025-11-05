from django.contrib import admin
from django.contrib.auth.models import User
from .models import UserProfile, ExpenseCategory, Budget, Expense, Income, BudgetCategory
from django.utils.html import mark_safe

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'avatar_display', 'default_currency', 'timezone', 'avatar_preview')
    list_filter = ('default_currency', 'timezone')
    readonly_fields = ('avatar_preview',)
    
    def avatar_display(self, obj):
        # Display friendly avatar name instead of file path
        return dict(obj.AVATAR_CHOICES).get(obj.profile_picture, 'Default Avatar')
    avatar_display.short_description = 'Avatar'
    
    def avatar_preview(self, obj):
        # Show avatar preview in admin
        if obj.profile_picture:
            return mark_safe(f'<img src="{obj.avatar_url}" width="80" height="80" style="border-radius: 8px; border: 2px solid #ddd;" />')
        return "No avatar selected"
    avatar_preview.short_description = 'Avatar Preview'


@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_predefined', 'user', 'public_id', 'created_at')
    list_filter = ('is_predefined', 'created_at')
    search_fields = ('name', 'description', 'user__username', 'public_id')
    readonly_fields = ('public_id', 'created_at', 'updated_at')
    
    fieldsets = (
        (None, {'fields': ('name', 'public_id')}),
        ('Category Details', {'fields': ('description', 'is_predefined', 'user')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'total_amount', 'currency_code', 'start_date', 'end_date', 'is_active', 'public_id')
    list_filter = ('currency_code', 'start_date', 'end_date', 'created_at')
    search_fields = ('name', 'user__username', 'description', 'public_id')
    readonly_fields = ('public_id', 'created_at', 'updated_at')
    date_hierarchy = 'start_date'
    
    fieldsets = (
        (None, {'fields': ('name', 'user', 'public_id')}),
        ('Budget Details', {'fields': ('total_amount', 'currency_code', 'start_date', 'end_date', 'description')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('amount', 'currency_code', 'category', 'user', 'expense_date', 'is_recurring', 'public_id')
    list_filter = ('currency_code', 'category', 'expense_date', 'is_recurring', 'created_at')
    search_fields = ('description', 'user__username', 'category__name', 'public_id')
    readonly_fields = ('public_id', 'created_at', 'updated_at')
    date_hierarchy = 'expense_date'
    
    fieldsets = (
        (None, {'fields': ('user', 'category', 'public_id')}),
        ('Expense Details', {'fields': ('amount', 'currency_code', 'description', 'expense_date')}),
        ('Recurring Settings', {'fields': ('is_recurring', 'recurrence_rule', 'parent_expense')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(Income)
class IncomeAdmin(admin.ModelAdmin):
    list_display = ('amount', 'currency_code', 'source', 'user', 'income_date', 'is_recurring', 'public_id')
    list_filter = ('currency_code', 'source', 'income_date', 'is_recurring', 'created_at')
    search_fields = ('source', 'description', 'user__username', 'public_id')
    readonly_fields = ('public_id', 'created_at', 'updated_at')
    date_hierarchy = 'income_date'
    
    fieldsets = (
        (None, {'fields': ('user', 'source', 'public_id')}),
        ('Income Details', {'fields': ('amount', 'currency_code', 'description', 'income_date')}),
        ('Recurring Settings', {'fields': ('is_recurring', 'recurrence_rule')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(BudgetCategory)
class BudgetCategoryAdmin(admin.ModelAdmin):
    list_display = ('budget', 'category', 'allocated_amount', 'public_id', 'created_at')
    list_filter = ('budget', 'category', 'created_at')
    search_fields = ('budget__name', 'category__name', 'public_id')
    readonly_fields = ('public_id', 'created_at', 'updated_at')
    
    fieldsets = (
        (None, {'fields': ('budget', 'category', 'public_id')}),
        ('Allocation', {'fields': ('allocated_amount',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )


# Customize the default User admin if desired
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
