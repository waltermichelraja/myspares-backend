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

        # Insert new brand
        brand_id = brands_col.insert_one({
            "brand_name": data["brand_name"],
            "brand_code": data["brand_code"],   # required
            "image_url": data.get("image_url", ""),  # optional
            "created_date": datetime.utcnow()
        }).inserted_id

        return JsonResponse({
            "message": "Brand created",
            "brand_id": str(brand_id),
            "brand_code": data["brand_code"]
        })


def list_brands_by_code(request,brand_code):
    brands = list(
        brands_col.find(
            {"brand_code": brand_code},
            {"_id": 0, "brand_name": 1, "brand_code": 1, "image_url": 1}
        )
    )
    return JsonResponse(brands, safe=False)

@csrf_exempt
def delete_brand(request, brand_code):
    if request.method == "DELETE":
        result = brands_col.delete_one({"brand_code": brand_code})
        return JsonResponse({"deleted_count": result.deleted_count})
    return JsonResponse({"error": "Invalid request method"}, status=405)

#========= MODEL ==========
@csrf_exempt
def create_model(request, brand_code):  # accept brand_code from URL
    if request.method == "POST":
        data = json.loads(request.body)

        # 1. Find brand by brand_code
        brand = brands_col.find_one({"brand_code": brand_code})
        if not brand:
            return JsonResponse({"error": f"No brand found with code {brand_code}"}, status=404)

        # 2. Validate model_code
        if "model_code" not in data or "model_name" not in data:
            return JsonResponse({"error": "model_code and model_name are required"}, status=400)

        # 3. Insert new model with brand_id reference
        model_id = models_col.insert_one({
            "brand_id": brand["_id"],          # store ObjectId of brand
            "model_name": data["model_name"],
            "model_code": data["model_code"],
            "image_url": data.get("image_url", ""),  # optional
            "created_at": datetime.utcnow()
        }).inserted_id

        return JsonResponse({"message": "Model created", "model_id": str(model_id)})
    return JsonResponse({"error": "Invalid method"}, status=405)

def list_models_by_brand(request, brand_code):
    # 1. Find the brand by code
    brand = brands_col.find_one({"brand_code": brand_code})
    if not brand:
        return JsonResponse({"error": f"No brand found with code {brand_code}"}, status=404)

    # 2. Fetch models linked to that brand
    models = list(models_col.find({"brand_id": brand["_id"]}))
    for m in models:
        m["_id"] = str(m["_id"])
        m["brand_id"] = str(m["brand_id"])

    return JsonResponse(models, safe=False)

@csrf_exempt
def delete_model(request, model_code):
    if request.method == "DELETE":
        # Find the model by model_code
        model = models_col.find_one({"model_code": model_code})
        if not model:
            return JsonResponse({"error": f"No model found with code {model_code}"}, status=404)

        # Delete the model
        models_col.delete_one({"_id": model["_id"]})
        return JsonResponse({"message": f"Model with code {model_code} deleted successfully"})
    
    return JsonResponse({"error": "Invalid method"}, status=405)


# ========== CATEGORY ==========
@csrf_exempt
def create_category(request, model_code):
    if request.method == "POST":
        data = json.loads(request.body)

        # 1. Find model
        model = models_col.find_one({"model_code": model_code})
        if not model:
            return JsonResponse({"error": f"No model found with code {model_code}"}, status=404)

        # 2. Get brand_id from model
        brand_id = model["brand_id"]

        # 3. Insert category
        category_id = categories_col.insert_one({
            "brand_id": brand_id,
            "model_id": model["_id"],
            "name": data["name"],
            "category_code": data.get("category_code", ""),  # optional unique code
            "image_url": data.get("image_url", ""),          # optional
            "created_at": datetime.utcnow()
        }).inserted_id

        return JsonResponse({"message": "Category created", "category_id": str(category_id)})

    return JsonResponse({"error": "Invalid method"}, status=405)


def list_categories(request, model_code):
    # 1. Find model
    model = models_col.find_one({"model_code": model_code})
    if not model:
        return JsonResponse({"error": f"No model found with code {model_code}"}, status=404)

    # 2. Fetch categories linked to this model
    cats = list(categories_col.find({"model_id": model["_id"]}))
    for c in cats:
        c["_id"] = str(c["_id"])
        c["brand_id"] = str(c["brand_id"])
        c["model_id"] = str(c["model_id"])
    return JsonResponse(cats, safe=False)

@csrf_exempt
def delete_category(request, category_code):
    if request.method == "DELETE":
        # Delete the category
        result = categories_col.delete_one({"category_code": category_code})
        if result.deleted_count == 0:
            return JsonResponse({"error": f"No category found with code {category_code}"}, status=404)
        return JsonResponse({"message": f"Category {category_code} deleted", "deleted_count": result.deleted_count})

    return JsonResponse({"error": "Invalid request method"}, status=405)


