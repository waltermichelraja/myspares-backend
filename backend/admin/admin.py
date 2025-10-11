import logging
from django.conf import settings


brands_collection=settings.MONGO_DB["brands"]
models_collection=settings.MONGO_DB["models"]
categories_collection=settings.MONGO_DB["categories"]
products_collection=settings.MONGO_DB["products"]

brands_collection.create_index("brand_code", unique=True)
models_collection.create_index([("brand_id", 1), ("model_code", 1)], unique=True)
categories_collection.create_index([("model_id", 1), ("category_code", 1)], unique=True)
products_collection.create_index([("category_id", 1), ("product_code", 1)], unique=True)

carts_collection=settings.MONGO_DB["carts"]

audits_collection=settings.MONGO_DB["audits"]

temporary_users_collection=settings.MONGO_DB["temporary_users"]

blacklisted_tokens_collection=settings.MONGO_DB["blacklisted_tokens"]

logger=logging.getLogger("admin_events")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch=logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter=logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
