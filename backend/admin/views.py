from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Brand, Model, Category


@api_view(["GET"])
def list_brands(request):
    try:
        brands = Brand.brands_list()
        return Response({"brands": brands}, status=status.HTTP_200_OK)
    except RuntimeError as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(["POST"])
def insert_brand(request):
    data = request.data
    for field in ["brand_name", "brand_code", "image_url"]:
        if field not in data:
            return Response({"error": f"{field} is required"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        brand = Brand.brand_insert(data["brand_name"], data["brand_code"], data["image_url"])
        return Response({"message": "brand inserted successfully", "brand": brand.to_dict()}, status=status.HTTP_201_CREATED)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except RuntimeError as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(["DELETE"])
def delete_brand(request, brand_code):
    try:
        Brand.brand_delete(brand_code)
        return Response({"message": "brand deleted successfully"}, status=status.HTTP_200_OK)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
    except RuntimeError as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(["GET"])
def fetch_brand(request, brand_code):
    try:
        brand = Brand.brand_fetch(brand_code)
        return Response({"brand": brand}, status=status.HTTP_200_OK)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
    except RuntimeError as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
def list_models(request, brand_code):
    try:
        models = Model.models_list(brand_code)
        return Response({"models": models}, status=status.HTTP_200_OK)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
    except RuntimeError as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(["POST"])
def insert_model(request, brand_code):
    data = request.data
    for field in ["model_name", "model_code", "image_url"]:
        if field not in data:
            return Response({"error": f"{field} is required"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        model = Model.model_insert(brand_code, data["model_name"], data["model_code"], data["image_url"])
        return Response({"message": "model inserted successfully", "model": model.to_dict()}, status=status.HTTP_201_CREATED)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except RuntimeError as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(["DELETE"])
def delete_model(request, brand_code, model_code):
    try:
        Model.model_delete(brand_code, model_code)
        return Response({"message": "model deleted successfully"}, status=status.HTTP_200_OK)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
    except RuntimeError as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(["GET"])
def fetch_model(request, brand_code, model_code):
    try:
        model = Model.model_fetch(brand_code, model_code)
        return Response({"model": model}, status=status.HTTP_200_OK)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
    except RuntimeError as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
def list_categories(request, brand_code, model_code):
    try:
        categories = Category.categories_list(brand_code, model_code)
        return Response({"categories": categories}, status=status.HTTP_200_OK)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
    except RuntimeError as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(["POST"])
def insert_category(request, brand_code, model_code):
    data = request.data
    for field in ["category_name", "category_code", "image_url"]:
        if field not in data:
            return Response({"error": f"{field} is required"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        category = Category.category_insert(
            brand_code, model_code,
            data["category_name"], data["category_code"], data["image_url"]
        )
        return Response({"message": "category inserted successfully", "category": category.to_dict()}, status=status.HTTP_201_CREATED)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except RuntimeError as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(["DELETE"])
def delete_category(request, brand_code, model_code, category_code):
    try:
        Category.category_delete(brand_code, model_code, category_code)
        return Response({"message": "category deleted successfully"}, status=status.HTTP_200_OK)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
    except RuntimeError as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(["GET"])
def fetch_category(request, brand_code, model_code, category_code):
    try:
        category = Category.category_fetch(brand_code, model_code, category_code)
        return Response({"category": category}, status=status.HTTP_200_OK)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
    except RuntimeError as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)