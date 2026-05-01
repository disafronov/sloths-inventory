from django.contrib.auth import views as auth_views
from django.urls import path
from django.views.i18n import set_language

from .views import UserPasswordChangeView

app_name = "common"

urlpatterns = [
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="login.html", redirect_authenticated_user=True
        ),
        name="login",
    ),
    path(
        "password/change/",
        UserPasswordChangeView.as_view(),
        name="password_change",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("i18n/setlang/", set_language, name="set_language"),
]
