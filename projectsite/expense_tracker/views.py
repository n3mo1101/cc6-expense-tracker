from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Sum, Count, Q, F, Value, CharField
from django.utils import timezone
from datetime import timedelta, datetime
from django.db import models
import json


# ===== AUTHENTICATION VIEWS =====
def login_view(request):
    """Handle user login"""
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'account/login.html')


def logout_view(request):
    """Handle user logout"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')


# ===== DASHBOARD/HOME VIEW =====
@login_required
def dashboard_view(request):
    """User dashboard displaying summary and key metrics"""
    return render(request, 'dashboard.html')


@login_required
def transactions_view(request):
    """View and manage transactions"""
    return render(request, 'transactions.html')


@login_required
def analytics_view(request):
    """Analytics and data visualization"""
    return render(request, 'analytics.html')


@login_required
def income_view(request):
    """Manage income"""
    return render(request, 'income.html')


@login_required
def expenses_view(request):
    """Manage expenses"""
    return render(request, 'expenses.html')


@login_required
def budgets_view(request):
    """Manage budgets"""
    return render(request, 'budgets.html')


@login_required
def categories_view(request):
    """Manage categories"""
    return render(request, 'categories.html')