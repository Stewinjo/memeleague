from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from captcha.fields import CaptchaField
from .forms import RegisterForm, LoginForm, ProfileForm

# Home View
def home(request):
    """
    Display the home page with options to register, login, or play as a guest.
    """
    return render(request, "core/home.html")


# Login View
def memeleague_login(request):
    """
    Handle user login. Show CAPTCHA after 3 failed attempts.
    """
    failed_attempts = request.session.get('failed_login_attempts', 0)
    show_captcha = failed_attempts >= 3

    # Dynamically add CAPTCHA to the login form if needed
    class CaptchaLoginForm(LoginForm):
        captcha = CaptchaField()

    FormClass = CaptchaLoginForm if show_captcha else LoginForm

    if request.method == 'POST':
        form = FormClass(request, data=request.POST)
        if form.is_valid():
            user = authenticate(
                request,
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password']
            )
            if user:
                auth_login(request, user)
                request.session['failed_login_attempts'] = 0  # Reset failed attempts
                messages.success(request, f"Welcome back, {user.username}!")
                return redirect('core:home')
            else:
                # Increment failed login attempts
                request.session['failed_login_attempts'] = failed_attempts + 1
                messages.error(request, "Invalid credentials. Please try again.")
    else:
        form = FormClass()

    return render(request, 'core/login.html', {'form': form, 'show_captcha': show_captcha})


# Register View
def register(request):
    """
    Handle user registration. Automatically log the user in upon successful registration.
    """
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)  # Log the user in after registration
            messages.success(request, f"Account created successfully. Welcome, {user.username}!")
            return redirect('core:home')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = RegisterForm()

    return render(request, 'core/register.html', {'form': form})


# Guest Entry View
def guest_entry(request):
    """
    Allow users to enter as guests by choosing a username and avatar.
    """
    if request.method == "POST":
        username = request.POST.get("username")
        profile_pic = request.POST.get("profile_picture")

        # Validate input
        if not username or not profile_pic:
            messages.error(request, "Please provide a username and select an avatar.")
            return redirect("core:guest_entry")

        # Store guest data in session
        request.session["guest_username"] = username
        request.session["guest_profile_pic"] = profile_pic
        messages.success(request, f"Welcome, {username}! You are now logged in as a guest.")
        return redirect("lobby:join_or_create_lobby")

    # Predefined profile pictures for guests
    profile_pics = ["profile1.png", "profile2.png", "profile3.png"]
    return render(request, "core/guest_entry.html", {"profile_pics": profile_pics})


# Logout View
@login_required
def memeleague_logout(request):
    """
    Log the user out and redirect to the home page.
    """
    auth_logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect("core:home")

@login_required
def profile(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('core:profile')
    else:
        form = ProfileForm(instance=request.user)
    return render(request, 'core/profile.html', {'form': form})

@login_required
def delete_account(request):
    if request.method == 'POST':
        user = request.user
        user.delete()
        messages.success(request, "Account deleted successfully.")
        return redirect('core:home')
