from django.urls import path
from expense_tracker import views

urlpatterns = [
    # Authentication
    path('accounts/login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Main pages
    path('', views.dashboard_view, name='home'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('transactions/', views.transactions_view, name='transactions'),
    path('budgets/', views.budgets_view, name='budgets'),
    path('income/', views.income_view, name='income'),
    path('expenses/', views.expenses_view, name='expenses'),
    path('categories/', views.categories_view, name='categories'),
    path('analytics/', views.analytics_view, name='analytics'),
    
    # Transaction API endpoints
    path('api/income/create/', views.create_income, name='create_income'),
    path('api/expense/create/', views.create_expense, name='create_expense'),
    path('api/transaction/<str:transaction_type>/<uuid:transaction_id>/', 
         views.get_transaction_detail, name='transaction_detail'),
    path('api/transaction/<str:transaction_type>/<uuid:transaction_id>/update/', 
         views.update_transaction, name='update_transaction'),
    path('api/transaction/<str:transaction_type>/<uuid:transaction_id>/delete/', 
         views.delete_transaction, name='delete_transaction'),
    path('api/transaction/<str:transaction_type>/<uuid:transaction_id>/complete/', 
         views.mark_transaction_complete, name='mark_transaction_complete'),
]