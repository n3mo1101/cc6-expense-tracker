from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.views.generic.list import ListView
from expense_tracker.models import Expense

# Home page view
class HomePageView(LoginRequiredMixin, ListView):
    model = Expense
    context_object_name = 'home'
    template_name = 'home.html'


# Add your login view function
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('home')  # Redirect to view data page after login
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'account/login.html')


def logout_view(request):
    """Simple logout view"""
    logout(request)
    return redirect('login')

def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("login")
    else:
        form = UserCreationForm()

    return render(request, "register.html", {"form": form})