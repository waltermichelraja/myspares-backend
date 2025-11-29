from django.urls import path
from .views import (
    list_brands, fetch_brand, search_brand,
    list_models, fetch_model, search_model,
    list_categories, fetch_category, search_category,
    list_products, fetch_product, search_product,
)

urlpatterns=[
    path("brands/", list_brands, name="list_brands"),
    path("brands/search/", search_brand, name="search_brands"),
    path("brands/<str:brand_code>/", fetch_brand, name="fetch_brand"),

    path("brands/<str:brand_code>/models/", list_models, name="list_models"),
    path("brands/<str:brand_code>/models/search/", search_model, name="search_models"),
    path("brands/<str:brand_code>/models/<str:model_code>/", fetch_model, name="fetch_model"),

    path("brands/<str:brand_code>/models/<str:model_code>/categories/", list_categories, name="list_categories"),
        path("brands/<str:brand_code>/models/<str:model_code>/categories/search/", search_category, name="search_categories"),
    path("brands/<str:brand_code>/models/<str:model_code>/categories/<str:category_code>/", fetch_category, name="fetch_category"),

    path("brands/<str:brand_code>/models/<str:model_code>/categories/<str:category_code>/products/", list_products, name="list_products"),
    path("brands/<str:brand_code>/models/<str:model_code>/categories/<str:category_code>/products/search/", search_product, name="search_products"),
    path("brands/<str:brand_code>/models/<str:model_code>/categories/<str:category_code>/products/<str:product_code>/", fetch_product, name="fetch_product"),
]
