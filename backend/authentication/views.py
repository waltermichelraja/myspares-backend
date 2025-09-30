from django.http import JsonResponse
from pymongo.errors import PyMongoError
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Auth, TokenManager, users_collection
from .apps import AuthenticationConfig


@api_view(["POST"])
def register(request):
    data=request.data
    for field in ["username", "phone_number", "password"]:
        if field not in data:
            return Response({"error": f"{field} is required"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        user=Auth.create(data["username"], data["phone_number"], data["password"])
        return Response({"message": "user registered successfully", "user": user.to_dict()}, status=status.HTTP_201_CREATED)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except RuntimeError as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
def login(request):
    data=request.data
    phone_number=data.get("phone_number")
    password=data.get("password")

    if not phone_number:
        return Response({"error": "phone_number is required"}, status=status.HTTP_400_BAD_REQUEST)
    if not password:
        return Response({"error": "password is required"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        user_data=users_collection.find_one({"phone_number": str(phone_number)})
    except PyMongoError as e:
        print(f"[DB ERROR] failed to query user: {e}")
        return Response({"error": "database error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    if not user_data:
        return Response({"error": "invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
    user=Auth.from_dict(user_data)
    if not user.check_password(password):
        return Response({"error": "invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

    tokens=TokenManager.generate_tokens(user)
    response=JsonResponse({
        "access": tokens["access"],
        "user": user.to_dict(include_password=False)
    })
    response.set_cookie("refresh_token", tokens["refresh"], **AuthenticationConfig.COOKIE_SETTINGS)
    return response


@api_view(["POST"])
def refresh(request):
    refresh_token=request.COOKIES.get("refresh_token")
    if not refresh_token:
        return Response({"error": "refresh token required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        if TokenManager.is_blacklisted(refresh_token):
            return Response({"error": "refresh token has been revoked"}, status=status.HTTP_401_UNAUTHORIZED)
        tokens=TokenManager.refresh_tokens(refresh_token)
        response=JsonResponse({"access": tokens["access"]})
        response.set_cookie("refresh_token", tokens["refresh"], **AuthenticationConfig.COOKIE_SETTINGS)
        return response
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)
    except RuntimeError as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
def logout(request):
    refresh_token=request.COOKIES.get("refresh_token")
    access_header=request.headers.get("Authorization", "")
    access_token=access_header.replace("Bearer ", "") if access_header.startswith("Bearer ") else None
    if not refresh_token or not access_token:
        return Response({"error": "refresh and access tokens required"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        payload=TokenManager.verify_access_token(access_token)
        user_id=payload.get("user_id")
        TokenManager.blacklist_token(refresh_token, access_token, user_id=user_id)
        response=JsonResponse({"message": "logged out successfully"})
        response.delete_cookie("refresh_token", path=AuthenticationConfig.COOKIE_SETTINGS["path"])
        return response
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except RuntimeError as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
