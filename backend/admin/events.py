import threading
from bson import ObjectId
from datetime import datetime, timezone
from pymongo.errors import PyMongoError
from client.models import Cart
from .admin import *


collections=[
    brands_collection,
    models_collection,
    categories_collection,
    products_collection
]

def log_audit(change, admin_id=None):
    audit_doc={
        "collection": change["ns"]["coll"],
        "operation": change["operationType"],
        "document_key": change.get("documentKey"),
        "full_document": change.get("fullDocument"),
        "update_description": change.get("updateDescription"),
        "timestamp": datetime.now(timezone.utc)
    }
    try:
        audits_collection.insert_one(audit_doc)
    except PyMongoError as e:
        logger.error(f"[AUDIT ERROR] failed to log audit: {e}")

def recalculate_cart_subtotals(product_id: ObjectId):
    now=datetime.now(timezone.utc)
    affected_carts=carts_collection.find({"items.product_id": product_id})
    for cart in affected_carts:
        try:
            new_subtotal=Cart.calculate_subtotal(cart["items"])
            carts_collection.update_one(
                {"_id": cart["_id"]},
                {"$set": {"subtotal": new_subtotal, "updated_at": now}}
            )
            logger.info(f"[CART UPDATED] cart {cart['_id']} recalculated due to change in product {product_id}")
        except Exception as e:
            logger.exception(f"[CART UPDATE ERROR] failed to recalculate cart {cart['_id']} for product {product_id}: {e}")

def handle_product_update(change):
    updated_fields=change.get("updateDescription", {}).get("updatedFields", {})
    product_id=change["documentKey"]["_id"]
    price_changed="price" in updated_fields
    offer_changed=any(k.startswith("offers") for k in updated_fields.keys())
    if price_changed or offer_changed:
        logger.info(f"[PRODUCT UPDATE] product {product_id} updated fields: {list(updated_fields.keys())}")
        recalculate_cart_subtotals(product_id)

def handle_product_delete(product_id: ObjectId):
    now=datetime.now(timezone.utc)
    affected_carts=carts_collection.find({"items.product_id": product_id})
    for cart in affected_carts:
        new_items=[item for item in cart["items"] if item["product_id"] != product_id]
        new_subtotal=Cart.calculate_subtotal(new_items)
        carts_collection.update_one(
            {"_id": cart["_id"]},
            {"$set": {
                "items": new_items,
                "subtotal": new_subtotal,
                "updated_at": now
            }}
        )
        logger.info(f"[CART CLEANUP] removed deleted product {product_id} from cart {cart['_id']}")

def watch_collection(coll):
    pipeline=[{"$match": {"operationType": {"$in": ["insert", "update", "delete"]}}}]
    while True:
        try:
            with coll.watch(pipeline=pipeline, full_document="updateLookup") as stream:
                for change in stream:
                    log_audit(change)
                    if coll==products_collection:
                        if change["operationType"]=="update":
                            handle_product_update(change)
                        elif change["operationType"]=="delete":
                            product_id=change["documentKey"]["_id"]
                            handle_product_delete(product_id)
        except PyMongoError as e:
            logger.error(f"[WATCH ERROR] change stream error on {coll.name}: {e}. Retrying...")
        except Exception as e:
            logger.exception(f"[WATCH ERROR] unexpected error on {coll.name}: {e}. Retrying...")

def start_watchers():
    for coll in collections:
        t=threading.Thread(target=watch_collection, args=(coll,), daemon=True)
        t.start()
        logger.info(f"[WATCHER STARTED] watching collection {coll.name}")