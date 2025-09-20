from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from .models import Cart, Address
from authentication.models import TokenManager


def get_token_from_header(request):
    auth_header=request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    return auth_header.split(" ", 1)[1]

def require_auth(request, user_id):
    token=get_token_from_header(request)
    if not token:
        return Response({"error": "authorization header missing"}, status=status.HTTP_401_UNAUTHORIZED)
    try:
        payload=TokenManager.verify_access_token(token)
        if str(payload["user_id"])!=str(user_id):
            return Response({"error": "forbidden: user mismatch"}, status=status.HTTP_403_FORBIDDEN)
        return payload
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def list_cart(request, user_id):
    auth=require_auth(request, user_id)
    if isinstance(auth, Response):
        return auth
    cart=Cart.get_cart(user_id)
    return Response({"cart": cart.to_dict()}, status=status.HTTP_200_OK)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def add_to_cart(request, user_id, product_id):
    auth=require_auth(request, user_id)
    if isinstance(auth, Response):
        return auth
    quantity=int(request.data.get("quantity", 1))
    try:
        cart=Cart.add_item(str(user_id), str(product_id), quantity)
        return Response({"cart": cart.to_dict()}, status=status.HTTP_200_OK)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["DELETE"])
@authentication_classes([])
@permission_classes([AllowAny])
def remove_from_cart(request, user_id, product_id):
    auth=require_auth(request, user_id)
    if isinstance(auth, Response):
        return auth
    try:
        cart=Cart.remove_item(str(user_id), str(product_id))
        return Response({"cart": cart.to_dict()}, status=status.HTTP_200_OK)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def get_address(request, user_id):
    auth=require_auth(request, user_id)
    if isinstance(auth, Response):
        return auth
    try:
        address=Address.get_address(user_id)
        return Response({"address": address.to_dict()}, status=status.HTTP_200_OK)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)


@api_view(["PUT"])
@authentication_classes([])
@permission_classes([AllowAny])
def update_address(request, user_id):
    auth=require_auth(request, user_id)
    if isinstance(auth, Response):
        return auth
    try:
        address=Address.update_address(user_id, **request.data)
        return Response({"address": address.to_dict()}, status=status.HTTP_200_OK)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)