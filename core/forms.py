from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, UserChangeForm
from django.contrib.auth.models import User
from captcha.fields import CaptchaField
from .models import CustomUser  # Replace with your custom user model

class LoginForm(AuthenticationForm):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'placeholder': 'Username/Email'}),
        label="Username or Email"
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Password'}),
        label="Password"
    )
    captcha = CaptchaField(required=False)  # CAPTCHA shown dynamically after failed attempts

class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'Email'}),
        label="Email"
    )
    captcha = CaptchaField()

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2']


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'Email', 'class': 'form-control'}),
        label="Email"
    )
    captcha = CaptchaField(widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = CustomUser  # Use your custom user model
        fields = ['username', 'email', 'password1', 'password2']

        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Username', 'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Email', 'class': 'form-control'}),
            'password1': forms.PasswordInput(attrs={'placeholder': 'Password', 'class': 'form-control'}),
            'password2': forms.PasswordInput(attrs={'placeholder': 'Confirm Password', 'class': 'form-control'}),
        }

class UpdateProfileForm(forms.ModelForm):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
        label="Email"
    )
    profile_picture = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'}),
        label="Profile Picture"
    )

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'profile_picture']

class ProfileForm(UserChangeForm):
    profile_picture = forms.ChoiceField(
        choices=[],
        label="Profile Picture",
        widget=forms.RadioSelect,
        required=False,
    )

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'profile_picture']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dynamically populate the profile picture choices
        self.fields['profile_picture'].choices = [
            (f'profile_pics/{img}', img) for img in self.get_profile_pics()
        ]

    def get_profile_pics(self):
        import os
        profile_pics_dir = os.path.join('static', 'profile_pics')
        return os.listdir(profile_pics_dir)