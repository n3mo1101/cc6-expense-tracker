from django.contrib import admin
from django.urls import path
from expense_tracker import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('testing/viewdata/', views.view_data, name='view_data'),
    path('login/', views.login_view, name='login'),
    path('', views.login_view, name='home'),  # Make login the home page
]