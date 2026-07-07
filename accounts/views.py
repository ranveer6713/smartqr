"""
Accounts app views.
Handles faculty login, logout, and password change.
"""

from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .forms import FacultyLoginForm, FacultyPasswordChangeForm, FacultyRegistrationForm


def faculty_register(request):
    """
    Faculty registration view.
    Redirects to dashboard if already authenticated.
    """
    if request.user.is_authenticated:
        return redirect('dashboard:home')

    if request.method == 'POST':
        form = FacultyRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Log the user in directly after registration
            login(request, user)
            messages.success(request, f'Account created successfully! Welcome, {user.first_name or user.username}!')
            return redirect('dashboard:home')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = FacultyRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


def faculty_login(request):
    """
    Faculty login view.
    Redirects to dashboard if already authenticated.
    """
    # If the user is already logged in, send them to dashboard
    if request.user.is_authenticated:
        return redirect('dashboard:home')

    if request.method == 'POST':
        form = FacultyLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
            # Respect 'next' parameter for protected page redirects
            next_url = request.GET.get('next', 'dashboard:home')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password. Please try again.')
    else:
        form = FacultyLoginForm()

    return render(request, 'accounts/login.html', {'form': form})


def faculty_logout(request):
    """Log out the current faculty and redirect to login page."""
    if request.method == 'POST':
        logout(request)
        messages.info(request, 'You have been logged out successfully.')
    return redirect('accounts:login')


@login_required
def change_password(request):
    """
    Allow faculty to change their password.
    Updates session to prevent logout after password change.
    """
    if request.method == 'POST':
        form = FacultyPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Keep the user logged in after password change
            update_session_auth_hash(request, user)
            messages.success(request, 'Password changed successfully!')
            return redirect('dashboard:home')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = FacultyPasswordChangeForm(request.user)

    return render(request, 'accounts/change_password.html', {'form': form})
