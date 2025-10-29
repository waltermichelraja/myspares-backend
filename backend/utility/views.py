from admin.views import *
from admin.models import Brand, Model, Category, Product
from .exceptions import handle_exceptions


@api_view(["GET"])
@handle_exceptions
def list_brands(request):
    brands=Brand.brands_list()
    return Response({"brands": brands}, status=status.HTTP_200_OK)

@api_view(["GET"])
@handle_exceptions
def fetch_brand(request, brand_code):
    brand = Brand.brand_fetch(brand_code)
    return Response({"brand": brand}, status=status.HTTP_200_OK)

@api_view(["GET"])
@handle_exceptions
def search_brand(request):
    query=request.query_params.get("q", "").strip("/")
    if not query:
        return Response(
            {"error": "missing required query parameter: q"},
            status=status.HTTP_400_BAD_REQUEST
        )
    results=Brand.brand_search(query)
    return Response({"results": results}, status=status.HTTP_200_OK)


@api_view(["GET"])
@handle_exceptions
def list_models(request, brand_code):
    models=Model.models_list(brand_code)
    return Response({"models": models}, status=status.HTTP_200_OK)

@api_view(["GET"])
@handle_exceptions
def fetch_model(request, brand_code, model_code):
    model=Model.model_fetch(brand_code, model_code)
    return Response({"model": model}, status=status.HTTP_200_OK)

@api_view(["GET"])
@handle_exceptions
def search_model(request, brand_code):
    query=request.query_params.get("q", "").strip("/")
    if not query:
        return Response(
            {"error": "missing required query parameter: q"},
            status=status.HTTP_400_BAD_REQUEST
        )
    results=Model.model_search(brand_code, query)
    return Response({"results": results}, status=status.HTTP_200_OK)


@api_view(["GET"])
@handle_exceptions
def list_categories(request, brand_code, model_code):
    categories=Category.categories_list(brand_code, model_code)
    return Response({"categories": categories}, status=status.HTTP_200_OK)

@api_view(["GET"])
@handle_exceptions
def fetch_category(request, brand_code, model_code, category_code):
    category=Category.category_fetch(brand_code, model_code, category_code)
    return Response({"category": category}, status=status.HTTP_200_OK)

@api_view(["GET"])
@handle_exceptions
def search_category(request, brand_code, model_code):
    query=request.query_params.get("q", "").strip("/")
    if not query:
        return Response(
            {"error": "missing required query parameter: q"},
            status=status.HTTP_400_BAD_REQUEST
        )
    results=Category.category_search(brand_code, model_code, query)
    return Response({"results": results}, status=status.HTTP_200_OK)


@api_view(["GET"])
@handle_exceptions
def list_products(request, brand_code, model_code, category_code):
    products=Product.products_list(brand_code, model_code, category_code)
    return Response({"products": products}, status=status.HTTP_200_OK)

@api_view(["GET"])
@handle_exceptions
def fetch_product(request, brand_code, model_code, category_code, product_code):
    product=Product.product_fetch(brand_code, model_code, category_code, product_code)
    return Response({"product": product}, status=status.HTTP_200_OK)

@api_view(["GET"])
@handle_exceptions
def search_product(request, brand_code, model_code, category_code):
    query=request.query_params.get("q", "").strip("/")
    if not query:
        return Response(
            {"error": "missing required query parameter: q"},
            status=status.HTTP_400_BAD_REQUEST
        )
    results=Product.product_search(brand_code, model_code, category_code, query)
    return Response({"results": results}, status=status.HTTP_200_OK)