from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from pymongo import MongoClient
from bson import ObjectId
import os, json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# === MongoDB Connection ===
client = MongoClient(os.getenv("MONGO_URI"))
db = client["MySpares_db"]

brands_col = db["brands"]
models_col = db["models"]       # New collection for Bikes/Models
categories_col = db["categories"]
products_col = db["products"]

# Helper to convert ObjectId to string
def obj_id(o):
    if isinstance(o, ObjectId):
        return str(o)
    return o

# ========== BRAND ==========
@csrf_exempt
def create_brand(request):
    if request.method == "POST":
        data = json.loads(request.body)
        brand_id = brands_col.insert_one({
            "brand_name": data["brand_name"],
            "logo_pic": data.get("logo_pic", ""),
            "created_date": datetime.utcnow()
        }).inserted_id
        return JsonResponse({"message": "Brand created", "brand_id": str(brand_id)})

def list_brands(request):
    brands = list(brands_col.find({}, {"_id": 1, "brand_name": 1, "logo_pic": 1}))
    for b in brands: b["_id"] = str(b["_id"])
    return JsonResponse(brands, safe=False)

@csrf_exempt
def delete_brand(request, brand_id):
    result = brands_col.delete_one({"_id": ObjectId(brand_id)})
    return JsonResponse({"deleted_count": result.deleted_count})

# ========== MODEL (BIKE) ==========
@csrf_exempt
def create_model(request):
    if request.method == "POST":
        data = json.loads(request.body)
        model_id = models_col.insert_one({
            "brand_id": ObjectId(data["brand_id"]),
            "model_name": data["model_name"],
            "image_url": data.get("image_url", ""),  # optional
            "created_at": datetime.utcnow()
        }).inserted_id
        return JsonResponse({"message": "Model created", "model_id": str(model_id)})
    
def list_models(request):
    models = list(models_col.find())
    for m in models:
        m["_id"] = str(m["_id"])
        m["brand_id"] = str(m["brand_id"])
    return JsonResponse(models, safe=False)

@csrf_exempt
def delete_model(request, model_id):
    if request.method == "DELETE":
        result = models_col.delete_one({"_id": ObjectId(model_id)})
        return JsonResponse({"deleted_count": result.deleted_count})
    return JsonResponse({"error": "Invalid request method"}, status=405)

# ========== CATEGORY ==========
@csrf_exempt
def create_category(request):
    if request.method == "POST":
        data = json.loads(request.body)
        category_id = categories_col.insert_one({
            "brand_id": ObjectId(data["brand_id"]),
            "name": data["name"],
            "image": data.get("image", ""),
            "created_date": datetime.utcnow()
        }).inserted_id
        return JsonResponse({"message": "Category created", "category_id": str(category_id)})

def list_categories(request):
    cats = list(categories_col.find())
    for c in cats: c["_id"], c["brand_id"] = str(c["_id"]), str(c["brand_id"])
    return JsonResponse(cats, safe=False)

@csrf_exempt
def delete_category(request, category_id):
    result = categories_col.delete_one({"_id": ObjectId(category_id)})
    return JsonResponse({"deleted_count": result.deleted_count})

# ========== PRODUCT ==========
@csrf_exempt
def create_product(request):
    if request.method == "POST":
        data = json.loads(request.body)
        product_id = products_col.insert_one({
            "brand_id": ObjectId(data["brand_id"]),
            "category_id": ObjectId(data["category_id"]),
            "name": data["name"],
            "short_desc": data.get("short_desc", ""),
            "price": data["price"],
            "stock": data.get("stock", 0),
            "image": data.get("image", ""),
            "created_date": datetime.utcnow()
        }).inserted_id
        return JsonResponse({"message": "Product created", "product_id": str(product_id)})

def list_products(request):
    prods = list(products_col.find())
    for p in prods:
        p["_id"], p["brand_id"], p["category_id"] = str(p["_id"]), str(p["brand_id"]), str(p["category_id"])
    return JsonResponse(prods, safe=False)

@csrf_exempt
def delete_product(request, product_id):
    result = products_col.delete_one({"_id": ObjectId(product_id)})
    return JsonResponse({"deleted_count": result.deleted_count})

def product_count(request):
    count = products_col.count_documents({})
    return JsonResponse({"total_products": count})

@csrf_exempt
def update_stock(request, product_id, action):
    if request.method == "POST":
        qty = int(request.GET.get("quantity", 1))
        update = {"$inc": {"stock": qty}} if action == "increase" else {"$inc": {"stock": -qty}}
        products_col.update_one({"_id": ObjectId(product_id)}, update)
        product = products_col.find_one({"_id": ObjectId(product_id)})
        return JsonResponse({"message": "Stock updated", "product_id": product_id, "new_stock": product["stock"]})
