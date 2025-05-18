from django.urls import path
from django.contrib.auth import views as auth_views
from django.views.i18n import set_language
from . import views

app_name = "common"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("login/", auth_views.LoginView.as_view(template_name="login.html", redirect_authenticated_user=True), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("i18n/setlang/", set_language, name="set_language"),
] 