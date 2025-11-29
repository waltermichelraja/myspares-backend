from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import *
from .apps import AuthenticationConfig
from utility.exceptions import handle_exceptions


@handle_exceptions
@api_view(["POST"])
def register(request):
    data=request.data
    for field in ["username", "phone_number", "password"]:
        if field not in data:
            raise ValueError(f"{field} is required")
    user=Auth.create(data["username"], data["phone_number"], data["password"])
    return Response({"message": "user registered successfully", "user": user.to_dict()}, status=status.HTTP_201_CREATED)


@handle_exceptions
@api_view(["POST"])
def send_otp_view(request):
    data=request.data
    for field in ["username", "phone_number", "password"]:
        if field not in data:
            raise ValueError(f"{field} is required")
    Auth.create_temp_user(data["username"], data["phone_number"], data["password"])
    Auth.send_otp_to_user(data["phone_number"])
    return Response({"message": "OTP sent successfully"})


@handle_exceptions
@api_view(["POST"])
def verify_otp_view(request):
    data=request.data
    phone_number=data.get("phone_number")
    code=data.get("otp")
    if not phone_number or not code:
        raise ValueError("phone_number and otp are required")
    if not Auth.verify_user_otp(phone_number, code):
        raise ValueError("invalid or expired OTP")
    user_data=Auth.promote_temp_user_to_main(phone_number)
    return JsonResponse({
        "message": "user verified and registered successfully", "user": user_data.to_dict(include_password=False)
        }, status=status.HTTP_201_CREATED)


@handle_exceptions
@api_view(["POST"])
def login(request):
    data=request.data
    phone_number=data.get("phone_number")
    password=data.get("password")
    if not phone_number:
        raise ValueError("phone_number is required")
    if not password:
        raise ValueError("password is required")
    user_data=users_collection.find_one({"phone_number": normalize_number(phone_number)})
    if not user_data:
        raise ValueError("invalid credentials")
    user=Auth.from_dict(user_data)
    if not user.check_password(password):
        raise ValueError("invalid credentials")
    tokens=TokenManager.generate_tokens(user, request=request)
    response=JsonResponse({
        "access": tokens["access"],
        "user": user.to_dict(include_password=False)
    })
    response.set_cookie("refresh_token", tokens["refresh"], **AuthenticationConfig.COOKIE_SETTINGS)
    return response


@handle_exceptions
@api_view(["POST"])
def forgot_password_send(request):
    phone=request.data.get("phone_number")
    if not phone:
        raise ValueError("phone_number is required")
    Auth.initiate_password_reset(phone)
    return Response({"message": "if an account with the number exists, an OTP was sent."})


@handle_exceptions
@api_view(["POST"])
def forgot_password_verify(request):
    phone=request.data.get("phone_number")
    otp=request.data.get("otp")
    if not phone or not otp:
        raise ValueError("phone_number and otp are required")
    reset_token=Auth.verify_password_reset_otp(phone, otp)
    return Response({"reset_token": reset_token})


@handle_exceptions
@api_view(["POST"])
def forgot_password_reset(request):
    token=request.data.get("reset_token")
    new_password=request.data.get("new_password")
    if not token or not new_password:
        raise ValueError("reset_token and new_password are required")
    Auth.reset_password_with_token(token, new_password)
    return Response({"message": "password has been reset successfully"})


@handle_exceptions
@api_view(["POST"])
def refresh(request):
    refresh_token=request.COOKIES.get("refresh_token")
    if not refresh_token:
        raise ValueError("refresh token required")
    if TokenManager.is_blacklisted_refresh(refresh_token):
        raise ValueError("refresh token has been revoked")
    tokens=TokenManager.refresh_tokens(refresh_token)
    response=JsonResponse({"access": tokens["access"]})
    response.set_cookie("refresh_token", tokens["refresh"], **AuthenticationConfig.COOKIE_SETTINGS)
    return response


@handle_exceptions
@api_view(["POST"])
def logout(request):
    refresh_token=request.COOKIES.get("refresh_token")
    access_header=request.headers.get("Authorization", "")
    access_token=access_header.replace("Bearer ", "") if access_header.startswith("Bearer ") else None
    if not refresh_token or not access_token:
        raise ValueError("refresh and access tokens required")
    payload=TokenManager.verify_access_token(access_token)
    user_id=payload.get("user_id")
    TokenManager.blacklist_token(refresh_token, access_token, user_id=user_id)
    response=JsonResponse({"message": "logged out successfully"})
    response.delete_cookie("refresh_token", path=AuthenticationConfig.COOKIE_SETTINGS["path"])
    return response