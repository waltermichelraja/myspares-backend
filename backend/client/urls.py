from django.urls import path
from .views import list_cart, add_to_cart, remove_from_cart

urlpatterns = [
    path("<str:user_id>/cart/", list_cart, name="list_cart"),
    path("<str:user_id>/cart/add/<str:product_id>/", add_to_cart, name="add_to_cart"),
    path("<str:user_id>/cart/remove/<str:product_id>/", remove_from_cart, name="remove_from_cart"),
]