import threading
import time
from bson import ObjectId
from datetime import datetime, timezone, timedelta
from pymongo.errors import PyMongoError
from pymongo import UpdateOne
from client.models import Cart
from .admin import *


collections=[
    brands_collection,
    models_collection,
    categories_collection,
    products_collection,
    temporary_users_collection,
    blacklisted_tokens_collection,
    audits_collection
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
            logger.info(f"[UPDATE CART] cart {cart['_id']} recalculated due to change in product {product_id}")
        except Exception as e:
            logger.exception(f"[UPDATE CART ERROR] failed to recalculate cart {cart['_id']} for product {product_id}: {e}")

def handle_stock_decrease(product_id: ObjectId, new_stock: int):
    now=datetime.now(timezone.utc)
    if new_stock<=0:
        handle_product_delete(product_id)
        logger.warning(f"[ZERO STOCK] product {product_id} removed from all carts (out of stock)")
        return
    affected_carts=list(carts_collection.find({"items.product_id": product_id}))
    if not affected_carts:
        return
    cart_map={cart["_id"]: cart for cart in affected_carts}
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
    if total_requested==0 or total_requested<=new_stock:
        logger.info(f"[STOCK OK] total requested ({total_requested}) <= stock ({new_stock})")
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
        cart=cart_map.get(cart_id)
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
        logger.info(f"[ADJUST CART] cart {cart_id}: product {product_id} quantity set to {new_qty}")
    if bulk_ops:
        carts_collection.bulk_write(bulk_ops)
        logger.info(f"[REDISTRIBUTE STOCK] product {product_id}: requested {total_requested}, stock {new_stock}")
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
    if "price" in updated_fields or any(k.startswith("offers") for k in updated_fields.keys()):
        recalculate_cart_subtotals(product_id)
    if "stock" in updated_fields:
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
        logger.info(f"[CLEANUP CART] removed product {product_id} from cart {cart['_id']}")

def cleanup_temp_users(days: int=1):
    cutoff=datetime.now(timezone.utc)-timedelta(days=days)
    try:
        result=temporary_users_collection.delete_many({"created_at": {"$lt": cutoff}})
        logger.info(f"[CLEANUP USER] removed {result.deleted_count} temporary users older than {days} day")
    except PyMongoError as e:
        logger.error(f"[CLEANUP USER ERROR] {e}")

def cleanup_old_tokens(days: int=7):
    cutoff=datetime.now(timezone.utc)-timedelta(days=days)
    try:
        result=blacklisted_tokens_collection.delete_many({"blacklisted_at": {"$lt": cutoff}})
        logger.info(f"[CLEANUP TOKEN] removed {result.deleted_count} blacklisted tokens older than {days} days")
    except PyMongoError as e:
        logger.error(f"[CLEANUP TOKEN ERROR] {e}")

def cleanup_old_audits(days: int=30):
    cutoff=datetime.now(timezone.utc)-timedelta(days=days)
    try:
        result=audits_collection.delete_many({"timestamp": {"$lt": cutoff}})
        logger.info(f"[CLEANUP AUDIT] removed {result.deleted_count} audit logs older than {days} days")
    except PyMongoError as e:
        logger.error(f"[CLEANUP AUDIT ERROR] {e}")

def start_cleanup(interval_sec=3600):
    def run():
        while True:
            cleanup_temp_users(1)
            cleanup_old_tokens(7)
            cleanup_old_audits(30)
            time.sleep(interval_sec)
    t=threading.Thread(target=run, daemon=True)
    t.start()
    logger.info("[PERIODIC CLEANUP] background cleanup thread started")

def watch_collection(coll):
    pipeline=[{"$match": {"operationType": {"$in": ["insert", "update", "delete"]}}}]
    while True:
        try:
            with coll.watch(pipeline=pipeline, full_document="updateLookup") as stream:
                for change in stream:
                    if coll!=audits_collection:
                        log_audit(change)
                    if coll==products_collection:
                        if change["operationType"]=="update":
                            handle_product_update(change)
                        elif change["operationType"]=="delete":
                            handle_product_delete(change["documentKey"]["_id"])
        except PyMongoError as e:
            logger.error(f"[WATCH ERROR] {coll.name}: {e}. retrying...")
            time.sleep(5)
        except Exception as e:
            logger.exception(f"[WATCH ERROR] unexpected error on {coll.name}: {e}. retrying...")
            time.sleep(5)

def start_watchers():
    start_cleanup()
    for coll in collections:
        t=threading.Thread(target=watch_collection, args=(coll,), daemon=True)
        t.start()
        logger.info(f"[WATCHER STARTED] watching collection {coll.name}")
