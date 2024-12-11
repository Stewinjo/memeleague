from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User, AnonymousUser
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import JsonResponse, HttpRequest
from django.conf import settings
from django.urls import reverse
from captcha.fields import CaptchaField
from .forms import RegisterForm, LoginForm, ProfileForm
from core.dataclasses import GuestUser
import random, os

#-------- Helper Functions --------

# Helper function to generate a random username
def generate_username():
    username_prefix = ["Turbo","Hyper","Mega","Ultra","Super","Power","Lightning","Sonic","Electro","Quantum","Astro","Cosmic","Rocket","Nitro","Atomic","Mystic","Shadow","Phantom","Ghostly","Magic","Enchanted","Arcane","Lunar","Stellar","Solar","Frost","Ember","Crimson","Radiant","Obsidian","Wacky","Loopy","Quirky","Silly","Zany","Bouncy","Chunky","Sassy","Funky","Jolly","Stormy","Fiery","Windy","Rainy","Thunder","Frosty","Glacier","Blooming","Sunny","Bloomy","Robo","Cyber","Techno","Pixel","Circuit","Nano","Gear","Mecha","Droid","Steam","Iron","Steel","Titan","King","Queen","Alpha","Omega","Apex","Savage","Prime","Neon","Glitter","Velvet","Crystal","Midnight","Velvet","Spicy","Golden","Rusty","Funky"]
    username_main = ["Aye-Aye", "Okapi", "Kudu", "Quokka", "Nyala", "Oryx", "Numbat", "Wombat", "Takin", "Dhole", "Kia", "Saola", "Civet", "Koel", "Geoduck", "Onager", "Binturong", "Cassowary", "Pudu", "Quoll", "Ratel", "Agouti", "Fossa", "Kinkajou", "Jacana", "Turaco", "Manakin", "Dik-dik", "Markhor", "Pangolin", "Gerenuk", "Seriema", "Hihi", "Toddycat", "Galah", "Kakapo", "Lyrebird", "Tamaraw", "Tarsier", "Axolotl", "Anole", "Coati", "Grison", "Malayan", "Bongo", "Tapir", "Margay", "Zorilla", "Barbary", "Palila", "Dog", "Cat", "Rabbit", "Cow", "Horse", "Sheep", "Pig", "Goat", "Chicken", "Duck", "Goose", "Turkey", "Deer", "Bear", "Fox", "Wolf", "Tiger", "Lion", "Leopard", "Cheetah", "Elephant", "Giraffe", "Zebra", "Kangaroo", "Panda", "Penguin", "Dolphin", "Shark", "Whale", "Seal", "Otter", "Raccoon", "Squirrel", "Hedgehog", "Bat", "Monkey", "Gorilla", "Chimpanzee", "Lizard", "Snake", "Frog", "Toad", "Turtle", "Crocodile", "Alligator", "Eagle", "Owl", "Parrot", "Flamingo", "Peacock"]
    username_suffix = ["mancer","zilla","tron","pocalypse","lord","ster","kin","ish","master","beast","tail","face","squatch","fluff","feet","mon","ling","sprout","boom","snout","wing","whip","quake","bloom","scream","buzz","grin"]

    return f"{random.choice(username_prefix)}{random.choice(username_main)}{random.choice(username_suffix)}"

# Helper function to fetch available profile pictures
def get_available_profile_pics():
    # Path to the profile pictures directory
    profile_pic_dir = os.path.join(settings.STATICFILES_DIRS[0], "images", "profile_pics")

    # Fetch all image files from the directory
    return [f for f in os.listdir(profile_pic_dir) if f.endswith((".png", ".jpg", ".jpeg", ".gif"))]

# Function to generate a random username
def generate_username_wrapper(request:HttpRequest):
    random_username = generate_username()
    return JsonResponse({"username": random_username})

def user_is_authenticated(request:HttpRequest) -> bool:
    return request.user.is_authenticated or GuestUser.is_valid_guest_user(request)

#-------- View Functions --------

