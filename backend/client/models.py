from datetime import datetime, timezone
from bson import ObjectId
from .admin import *


class Cart:
    def __init__(self, user_id, items=None, created_at=None, updated_at=None, subtotal=0, _id=None):
        self.id=_id
        self.user_id=user_id
        self.items=items or []
        self.subtotal=subtotal
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
            "subtotal": self.subtotal,
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
            subtotal=data.get("subtotal", 0),
            _id=str(data.get("_id")) if data.get("_id") else None,
        )

    @staticmethod
    def calculate_subtotal(items):
        subtotal=0
        now=datetime.now(timezone.utc).timestamp()
        for item in items:
            product=products_collection.find_one({"_id": item["product_id"]})
            if not product:
                continue
            price=product.get("price", 0)
            offers=product.get("offers", {})
            if offers:
                discount=offers.get("discount", 0)
                validity=offers.get("validity", {})
                from_ts=validity.get("from", 0)
                to_ts=validity.get("to", 0)
                if from_ts <= now <= to_ts:
                    price=price * (1-(discount/100))
            subtotal+=price*item["quantity"]
        return round(subtotal, 2)

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
            cart_doc["subtotal"]=cls.calculate_subtotal(cart_doc["items"])
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
        cart["subtotal"]=cls.calculate_subtotal(cart["items"])
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
        if not cart_doc:
            return cls(user_id=user_id)

        cart_doc["subtotal"]=cls.calculate_subtotal(cart_doc["items"])
        carts_collection.update_one({"_id": cart_doc["_id"]}, {"$set": {"subtotal": cart_doc["subtotal"], "updated_at": now}})
        return cls.from_dict(cart_doc)
    