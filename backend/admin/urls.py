from django.urls import path
from .views import (
    list_brands, insert_brand, delete_brand, fetch_brand,
    list_models, insert_model, delete_model, fetch_model,
    list_categories, insert_category, delete_category, fetch_category
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

    path("brands/<str:brand_code>/models/<str:model_code>/categories/", list_categories, name="list_categories"),
    path("brands/<str:brand_code>/models/<str:model_code>/categories/insert/", insert_category, name="insert_category"),
    path("brands/<str:brand_code>/models/<str:model_code>/categories/delete/<str:category_code>/", delete_category, name="delete_category"),
    path("brands/<str:brand_code>/models/<str:model_code>/categories/<str:category_code>/", fetch_category, name="fetch_category"),
]