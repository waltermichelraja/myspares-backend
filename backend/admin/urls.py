from django.urls import path
from .views import (
    list_brands, insert_brand, delete_brand, fetch_brand,
    list_models, insert_model, delete_model, fetch_model
    )

urlpatterns = [
    path("brands/", list_brands, name="list_brands"),
    path("brands/insert/", insert_brand, name="insert_brand"),
    path("brands/delete/<str:brand_code>/", delete_brand, name="delete_brand"),
    path("brands/<str:brand_code>/", fetch_brand, name="fetch_brand"),

    path("brands/<str:brand_code>/models/", list_models, name="list_models"),
    path("brands/<str:brand_code>/models/insert/", insert_model, name="insert_model"),
    path("brands/<str:brand_code>/models/delete/<str:model_code>/", delete_model, name="delete_model"),
    path("brands/<str:brand_code>/models/<str:model_code>/", fetch_model, name="fetch_model"),
]