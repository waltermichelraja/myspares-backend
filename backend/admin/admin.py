from django.conf import settings


brands_collection=settings.MONGO_DB["brands"]
models_collection=settings.MONGO_DB["models"]
categories_collection=settings.MONGO_DB["categories"]
products_collection=settings.MONGO_DB["products"]

brands_collection.create_index("brand_code", unique=True)
models_collection.create_index([("brand_id", 1), ("model_code", 1)], unique=True)
categories_collection.create_index([("model_id", 1), ("category_code", 1)], unique=True)
products_collection.create_index([("category_id", 1), ("product_code", 1)], unique=True)
