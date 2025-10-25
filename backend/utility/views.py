from admin.views import *
from admin.models import Brand, Model, Category, Product
from .exceptions import handle_exceptions


@handle_exceptions
@api_view(["GET"])
def list_brands(request):
    brands=Brand.brands_list()
    return Response({"brands": brands}, status=status.HTTP_200_OK)

@handle_exceptions
@api_view(["GET"])
def fetch_brand(request, brand_code):
    brand = Brand.brand_fetch(brand_code)
    return Response({"brand": brand}, status=status.HTTP_200_OK)

@handle_exceptions
@api_view(["GET"])
def search_brand(request, query):
    results=Brand.brand_search(query)
    return Response({"results": results}, status=status.HTTP_200_OK)


@handle_exceptions
@api_view(["GET"])
def list_models(request, brand_code):
    models=Model.models_list(brand_code)
    return Response({"models": models}, status=status.HTTP_200_OK)

@handle_exceptions
@api_view(["GET"])
def fetch_model(request, brand_code, model_code):
    model=Model.model_fetch(brand_code, model_code)
    return Response({"model": model}, status=status.HTTP_200_OK)

@handle_exceptions
@api_view(["GET"])
def search_model(request, brand_code, query):
    results=Model.model_search(brand_code, query)
    return Response({"results": results}, status=status.HTTP_200_OK)


@handle_exceptions
@api_view(["GET"])
def list_categories(request, brand_code, model_code):
    categories=Category.categories_list(brand_code, model_code)
    return Response({"categories": categories}, status=status.HTTP_200_OK)

@handle_exceptions
@api_view(["GET"])
def fetch_category(request, brand_code, model_code, category_code):
    category=Category.category_fetch(brand_code, model_code, category_code)
    return Response({"category": category}, status=status.HTTP_200_OK)

@handle_exceptions
@api_view(["GET"])
def search_category(request, brand_code, model_code, query):
    results=Category.category_search(brand_code, model_code, query)
    return Response({"results": results}, status=status.HTTP_200_OK)


@handle_exceptions
@api_view(["GET"])
def list_products(request, brand_code, model_code, category_code):
    products=Product.products_list(brand_code, model_code, category_code)
    return Response({"products": products}, status=status.HTTP_200_OK)

@handle_exceptions
@api_view(["GET"])
def fetch_product(request, brand_code, model_code, category_code, product_code):
    product=Product.product_fetch(brand_code, model_code, category_code, product_code)
    return Response({"product": product}, status=status.HTTP_200_OK)

@handle_exceptions
@api_view(["GET"])
def search_product(request, brand_code, model_code, category_code, query):
    results=Product.product_search(brand_code, model_code, category_code, query)
    return Response({"results": results}, status=status.HTTP_200_OK)