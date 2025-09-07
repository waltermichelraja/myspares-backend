from django.urls import path
from .views import list_brands, fetch_brand, insert_brand, delete_brand

urlpatterns = [
    path("brands/", list_brands, name="list_brands"),
    path("brands/insert/", insert_brand, name="insert_brand"),
    path("brands/delete/<str:brand_code>/", delete_brand, name="delete_brand"),
    path("brands/<str:brand_code>/", fetch_brand, name="fetch_brand"),
]
