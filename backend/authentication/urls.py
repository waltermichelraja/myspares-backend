from django.urls import path
from .views import register, send_otp_view, verify_otp_view, login, refresh, logout

urlpatterns = [
    path("register/", register, name="register"),
    path("register/send-otp/", send_otp_view, name="send_otp"),
    path("register/verify-otp/", verify_otp_view, name="verify_otp"),
    path("login/", login, name="login"),
    path("refresh/", refresh, name="token_refresh"),
    path("logout/", logout, name="logout"),
]
