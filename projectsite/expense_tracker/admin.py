from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, Wallet, Category, IncomeSource, Budget, RecurringTransaction, Income, Expense, CurrencyCache


# ============================================================================
# INLINE MODELS
# ============================================================================

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'


class WalletInline(admin.TabularInline):
    model = Wallet
    extra = 0
    readonly_fields = ['id', 'created_at', 'updated_at']


# ============================================================================
# CUSTOM USER ADMIN: Extended User admin with profile and wallets.
# ============================================================================

class UserAdmin(BaseUserAdmin):
    inlines = [UserProfileInline, WalletInline]
    list_display = ['username', 'email', 'get_primary_currency', 'is_active', 'date_joined']
    
    def get_primary_currency(self, obj):
        return obj.profile.primary_currency if hasattr(obj, 'profile') else '-'
    get_primary_currency.short_description = 'Currency'


# Re-register User with custom admin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


# ============================================================================
# USER PROFILE ADMIN
# ============================================================================

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'primary_currency', 'created_at']
    list_filter = ['primary_currency']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['id', 'created_at', 'updated_at']


# ============================================================================
# WALLET ADMIN
# ============================================================================

@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ['user', 'currency', 'balance', 'is_primary', 'updated_at']
    list_filter = ['currency', 'is_primary']
    search_fields = ['user__username']
    readonly_fields = ['id', 'created_at', 'updated_at']


# ============================================================================
# CATEGORY ADMIN
# ============================================================================

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'icon', 'created_at']
    list_filter = ['user']
    search_fields = ['name', 'user__username']
    readonly_fields = ['id', 'created_at', 'updated_at']


# ============================================================================
# INCOME SOURCE ADMIN
# ============================================================================

@admin.register(IncomeSource)
class IncomeSourceAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'icon', 'created_at']
    list_filter = ['user']
    search_fields = ['name', 'user__username']
    readonly_fields = ['id', 'created_at', 'updated_at']


# ============================================================================
# BUDGET ADMIN
# ============================================================================

@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'budget_type', 'amount', 'spent_amount', 'remaining', 'status']
    list_filter = ['budget_type', 'recurrence_pattern', 'status', 'currency']
    search_fields = ['name', 'user__username']
    readonly_fields = ['id', 'created_at', 'updated_at']
    filter_horizontal = ['category_filters']
    fieldsets = [
        (None, {
            'fields': ['id', 'user', 'name', 'budget_type']
        }),
        ('Amount', {
            'fields': ['amount', 'currency', 'spent_amount']
        }),
        ('Schedule', {
            'fields': ['recurrence_pattern', 'start_date', 'end_date', 'last_reset_date', 'status']
        }),
        ('Category Filter', {
            'fields': ['category_filters'],
            'classes': ['collapse']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    
    def remaining(self, obj):
        return obj.remaining_amount
    remaining.short_description = 'Remaining'


# ============================================================================
# RECURRING TRANSACTION ADMIN
# ============================================================================

@admin.register(RecurringTransaction)
class RecurringTransactionAdmin(admin.ModelAdmin):
    list_display = ['get_name', 'user', 'type', 'amount', 'currency', 'recurrence_pattern', 'is_active']
    list_filter = ['type', 'recurrence_pattern', 'is_active', 'currency']
    search_fields = ['category__name', 'income_source__name', 'user__username', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']
    fieldsets = [
        (None, {
            'fields': ['id', 'user', 'type', 'category', 'income_source', 'description']
        }),
        ('Amount', {
            'fields': ['amount', 'currency']
        }),
        ('Schedule', {
            'fields': ['recurrence_pattern', 'custom_interval_days', 'start_date', 'end_date', 'last_generated_date', 'is_active']
        }),
        ('Linked Budget', {
            'fields': ['budget'],
            'classes': ['collapse']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]

    def get_name(self, obj):
        if obj.category:
            return obj.category.name
        elif obj.income_source:
            return obj.income_source.name
        return '-'
    get_name.short_description = 'Category/Source'


# ============================================================================
# INCOME ADMIN
# ============================================================================

@admin.register(Income)
class IncomeAdmin(admin.ModelAdmin):
    list_display = ['get_source_name', 'user', 'amount', 'currency', 'transaction_date', 'status']
    list_filter = ['status', 'currency', 'source', 'transaction_date']
    search_fields = ['source__name', 'user__username', 'description']
    readonly_fields = ['id', 'converted_amount', 'created_at', 'updated_at']
    date_hierarchy = 'transaction_date'
    fieldsets = [
        (None, {
            'fields': ['id', 'user', 'source', 'description']
        }),
        ('Amount', {
            'fields': ['amount', 'currency', 'exchange_rate', 'converted_amount']
        }),
        ('Status', {
            'fields': ['transaction_date', 'status']
        }),
        ('Recurring', {
            'fields': ['recurring_transaction'],
            'classes': ['collapse']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]

    def get_source_name(self, obj):
        return obj.source.name
    get_source_name.short_description = 'Source'


# ============================================================================
# EXPENSE ADMIN
# ============================================================================

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['get_category_name', 'user', 'amount', 'currency', 'transaction_date', 'status', 'budget']
    list_filter = ['status', 'currency', 'category', 'transaction_date']
    search_fields = ['category__name', 'user__username', 'description']
    readonly_fields = ['id', 'converted_amount', 'created_at', 'updated_at']
    date_hierarchy = 'transaction_date'
    fieldsets = [
        (None, {
            'fields': ['id', 'user', 'category', 'description']
        }),
        ('Amount', {
            'fields': ['amount', 'currency', 'exchange_rate', 'converted_amount']
        }),
        ('Status', {
            'fields': ['transaction_date', 'status']
        }),
        ('Links', {
            'fields': ['budget', 'recurring_transaction'],
            'classes': ['collapse']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]

    def get_category_name(self, obj):
        return obj.category.name
    get_category_name.short_description = 'Category'


# ============================================================================
# CURRENCY CACHE ADMIN
# ============================================================================

@admin.register(CurrencyCache)
class CurrencyCacheAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'exchange_rate', 'last_updated']
    search_fields = ['code', 'name']
    readonly_fields = ['last_updated']
    ordering = ['code']


# ============================================================================
# ADMIN SITE CUSTOMIZATION
# ============================================================================

admin.site.site_header = 'MoneyLens Admin'
admin.site.site_title = 'MoneyLens'
admin.site.index_title = 'Dashboard'