#============= PRODUCT =============
@csrf_exempt
def create_product(request, category_code):
    if request.method == "POST":
        data = json.loads(request.body)

        # 1. Find category
        category = categories_col.find_one({"category_code": category_code})
        if not category:
            return JsonResponse({"error": f"No category found with code {category_code}"}, status=404)

        # Get IDs from DB
        brand_id = category["brand_id"]
        model_id = category.get("model_id")
        category_id = category["_id"]

        # 2. Generate code_prefix using brand_code and model_code if available
        brand = brands_col.find_one({"_id": brand_id})
        brand_code = brand["brand_code"] if brand else "BRD"

        model_code = "MOD"
        if model_id:
            model = models_col.find_one({"_id": model_id})
            model_code = model["model_code"] if model else "MOD"

        code_prefix = f"{brand_code}-{model_code}-{category_code}-{data['product_code']}"

        # 3. Create product document (basic fields only)
        product_doc = {
        "brand_id": brand_id,
        "model_id": model_id,
        "category_id": category_id,
        "name": data["name"],
        "product_code": data.get("product_code", ""),
        "code_prefix": code_prefix,
        "short_desc": data.get("short_desc", ""),
        "price": data["price"],
        "stock": int(data.get("stock", 1)),
        "image": data.get("image", ""),
        "created_date": datetime.utcnow(),
        "reviews": [],      # initialize empty
        "offers": {}        # initialize empty
    }

        # 4. Insert into DB
        product_id = products_col.insert_one(product_doc).inserted_id

        # 5. Convert ObjectIds to strings for JSON response
        response_doc = product_doc.copy()
        response_doc["_id"] = str(product_id)
        response_doc["brand_id"] = str(brand_id)
        response_doc["model_id"] = str(model_id) if model_id else None
        response_doc["category_id"] = str(category_id)

        return JsonResponse({"message": "Product created", "product": response_doc})

    return JsonResponse({"error": "Invalid request method"}, status=405)


# =========================================
# LIST PRODUCTS BY CATEGORY
# =========================================
def list_products(request, category_code, model_code=None):
    # 1. Find category by category_code
    category = categories_col.find_one({"category_code": category_code})
    if not category:
        return JsonResponse({"error": f"No category found with code {category_code}"}, status=404)

    # 2. Build query
    query = {"category_id": category["_id"]}

    # 3. If model_code is provided, filter by model_id as well
    if model_code:
        model = models_col.find_one({"model_code": model_code})
        if not model:
            return JsonResponse({"error": f"No model found with code {model_code}"}, status=404)
        query["model_id"] = model["_id"]

    # 4. Fetch products
    prods = list(products_col.find(query))
    
    # 5. Convert ObjectIds to strings
    for p in prods:
        p["_id"] = str(p["_id"])
        p["brand_id"] = str(p["brand_id"])
        p["model_id"] = str(p.get("model_id")) if p.get("model_id") else None
        p["category_id"] = str(p["category_id"])
    
    return JsonResponse(prods, safe=False)

# =========================================
# DELETE PRODUCT BY ObjectId
# =========================================
@csrf_exempt
def delete_product(request, product_id):
    if request.method == "DELETE":
        try:
            result = products_col.delete_one({"_id": ObjectId(product_id)})
            if result.deleted_count == 0:
                return JsonResponse({"error": "No product found with this ID"}, status=404)
            return JsonResponse({"message": "Product deleted", "deleted_count": result.deleted_count})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=405)


# =========================================
# PRODUCT COUNT BY product_code
# =========================================
def product_stock(request, product_code):
    # 1. Find product by product_code
    product = products_col.find_one({"product_code": product_code})
    
    if not product:
        return JsonResponse({"error": f"No product found with code {product_code}"}, status=404)
    
    # 2. Return current stock
    return JsonResponse({
        "product_code": product_code,
        "stock": product.get("stock", 0)
    })



# =========================================
# UPDATE STOCK BY product_code
# action = increase / decrease
# =========================================
@csrf_exempt
def update_stock(request, product_code, action):
    if request.method == "POST":
        qty = int(request.GET.get("quantity", 1))
        if action not in ["increase", "decrease"]:
            return JsonResponse({"error": "Invalid action"}, status=400)

        update = {"$inc": {"stock": qty}} if action == "increase" else {"$inc": {"stock": -qty}}

        product = products_col.find_one_and_update(
            {"product_code": product_code},
            update,
            return_document=True
        )

        if not product:
            return JsonResponse({"error": f"No product found with code {product_code}"}, status=404)

        # Calculate new stock after update
        new_stock = product.get("stock", 0) + (qty if action == "increase" else -qty)

        return JsonResponse({"message": "Stock updated", "product_code": product_code, "new_stock": new_stock})

    return JsonResponse({"error": "Invalid request method"}, status=405)