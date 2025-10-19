from django.urls import path
from .views import (register, send_otp_view, verify_otp_view, login, refresh, logout,
                     forgot_password_send, forgot_password_verify, forgot_password_reset)

urlpatterns = [
    path("register/", register, name="register"),
    path("register/send-otp/", send_otp_view, name="send_otp"),
    path("register/verify-otp/", verify_otp_view, name="verify_otp"),
    path("login/", login, name="login"),
    path("forgot-password/send/", forgot_password_send, name="forgot_password_send"),
    path("forgot-password/verify/", forgot_password_verify, name="forgot_password_verify"),
    path("forgot-password/reset/", forgot_password_reset, name="forgot_password_reset"),
    path("refresh/", refresh, name="token_refresh"),
    path("logout/", logout, name="logout"),
]
