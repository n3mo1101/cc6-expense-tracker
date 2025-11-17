from django.contrib import admin
from django.urls import path
from expense_tracker import views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Authentication
    path('accounts/login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Main pages
    path('', views.dashboard_view, name='home'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('transactions/', views.transactions_view, name='transactions'),
    path('analytics/', views.analytics_view, name='analytics'),
    path('income/', views.income_view, name='income'),
    path('expenses/', views.expenses_view, name='expenses'),
    path('budgets/', views.budgets_view, name='budgets'),
    path('categories/', views.categories_view, name='categories'),
]