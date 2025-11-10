from django.contrib import admin
from django.urls import path
from expense_tracker import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('index/', views.dashboard, name='dashboard'),

    path('', views.login_view, name='home'),  # Make login the home page
    path('login/', views.login_view, name='login'),
     path('logout/', views.logout_view, name='logout'),
]