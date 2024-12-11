from django.urls import path
from django.views.generic import TemplateView
from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path('impressum/', TemplateView.as_view(template_name='core/impressum.html'), name='impressum'),
    path('privacy-policy/', TemplateView.as_view(template_name='core/privacy_policy.html'), name='privacy_policy'),
    path('terms-of-service/', TemplateView.as_view(template_name='core/terms_of_service.html'), name='terms_of_service'),
    path("register/", views.register, name="register"),
    path("login/", views.login, name="login"),
    path("logout/", views.logout, name="logout"),
    path('profile/', views.profile, name='profile'),
    path('delete-account/', views.delete_account, name='delete_account'),
    path("save-profile/", views.save_profile, name="save_profile"),
    path("generate-username/", views.generate_username_wrapper, name="generate_username"),
]
