from django.urls import path
from . import views

urlpatterns = [
    # === Brand Endpoints ===
    path('brands/create/', views.create_brand, name='create_brand'),
    path('brands/', views.list_brands, name='list_brands'),
    path('brands/delete/<str:brand_id>/', views.delete_brand, name='delete_brand'),

    # === Model Endpoints ===
    path('models/create/', views.create_model, name='create_model'),
    path('models/', views.list_models, name='list_models'),
    path('models/delete/<str:model_id>/', views.delete_model, name='delete_model'),

    # === Category Endpoints ===
    path('categories/create/', views.create_category, name='create_category'),
    path('categories/', views.list_categories, name='list_categories'),
    path('categories/delete/<str:category_id>/', views.delete_category, name='delete_category'),

    # === Product Endpoints ===
    path('products/create/', views.create_product, name='create_product'),
    path('products/', views.list_products, name='list_products'),
    path('products/delete/<str:product_id>/', views.delete_product, name='delete_product'),
    path('products/count/', views.product_count, name='product_count'),
    path('products/update-stock/<str:product_id>/<str:action>/', views.update_stock, name='update_stock'),
]
