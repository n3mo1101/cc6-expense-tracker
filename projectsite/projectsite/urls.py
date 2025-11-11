from django.contrib import admin
from django.urls import path
from expense_tracker import views
from expense_tracker.views import HomePageView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.HomePageView.as_view(), name='home'),

    path('accounts/login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]