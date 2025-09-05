from django.urls import path
from .views import register, login, refresh, logout

urlpatterns = [
    path("register/", register, name="register"),
    path("login/", login, name="login"),
    path("refresh/", refresh, name="token_refresh"),
    path("logout/", logout, name="logout"),
]
