from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.decorators import login_required

# Add your login view function
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('view_data')  # Redirect to view data page after login
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'testing/login.html')

# Keep your existing view_data function but add login_required
@login_required
def view_data(request):
    # For now, use dummy data to test the template
    context = {
        'user_username': request.user.username,
        'profile': None,  # You can add real profile data later
        'categories': [],  # Empty list for now
    }
    return render(request, 'testing/viewdata.html', context)