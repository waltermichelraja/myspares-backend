from django.urls import path
from .views import (
    insert_brand, delete_brand, update_brand,
    insert_model, delete_model, update_model,
    insert_category, delete_category, update_category,
    insert_product, delete_product, update_product,
)

urlpatterns=[
     path("brands/insert/", insert_brand, name="insert_brand"),
     path("brands/delete/<str:brand_code>/", delete_brand, name="delete_brand"),
     path("brands/update/<str:brand_code>/", update_brand, name="update_brand"),

     path("brands/<str:brand_code>/models/insert/", insert_model, name="insert_model"),
     path("brands/<str:brand_code>/models/delete/<str:model_code>/", delete_model, name="delete_model"),
     path("brands/<str:brand_code>/models/update/<str:model_code>/", update_model, name="update_model"),

     path("brands/<str:brand_code>/models/<str:model_code>/categories/insert/", insert_category, name="insert_category"),
     path("brands/<str:brand_code>/models/<str:model_code>/categories/delete/<str:category_code>/", delete_category, name="delete_category"),
     path("brands/<str:brand_code>/models/<str:model_code>/categories/update/<str:category_code>/", update_category, name="update_category"),

     path("brands/<str:brand_code>/models/<str:model_code>/categories/<str:category_code>/products/insert/",
          insert_product, name="insert_product"),
     path("brands/<str:brand_code>/models/<str:model_code>/categories/<str:category_code>/products/delete/<str:product_code>/",
          delete_product, name="delete_product"),
     path("brands/<str:brand_code>/models/<str:model_code>/categories/<str:category_code>/products/update/<str:product_code>/",
          update_product, name="update_product"),
]
