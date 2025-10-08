from django.urls import path
from . import views

urlpatterns = [
    # 🔹 Registration Flow
    path("register/", views.register_send_otp, name="register_send_otp"),
    path("register/verify-otp/", views.register_verify_otp, name="register_verify_otp"),

    # 🔹 Login Flow
    path("login/", views.login_send_otp, name="login_send_otp"),
    path("login/verify-otp/", views.login_verify_otp, name="login_verify_otp"),

    # 🔹 Profile
    path("user/<str:phone>/", views.get_user_profile, name="get_user_profile"),
]
