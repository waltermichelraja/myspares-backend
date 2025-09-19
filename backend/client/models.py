from datetime import datetime, timezone
from bson import ObjectId
from .admin import *


class Cart:
    def __init__(self, user_id, items=None, created_at=None, updated_at=None, _id=None):
        self.id=_id
        self.user_id=user_id
        self.items=items or []
        self.created_at=created_at or datetime.now(timezone.utc)
        self.updated_at=updated_at or datetime.now(timezone.utc)

    def to_dict(self):
        return {
            "_id": str(self.id) if self.id else None,
            "user_id": str(self.user_id),
            "items": [
                {
                    "product_id": str(item["product_id"]),
                    "quantity": item["quantity"],
                    "added_at": str(item.get("added_at", datetime.now(timezone.utc)))
                } for item in self.items
            ],
            "created_at": str(self.created_at),
            "updated_at": str(self.updated_at),
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            user_id=str(data["user_id"]),
            items=data.get("items", []),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            _id=str(data.get("_id")) if data.get("_id") else None,
        )

    @classmethod
    def get_cart(cls, user_id):
        doc=carts_collection.find_one({"user_id": ObjectId(user_id)})
        if not doc:
            return cls(user_id=user_id)
        return cls.from_dict(doc)

    @classmethod
    def add_item(cls, user_id, product_id, quantity=1):
        if not users_collection.find_one({"_id": ObjectId(user_id)}):
            raise ValueError("user not found")
        if not products_collection.find_one({"_id": ObjectId(product_id)}):
            raise ValueError("product not found")

        now=datetime.now(timezone.utc)
        cart=carts_collection.find_one({"user_id": ObjectId(user_id)})
        if not cart:
            cart_doc={
                "user_id": ObjectId(user_id),
                "items": [{"product_id": ObjectId(product_id), "quantity": quantity, "added_at": now}],
                "created_at": now,
                "updated_at": now,
            }
            result=carts_collection.insert_one(cart_doc)
            cart_doc["_id"]=result.inserted_id
            return cls.from_dict(cart_doc)
        item_found=False
        for item in cart["items"]:
            if item["product_id"]==ObjectId(product_id):
                item["quantity"]+=quantity
                item_found=True
                break
        if not item_found:
            cart["items"].append({"product_id": ObjectId(product_id), "quantity": quantity, "added_at": now})

        cart["updated_at"]=now
        carts_collection.update_one({"_id": cart["_id"]}, {"$set": cart})
        return cls.from_dict(cart)

    @classmethod
    def remove_item(cls, user_id, product_id, quantity=1):
        now=datetime.now(timezone.utc)
        result=carts_collection.update_one(
            {"user_id": ObjectId(user_id), "items.product_id": ObjectId(product_id)},
            {"$inc": {"items.$.quantity": -quantity}, "$set": {"updated_at": now}}
        )
        if result.modified_count==0:
            raise ValueError("cart or item not found")
        carts_collection.update_one(
            {"user_id": ObjectId(user_id)},
            {"$pull": {"items": {"quantity": {"$lte": 0}}}, "$set": {"updated_at": now}}
        )
        cart_doc=carts_collection.find_one({"user_id": ObjectId(user_id)})
        return cls.from_dict(cart_doc)