# Home View
def home(request:HttpRequest):
    """
    Handle homepage logic and guest login. Redirect to the 'next' URL if provided.
    """
    next_url = request.GET.get('next', None)

    # Redirect logged-in or guest users directly to the "next" URL if provided
    if next_url and (request.user.is_authenticated or "guest_username" in request.session):
        return redirect(next_url)

    # Handle POST request for guest login
    if request.method == "POST" and "continue_as_guest" in request.POST:
        guestUser = GuestUser(
            username = request.POST.get("username"),
            profile_picture = request.POST.get("profile_picture")
        )

        next_url = request.POST.get("next")  # Preserve the next parameter

        if not guestUser.is_valid():
            # Return error not valid
            return render(request, "core/home.html", {
                "error": "Please provide a username and select a profile picture.",
                "random_username": generate_username(),
                "profile_pics": get_available_profile_pics(),
                "selected_profile_pic": profile_picture,
                "next": next_url,
            })

        # Store guest data in the session
        guestUser.save_guest_user_to_session(request)

        # Redirect to the "next" URL if provided, or to the default lobby page
        return redirect(next_url or "lobby:join")

    # Handle GET request for rendering the home page
    profile_pics = get_available_profile_pics()
    selected_profile_pic = f"/static/images/profile_pics/{random.choice(profile_pics)}" if profile_pics else ""

    context = {
        "random_username": generate_username(),
        "profile_pics": profile_pics,
        "selected_profile_pic": selected_profile_pic,
        "next": next_url,  # Pass next URL to the template
    }
    return render(request, "core/home.html", context)

# Login View
def login(request:HttpRequest):
    """
    Handle user login. Show CAPTCHA after 3 failed attempts.
    Redirect to the 'next' URL if provided after successful login.
    """
    # Retrieve the "next" parameter from the GET request
    next_url = request.GET.get('next', None)

    # Retrieve the number of failed attempts from the session
    failed_attempts = request.session.get('failed_login_attempts', 0)
    show_captcha = failed_attempts >= 3

    # Dynamically add CAPTCHA to the login form if needed
    class CaptchaLoginForm(AuthenticationForm):
        captcha = CaptchaField()

    # Use the form with CAPTCHA only after 3 failed attempts
    FormClass = CaptchaLoginForm if show_captcha else AuthenticationForm

    if request.method == 'POST':
        form = FormClass(request, data=request.POST)
        if form.is_valid():
            user = authenticate(
                request,
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password']
            )
            if user:
                # Successful login
                auth_login(request, user)
                request.session['failed_login_attempts'] = 0  # Reset failed attempts
                messages.success(request, f"Welcome back, {user.username}!")

                # Validate the next URL
                next_redirect = request.POST.get("next")
                if not next_redirect or next_redirect == "None":
                    next_redirect = reverse("core:home")

                return redirect(next_redirect)
            else:
                # Increment failed login attempts
                request.session['failed_login_attempts'] = failed_attempts + 1
                messages.error(request, "Invalid credentials. Please try again.")
    else:
        form = FormClass()

    return render(request, 'core/login.html', {'form': form, 'show_captcha': show_captcha, 'next': next_url})



# Register View
def register(request:HttpRequest):
    """
    Handle user registration. Automatically log the user in upon successful registration
    and redirect to the 'next' URL if provided.
    """
    # Retrieve the "next" parameter from the request
    next_url = request.GET.get('next', None)

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)  # Log the user in after registration
            messages.success(request, f"Account created successfully. Welcome, {user.username}!")
            # Redirect to the "next" URL if provided, or the homepage
            return redirect(request.POST.get("next", "core:home"))
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = RegisterForm()

    return render(request, 'core/register.html', {'form': form, 'next': next_url})

# Logout View
@login_required
def logout(request:HttpRequest):
    """
    Log the user out and redirect to the home page.
    """
    auth_logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect("core:home")

@login_required
def profile(request:HttpRequest):
    """
    Handle user profile updates, including selecting a profile picture.
    """
    # Available profile pictures
    profile_pictures = os.listdir(os.path.join('static', 'images', 'profile_pics'))

    if request.method == "POST":
        form = ProfileForm(request.POST, instance=request.user)
        selected_picture = request.POST.get('profile_picture')

        if form.is_valid():
            user = form.save(commit=False)
            if selected_picture in profile_pictures:
                user.profile_picture = selected_picture
            user.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('core:profile')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ProfileForm(instance=request.user)

    return render(request, 'core/profile.html', {'form': form, 'profile_pictures': profile_pictures})

@login_required
def delete_account(request:HttpRequest):
    if request.method == 'POST':
        user = request.user
        user.delete()
        messages.success(request, "Account deleted successfully.")
        return redirect('core:home')

def save_profile(request:HttpRequest):
    if request.method == "POST":
        username = request.POST.get("username")
        profile_picture = request.POST.get("profile_picture")

        # Store the selected username and profile picture in the session
        request.session["guest_username"] = username
        request.session["guest_profile_picture"] = profile_picture

        # Redirect to the lobby or any desired page
        return redirect("lobby:join_or_create_lobby")

    return redirect("core:home")
