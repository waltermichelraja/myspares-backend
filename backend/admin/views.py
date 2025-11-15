from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from .models import Brand, Model, Category, Product, Admin
from utility.exceptions import handle_exceptions
import tempfile


def save_image(image_file):
    if not image_file:
        return None
    tmp_path=tempfile.NamedTemporaryFile(delete=False,suffix=".jpg").name
    with open(tmp_path,"wb") as f:
        for chunk in image_file.chunks():
            f.write(chunk)
    return tmp_path


@api_view(["POST"])
@parser_classes([MultiPartParser,FormParser])
@handle_exceptions
def insert_brand(request):
    data=request.data
    for field in ["brand_name", "brand_code"]:
        if field not in data:
            raise ValueError(f"{field} is required")
    image_file=request.FILES.get("image")
    if not image_file:
        raise ValueError("image is required")
    tmp_path=save_image(image_file)
    brand=Brand.brand_insert(data["brand_name"], data["brand_code"], tmp_path)
    return Response({
        "message": "brand inserted successfully",
        "brand": brand.to_dict()
    },status=status.HTTP_201_CREATED)

@api_view(["DELETE"])
@handle_exceptions
def delete_brand(request, brand_code):
    Brand.brand_delete(brand_code)
    return Response({"message": "brand deleted successfully"}, status=status.HTTP_200_OK)

@api_view(["PUT"])
@parser_classes([MultiPartParser,FormParser])
@handle_exceptions
def update_brand(request, brand_code):
    updates=request.data
    if not updates and "image" not in request.FILES:
        raise ValueError("no fields provided for update")
    image_file=request.FILES.get("image")
    tmp_path=save_image(image_file) if image_file else None
    updated_brand=Brand.brand_update(brand_code, updates, image_file_path=tmp_path)
    return Response({
        "message": "brand updated successfully",
        "brand": updated_brand.to_dict()
    },status=status.HTTP_200_OK)


@api_view(["POST"])
@parser_classes([MultiPartParser,FormParser])
@handle_exceptions
def insert_model(request, brand_code):
    data=request.data
    for field in ["model_name", "model_code"]:
        if field not in data:
            raise ValueError(f"{field} is required")
    image_file=request.FILES.get("image")
    if not image_file:
        raise ValueError("image is required")
    tmp_path=save_image(image_file)
    model=Model.model_insert(brand_code, data["model_name"], data["model_code"], tmp_path)
    return Response({
        "message": "model inserted successfully",
        "model": model.to_dict()
    },status=status.HTTP_201_CREATED)

@api_view(["DELETE"])
@handle_exceptions
def delete_model(request, brand_code, model_code):
    Model.model_delete(brand_code, model_code)
    return Response({"message": "model deleted successfully"}, status=status.HTTP_200_OK)

@api_view(["PUT"])
@parser_classes([MultiPartParser,FormParser])
@handle_exceptions
def update_model(request, brand_code, model_code):
    updates=request.data
    if not updates and "image" not in request.FILES:
        raise ValueError("no fields provided for update")
    image_file=request.FILES.get("image")
    tmp_path=save_image(image_file) if image_file else None
    updated_model=Model.model_update(brand_code, model_code, updates, image_file_path=tmp_path)
    return Response({
        "message": "model updated successfully",
        "model": updated_model.to_dict()
    },status=status.HTTP_200_OK)


@api_view(["POST"])
@parser_classes([MultiPartParser,FormParser])
@handle_exceptions
def insert_category(request, brand_code, model_code):
    data=request.data
    for field in ["category_name", "category_code"]:
        if field not in data:
            raise ValueError(f"{field} is required")
    image_file=request.FILES.get("image")
    if not image_file:
        raise ValueError("image is required")
    tmp_path=save_image(image_file)
    category=Category.category_insert(
        brand_code,model_code, data["category_name"], data["category_code"], tmp_path)
    return Response({
        "message": "category inserted successfully",
        "category": category.to_dict()
    },status=status.HTTP_201_CREATED)

@api_view(["DELETE"])
@handle_exceptions
def delete_category(request, brand_code, model_code, category_code):
    Category.category_delete(brand_code, model_code, category_code)
    return Response({"message": "category deleted successfully"}, status=status.HTTP_200_OK)

@api_view(["PUT"])
@parser_classes([MultiPartParser,FormParser])
@handle_exceptions
def update_category(request, brand_code, model_code, category_code):
    updates=request.data
    if not updates and "image" not in request.FILES:
        raise ValueError("no fields provided for update")
    image_file=request.FILES.get("image")
    tmp_path=save_image(image_file) if image_file else None
    updated_category=Category.category_update(
        brand_code, model_code, category_code, updates, image_file_path=tmp_path)
    return Response({
        "message": "category updated successfully",
        "category": updated_category.to_dict()
    },status=status.HTTP_200_OK)


@api_view(["POST"])
@parser_classes([MultiPartParser,FormParser])
@handle_exceptions
def insert_product(request, brand_code, model_code, category_code):
    data=request.data
    for field in ["product_name", "product_code", "description", "price", "stock"]:
        if field not in data:
            raise ValueError(f"{field} is required")
    image_file=request.FILES.get("image")
    if not image_file:
        raise ValueError("image is required")
    tmp_path=save_image(image_file)
    product=Product.product_insert(
        brand_code, model_code, category_code, 
        data["product_name"], data["product_code"], 
        data["description"], data["price"], data["stock"], tmp_path)
    return Response({
        "message": "product inserted successfully",
        "product": product.to_dict()
    },status=status.HTTP_201_CREATED)

@api_view(["DELETE"])
@handle_exceptions
def delete_product(request, brand_code, model_code, category_code, product_code):
    Product.product_delete(brand_code, model_code, category_code, product_code)
    return Response({"message": "product deleted successfully"}, status=status.HTTP_200_OK)

@api_view(["PUT"])
@parser_classes([MultiPartParser,FormParser])
@handle_exceptions
def update_product(request, brand_code, model_code, category_code, product_code):
    import json
    updates=request.data.copy()
    if "offers" in updates:
        try:
            updates["offers"]=json.loads(updates["offers"])
        except json.JSONDecodeError:
            raise ValueError("offers must be valid JSON")
    if not updates and "image" not in request.FILES:
        raise ValueError("no fields provided for update")
    image_file=request.FILES.get("image")
    tmp_path=save_image(image_file) if image_file else None
    updated_product=Product.product_update(
        brand_code, model_code, category_code, product_code, updates, image_file_path=tmp_path)
    return Response({
        "message": "product updated successfully",
        "product": updated_product.to_dict()
    },status=status.HTTP_200_OK)


@api_view(["GET"])
@handle_exceptions
def list_audits(request):
    try:
        limit=int(request.query_params.get("limit", 50))
    except ValueError:
        return Response({"error": "limit must be an integer"}, status=status.HTTP_400_BAD_REQUEST)
    logs=Admin.audits_list(limit=limit)
    return Response(logs, status=status.HTTP_200_OK)

@api_view(["GET"])
@handle_exceptions
def search_audits(request):
    query=request.query_params.get("q", "").strip("/")
    sort_field=request.query_params.get("sort", "-timestamp")
    limit=int(request.query_params.get("limit", 50))
    if not query:
        return Response(
            {"error": "missing required query parameter: q"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    logs=Admin.audit_search(query, sort_field=sort_field, limit=limit)
    return Response(logs, status=status.HTTP_200_OK)
