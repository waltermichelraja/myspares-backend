from datetime import datetime, timezone
from bson import ObjectId
from .admin import *


class Cart:
    def __init__(self, user_id, items=None, created_at=None, updated_at=None, subtotal=0, _id=None):
        self.id=_id
        self.user_id=ObjectId(user_id) if not isinstance(user_id, ObjectId) else user_id
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
            user_id=data["user_id"],
            items=data.get("items", []),
            subtotal=data.get("subtotal", 0),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
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
                    price=price*(1-(discount/100))
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
        product=products_collection.find_one({"_id": ObjectId(product_id)})
        if not product:
            raise ValueError("product not found")
        stock=product.get("stock", 0)
        if stock<=0:
            raise ValueError("product is out of stock")
        now=datetime.now(timezone.utc)
        cart=carts_collection.find_one({"user_id": ObjectId(user_id)})
        if not cart:
            if quantity> stock:
                raise ValueError(f"only {stock} items available in stock")
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
                new_quantity=item["quantity"]+quantity
                if new_quantity>stock:
                    raise ValueError(f"only {stock} items available in stock")
                item["quantity"]=new_quantity
                item_found=True
                break
        if not item_found:
            if quantity>stock:
                raise ValueError(f"only {stock} items available in stock")
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


class Address:
    def __init__(self, user_id, name=None, phone_number=None, address_line1=None, address_line2=None,
                 city=None, state=None, pincode=None, country=None, updated_at=None, _id=None):
        self.id=_id
        self.user_id=ObjectId(user_id) if not isinstance(user_id, ObjectId) else user_id
        self.name=name
        self.phone_number=phone_number
        self.address_line1=address_line1
        self.address_line2=address_line2
        self.city=city
        self.state=state
        self.country=country
        self.pincode=pincode
        self.updated_at=updated_at or datetime.now(timezone.utc)

    def to_dict(self):
        return {
            "_id": str(self.id) if self.id else None,
            "user_id": str(self.user_id),
            "name": self.name,
            "phone_number": self.phone_number,
            "address_line1": self.address_line1,
            "address_line2": self.address_line2,
            "city": self.city,
            "state": self.state,
            "country": self.country,
            "pincode": self.pincode,
            "updated_at": str(self.updated_at)
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            user_id=data["user_id"],
            name=data.get("name"),
            phone_number=data.get("phone_number"),
            address_line1=data.get("address_line1"),
            address_line2=data.get("address_line2"),
            city=data.get("city"),
            state=data.get("state"),
            country=data.get("country"),
            pincode=data.get("pincode"),
            updated_at=data.get("updated_at"),
            _id=data.get("_id")
        )

    @classmethod
    def create_address(cls, user_id, name, phone_number):
        doc={
            "user_id": ObjectId(user_id),
            "name": str(name),
            "phone_number": str(phone_number),
            "address_line1": "",
            "address_line2": "",
            "city": "",
            "state": "",
            "country": "",
            "pincode": "",
            "updated_at": datetime.now(timezone.utc),
        }
        result=addresses_collection.insert_one(doc)
        doc["_id"]=result.inserted_id
        return cls.from_dict(doc)

    @classmethod
    def address_fetch(cls, user_id):
        doc=addresses_collection.find_one({"user_id": ObjectId(user_id)})
        if not doc:
            return cls(user_id=user_id)
        return cls.from_dict(doc)

    @classmethod
    def address_update(cls, user_id, **kwargs):
        allowed_fields=["name", "phone_number", "address_line1", "address_line2",
                          "city", "state", "pincode", "country"]
        update_data={field: kwargs[field] for field in allowed_fields if field in kwargs}
        if not update_data:
            raise ValueError("no valid fields provided for update")
        update_data["updated_at"]=datetime.now(timezone.utc)
        addresses_collection.update_one({"user_id": ObjectId(user_id)}, {"$set": update_data}, upsert=True)
        doc=addresses_collection.find_one({"user_id": ObjectId(user_id)})
        return cls.from_dict(doc)
    