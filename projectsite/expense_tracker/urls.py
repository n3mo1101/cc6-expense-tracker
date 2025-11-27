from django.urls import path
from expense_tracker import views

urlpatterns = [
    # Landing page
    path('', views.landing_view, name='home'),

    # Authentication
    path('accounts/login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),

    # Main pages
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

     # Budget API endpoints
     path('api/budget/create/', views.create_budget, name='create_budget'),
     path('api/budget/<uuid:budget_id>/', views.get_budget_detail, name='budget_detail'),
     path('api/budget/<uuid:budget_id>/update/', views.update_budget, name='update_budget'),
     path('api/budget/<uuid:budget_id>/toggle-status/', views.toggle_budget_status, name='toggle_budget_status'),
     path('api/budget/<uuid:budget_id>/delete/', views.delete_budget, name='delete_budget'),

     # Category API endpoints
     path('api/category/create/', views.create_category, name='create_category'),
     path('api/category/<uuid:category_id>/', views.get_category_detail, name='category_detail'),
     path('api/category/<uuid:category_id>/update/', views.update_category, name='update_category'),
     path('api/category/<uuid:category_id>/delete/', views.delete_category, name='delete_category'),

     # Income Source API endpoints
     path('api/income-source/create/', views.create_income_source, name='create_income_source'),
     path('api/income-source/<uuid:source_id>/', views.get_income_source_detail, name='income_source_detail'),
     path('api/income-source/<uuid:source_id>/update/', views.update_income_source, name='update_income_source'),
     path('api/income-source/<uuid:source_id>/delete/', views.delete_income_source, name='delete_income_source'),

     # Profile page
     path('profile/', views.profile_view, name='profile'),

     # Profile API endpoints
     path('api/profile/update/', views.update_profile, name='update_profile'),
     path('api/profile/change-password/', views.change_password, name='change_password'),
]