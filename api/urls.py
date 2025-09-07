from django.urls import path
from . import views

urlpatterns = [
    # === Brand Endpoints ===
    path('brands/create/', views.create_brand, name='create_brand'),
    path('brands/<str:brand_code>/', views.list_brands_by_code, name='list_brands_by_code'),
    path('brands/delete/<str:brand_code>/', views.delete_brand, name='delete_brand'),

    # === Model Endpoints ===
    path('models/create/<str:brand_code>/', views.create_model, name='create_model'),
    path('models/<str:brand_code>/', views.list_models_by_brand, name='list_models_by_brand'),
    path('models/delete/<str:model_code>/', views.delete_model, name='delete_model'),

    # === Category Endpoints ===
    path('categories/create/<str:model_code>/', views.create_category, name='create_category'),
    path('categories/<str:model_code>/', views.list_categories, name='list_categories'),
    path('categories/delete/<str:category_code>/', views.delete_category, name='delete_category'),

    # === Product Endpoints ===
    path('products/create/<str:category_code>/', views.create_product, name='create_product'),
    path('products/<str:category_code>/<str:model_code>/', views.list_products, name='list_products_by_category_model'),
    path('products/delete/<str:product_id>/', views.delete_product, name='delete_product'),
    path('products/count/<str:product_code>/', views.product_stock, name='product_stock'),
    path('products/update-stock/<str:product_code>/<str:action>/', views.update_stock, name='update_stock'),
]
