import threading
from datetime import datetime, timezone
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
    audits_collection.insert_one(audit_doc)

def watch_collection(coll):
    pipeline=[{"$match": {"operationType": {"$in": ["insert", "update", "delete"]}}}]
    with coll.watch(pipeline=pipeline, full_document="updateLookup") as stream:
        for change in stream:
            log_audit(change)

def start_watchers():
    for coll in collections:
        t=threading.Thread(target=watch_collection, args=(coll,), daemon=True)
        t.start()