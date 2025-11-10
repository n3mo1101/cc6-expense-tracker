from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required

# Display dashboard 
@login_required
def dashboard(request):
    context = {
        'page_title': 'Dashboard',
        # Add your data here
    }
    return render(request, 'index.html', context)

# Add your login view function
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('dashboard')  # Redirect to view data page after login
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'testing/login.html')

def logout_view(request):
    """Simple logout view"""
    logout(request)
    return redirect('login')