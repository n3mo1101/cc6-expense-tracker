from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('viewdata/', views.view_data, name='view_data'),
    path('charts/', views.quickchart_dashboard, name='charts'),  # New charts page
    path('login/', auth_views.LoginView.as_view(template_name='expense_tracker/login.html'), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('upload-receipt/', views.upload_receipt, name='upload_receipt'),
    path('confirm-receipt/', views.confirm_receipt, name='confirm_receipt'),
]