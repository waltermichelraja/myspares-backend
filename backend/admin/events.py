import threading
from bson import ObjectId
from datetime import datetime, timezone
from pymongo.errors import PyMongoError
from pymongo import UpdateOne
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

def handle_stock_decrease(product_id: ObjectId, new_stock: int):
    now=datetime.now(timezone.utc)
    if new_stock <= 0:
        handle_product_delete(product_id)
        logger.warning(f"[STOCK ZERO] product {product_id} removed from all carts (out of stock)")
        return
    affected_carts=list(carts_collection.find({"items.product_id": product_id}))
    if not affected_carts:
        return
    user_requests=[]
    total_requested=0
    for cart in affected_carts:
        for item in cart["items"]:
            if item["product_id"]==product_id:
                qty=int(item["quantity"])
                user_requests.append({
                    "cart_id": cart["_id"],
                    "requested": qty,
                    "fraction": 0.0,
                    "allocated": 0
                })
                total_requested+=qty
    if total_requested==0:
        return
    if total_requested<=new_stock:
        logger.info(f"[STOCK OK] total requested ({total_requested}) <= new stock ({new_stock}) - no redistribution needed")
        return
    for req in user_requests:
        exact_share=(req["requested"]/total_requested)*new_stock
        req["allocated"]=int(exact_share)
        req["fraction"]=exact_share-req["allocated"]
    allocated_total=sum(r["allocated"] for r in user_requests)
    remainder=max(0, new_stock-allocated_total)
    user_requests.sort(key=lambda r: r["fraction"], reverse=True)
    for i in range(min(remainder, len(user_requests))):
        user_requests[i]["allocated"]+=1
    bulk_ops=[]
    for req in user_requests:
        cart_id=req["cart_id"]
        new_qty=req["allocated"]
        cart=next((c for c in affected_carts if c["_id"]==cart_id), None)
        if not cart:
            continue
        new_items=[]
        for item in cart["items"]:
            if item["product_id"]==product_id:
                if new_qty>0:
                    item["quantity"]=new_qty
                    new_items.append(item)
            else:
                new_items.append(item)
        new_subtotal=Cart.calculate_subtotal(new_items)
        bulk_ops.append(UpdateOne(
            {"_id": cart_id},
            {"$set": {"items": new_items, "subtotal": new_subtotal, "updated_at": now}}
        ))
        logger.info(f"[CART ADJUSTED] cart {cart_id}: product {product_id} qty set to {new_qty}")
    if bulk_ops:
        carts_collection.bulk_write(bulk_ops)
        logger.info(f"[STOCK REDISTRIBUTION] product {product_id}: total requested {total_requested}, new stock {new_stock}")
        audits_collection.insert_one({
            "event": "stock_redistribution",
            "product_id": product_id,
            "total_requested": total_requested,
            "new_stock": new_stock,
            "timestamp": now
        })

def handle_product_update(change):
    updated_fields=change.get("updateDescription", {}).get("updatedFields", {})
    product_id=change["documentKey"]["_id"]
    price_changed="price" in updated_fields
    offer_changed=any(k.startswith("offers") for k in updated_fields.keys())
    stock_changed="stock" in updated_fields
    if price_changed or offer_changed:
        logger.info(f"[PRODUCT UPDATE] product {product_id} updated fields: {list(updated_fields.keys())}")
        recalculate_cart_subtotals(product_id)
    if stock_changed:
        new_stock=int(updated_fields["stock"])
        handle_stock_decrease(product_id, new_stock)

def handle_product_delete(product_id: ObjectId):
    now=datetime.now(timezone.utc)
    affected_carts=carts_collection.find({"items.product_id": product_id})
    for cart in affected_carts:
        new_items=[item for item in cart["items"] if item["product_id"]!=product_id]
        new_subtotal=Cart.calculate_subtotal(new_items)
        carts_collection.update_one(
            {"_id": cart["_id"]},
            {"$set": {"items": new_items, "subtotal": new_subtotal, "updated_at": now}}
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
            logger.error(f"[WATCH ERROR] change stream error on {coll.name}: {e}. retrying...")
        except Exception as e:
            logger.exception(f"[WATCH ERROR] unexpected error on {coll.name}: {e}. retrying...")

def start_watchers():
    for coll in collections:
        t=threading.Thread(target=watch_collection, args=(coll,), daemon=True)
        t.start()
        logger.info(f"[WATCHER STARTED] watching collection {coll.name}")