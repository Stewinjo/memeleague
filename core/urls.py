from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("register/", views.register, name="register"),
    path("login/", views.memeleague_login, name="login"),
    path("guest/", views.guest_entry, name="guest_entry"),
    path("logout/", views.memeleague_logout, name="logout"),
    path('profile/', views.profile, name='profile'),
    path('delete_account/', views.delete_account, name='delete_account'),
]
