from django.urls import path
from .views import (
    list_brands, insert_brand, delete_brand, fetch_brand, update_brand,
    list_models, insert_model, delete_model, fetch_model, update_model,
    list_categories, insert_category, delete_category, fetch_category, update_category,
    list_products, insert_product, delete_product, fetch_product, update_product
)

urlpatterns=[
    path("brands/", list_brands, name="list_brands"),
    path("brands/insert/", insert_brand, name="insert_brand"),
    path("brands/delete/<str:brand_code>/", delete_brand, name="delete_brand"),
    path("brands/update/<str:brand_code>/", update_brand, name="update_brand"),
    path("brands/<str:brand_code>/", fetch_brand, name="fetch_brand"),

    path("brands/<str:brand_code>/models/", list_models, name="list_models"),
    path("brands/<str:brand_code>/models/insert/", insert_model, name="insert_model"),
    path("brands/<str:brand_code>/models/delete/<str:model_code>/", delete_model, name="delete_model"),
    path("brands/<str:brand_code>/models/update/<str:model_code>/", update_model, name="update_model"),
    path("brands/<str:brand_code>/models/<str:model_code>/", fetch_model, name="fetch_model"),

    path("brands/<str:brand_code>/models/<str:model_code>/categories/", list_categories, name="list_categories"),
    path("brands/<str:brand_code>/models/<str:model_code>/categories/insert/", insert_category, name="insert_category"),
    path("brands/<str:brand_code>/models/<str:model_code>/categories/delete/<str:category_code>/", delete_category, name="delete_category"),
    path("brands/<str:brand_code>/models/<str:model_code>/categories/update/<str:category_code>/", update_category, name="update_category"),
    path("brands/<str:brand_code>/models/<str:model_code>/categories/<str:category_code>/", fetch_category, name="fetch_category"),

    path("brands/<str:brand_code>/models/<str:model_code>/categories/<str:category_code>/products/",
         list_products, name="list_products"),
    path("brands/<str:brand_code>/models/<str:model_code>/categories/<str:category_code>/products/insert/",
         insert_product, name="insert_product"),
    path("brands/<str:brand_code>/models/<str:model_code>/categories/<str:category_code>/products/delete/<str:product_code>/",
         delete_product, name="delete_product"),
    path("brands/<str:brand_code>/models/<str:model_code>/categories/<str:category_code>/products/update/<str:product_code>/",
         update_product, name="update_product"),
    path("brands/<str:brand_code>/models/<str:model_code>/categories/<str:category_code>/products/<str:product_code>/",
         fetch_product, name="fetch_product"),
]
