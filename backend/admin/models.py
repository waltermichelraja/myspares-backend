from pymongo.errors import PyMongoError
from datetime import datetime, timezone
from client.models import Cart
from .admin import *
import re


class Brand:
    def __init__(self, brand_name, brand_code, image_url, created_at=None, _id=None):
        self.id=_id
        self.brand_name=brand_name
        self.brand_code=brand_code
        self.image_url=image_url
        self.created_at=created_at or datetime.now(timezone.utc)

    @staticmethod
    def validate_fields(brand_name, brand_code, image_url):
        brand_name=str(brand_name).strip()
        brand_code=str(brand_code).strip()
        image_url=str(image_url).strip()
        if not re.match(r"^[A-Za-z0-9 ]+$", str(brand_name)) or not re.match(r"^.{2,50}$", str(brand_name)):
            raise ValueError("invalid brand_name: " + (
                    "brand_name too long/short" if not re.match(r"^.{2,50}$", str(brand_name)) 
                    else "invalid characters"
                )
            )
        if not re.match(r"^[A-Z0-9]+$", str(brand_code)) or not re.match(r"^.{2,10}$", str(brand_code)):
            raise ValueError("invalid brand_code: " + (
                    "brand_code too long/short" if not re.match(r"^.{2,10}$", str(brand_code)) 
                    else "invalid characters"
                )
            )
        if not image_url or not isinstance(image_url, str):
            raise ValueError("invalid image_url: must be a non-empty string")

    def to_dict(self):
        return {
            "_id": str(self.id) if self.id else None,
            "brand_name": self.brand_name,
            "brand_code": self.brand_code,
            "image_url": self.image_url,
            "created_at": str(self.created_at),
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            brand_name=data.get("brand_name"),
            brand_code=data.get("brand_code"),
            image_url=data.get("image_url"),
            created_at=data.get("created_at"),
            _id=data.get("_id"),
        )

    @classmethod
    def brands_list(cls, limit=20):
        try:
            docs=list(brands_collection.find().limit(limit))
            return [cls.from_dict(doc).to_dict() for doc in docs]
        except PyMongoError as e:
            raise RuntimeError(f"database error: {e}")

    @classmethod
    def brand_insert(cls, brand_name, brand_code, image_url):
        cls.validate_fields(brand_name, brand_code, image_url)
        if brands_collection.find_one({"brand_code": brand_code}):
            raise ValueError("brand_code already exists")
        brand_doc={
            "brand_name": brand_name,
            "brand_code": brand_code,
            "image_url": image_url,
            "created_at": datetime.now(timezone.utc)
        }
        result=brands_collection.insert_one(brand_doc)
        brand_doc["_id"]=result.inserted_id
        return cls.from_dict(brand_doc)

    @classmethod
    def brand_delete(cls, brand_code):
        brand_doc=brands_collection.find_one({"brand_code": brand_code})
        if not brand_doc:
            raise ValueError("brand not found")
        brand_id=brand_doc["_id"]
        model_docs=list(models_collection.find({"brand_id": brand_id}, {"_id": 1}))
        model_ids=[d["_id"] for d in model_docs]
        category_ids=[]

        if model_ids:
            category_docs=list(categories_collection.find({"model_id": {"$in": model_ids}}, {"_id": 1}))
            category_ids=[d["_id"] for d in category_docs]
        try:
            client=settings.MONGO_DB.client
            with client.start_session() as session:
                with session.start_transaction():
                    if category_ids:
                        products_collection.delete_many({"category_id": {"$in": category_ids}}, session=session)
                    if model_ids:
                        categories_collection.delete_many({"model_id": {"$in": model_ids}}, session=session)
                        models_collection.delete_many({"_id": {"$in": model_ids}}, session=session)
                    brands_collection.delete_one({"_id": brand_id}, session=session)
            return True
        except Exception:
            try:
                if category_ids:
                    products_collection.delete_many({"category_id": {"$in": category_ids}})
                if model_ids:
                    categories_collection.delete_many({"model_id": {"$in": model_ids}})
                    models_collection.delete_many({"_id": {"$in": model_ids}})
                brands_collection.delete_one({"_id": brand_id})
                return True
            except PyMongoError as e:
                raise RuntimeError(f"database error during cascade delete: {e}") from e

    @classmethod
    def brand_fetch(cls, brand_code):
        doc=brands_collection.find_one({"brand_code": brand_code})
        if not doc:
            raise ValueError("brand not found")
        return cls.from_dict(doc).to_dict()
    
    @classmethod
    def brand_search(cls, query):
        try:
            regex={"$regex": query, "$options": "i"}
            docs=list(brands_collection.find(
                {"$or": [
                    {"brand_name": regex},
                    {"brand_code": regex}
                ]}
            ))
            return [cls.from_dict(doc).to_dict() for doc in docs]
        except PyMongoError as e:
            raise RuntimeError(f"database error during search: {e}")
    
    @classmethod
    def brand_update(cls, brand_code, updates: dict):
        brand_doc=brands_collection.find_one({"brand_code": brand_code})
        if not brand_doc:
            raise ValueError("brand not found")
        allowed_fields=["brand_name", "image_url"]
        update_data={}
        for field in allowed_fields:
            if field in updates:
                if field=="brand_name":
                    if not isinstance(updates["brand_name"], str) or not (2 <= len(updates["brand_name"].strip()) <= 50):
                        raise ValueError("invalid brand_name")
                    update_data["brand_name"]=updates["brand_name"].strip()
                elif field=="image_url":
                    if not isinstance(updates["image_url"], str) or not updates["image_url"].strip():
                        raise ValueError("invalid image_url")
                    update_data["image_url"]=updates["image_url"].strip()
        if not update_data:
            raise ValueError("no valid fields to update")
        result=brands_collection.update_one({"_id": brand_doc["_id"]}, {"$set": update_data})
        if result.modified_count==0:
            raise RuntimeError("update failed")
        updated_doc=brands_collection.find_one({"_id": brand_doc["_id"]})
        return cls.from_dict(updated_doc)


class Model:
    def __init__(self, brand_id, model_name, model_code, image_url, created_at=None, _id=None):
        self.id=_id
        self.brand_id=brand_id
        self.model_name=model_name
        self.model_code=model_code
        self.image_url=image_url
        self.created_at=created_at or datetime.now(timezone.utc)

    @staticmethod
    def validate_fields(model_name, model_code, image_url):
        model_name=str(model_name).strip()
        model_code=str(model_code).strip()
        image_url=str(image_url).strip()
        if not re.match(r"^[A-Za-z0-9 ]+$", str(model_name)) or not re.match(r"^.{2,50}$", str(model_name)):
            raise ValueError("invalid model_name: " + (
                    "model_name too long/short" if not re.match(r"^.{2,50}$", str(model_name)) 
                    else "invalid characters"
                )
            )
        if not re.match(r"^[A-Z0-9]+$", str(model_code)) or not re.match(r"^.{2,10}$", str(model_code)):
            raise ValueError("invalid model_code: " + (
                    "model_code too long/short" if not re.match(r"^.{2,10}$", str(model_code)) 
                    else "invalid characters"
                )
            )
        if not image_url or not isinstance(image_url, str):
            raise ValueError("invalid image_url: must be a non-empty string")

    def to_dict(self):
        return {
            "_id": str(self.id) if self.id else None,
            "brand_id": str(self.brand_id),
            "model_name": self.model_name,
            "model_code": self.model_code,
            "image_url": self.image_url,
            "created_at": str(self.created_at),
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            brand_id=data.get("brand_id"),
            model_name=data.get("model_name"),
            model_code=data.get("model_code"),
            image_url=data.get("image_url"),
            created_at=data.get("created_at"),
            _id=data.get("_id"),
        )

    @classmethod
    def models_list(cls, brand_code, limit=20):
        brand_doc=brands_collection.find_one({"brand_code": brand_code})
        if not brand_doc:
            raise ValueError("brand not found")
        docs=list(models_collection.find({"brand_id":brand_doc["_id"]}).limit(limit))
        return [cls.from_dict(doc).to_dict() for doc in docs]

    @classmethod
    def model_insert(cls, brand_code, model_name, model_code, image_url):
        cls.validate_fields(model_name, model_code, image_url)
        brand_doc=brands_collection.find_one({"brand_code": brand_code})
        if not brand_doc:
            raise ValueError("brand not found")
        if models_collection.find_one({"brand_id": brand_doc["_id"], "model_code": model_code}):
            raise ValueError("model_code already exists for this brand")
        model_doc={
            "brand_id": brand_doc["_id"],
            "model_name": model_name,
            "model_code": model_code,
            "image_url": image_url,
            "created_at": datetime.now(timezone.utc)
        }
        result=models_collection.insert_one(model_doc)
        model_doc["_id"]=result.inserted_id
        return cls.from_dict(model_doc)

    @classmethod
    def model_delete(cls, brand_code, model_code):
        brand_doc=brands_collection.find_one({"brand_code": brand_code})
        if not brand_doc:
            raise ValueError("brand not found")
        model_doc=models_collection.find_one({"brand_id": brand_doc["_id"], "model_code": model_code})
        if not model_doc:
            raise ValueError("model not found")
        
        model_id=model_doc["_id"]
        category_docs=list(categories_collection.find({"model_id": model_id}, {"_id": 1}))
        category_ids=[d["_id"] for d in category_docs]
        try:
            client=settings.MONGO_DB.client
            with client.start_session() as session:
                with session.start_transaction():
                    if category_ids:
                        products_collection.delete_many({"category_id": {"$in": category_ids}}, session=session)
                        categories_collection.delete_many({"_id": {"$in": category_ids}}, session=session)
                    models_collection.delete_one({"_id": model_id}, session=session)
            return True
        except Exception:
            try:
                if category_ids:
                    products_collection.delete_many({"category_id": {"$in": category_ids}})
                    categories_collection.delete_many({"_id": {"$in": category_ids}})
                models_collection.delete_one({"_id": model_id})
                return True
            except PyMongoError as e:
                raise RuntimeError(f"database error during cascade delete: {e}") from e

    @classmethod
    def model_fetch(cls, brand_code, model_code):
        brand_doc=brands_collection.find_one({"brand_code": brand_code})
        if not brand_doc:
            raise ValueError("brand not found")
        doc=models_collection.find_one({"brand_id": brand_doc["_id"], "model_code": model_code})
        if not doc:
            raise ValueError("model not found")
        return cls.from_dict(doc).to_dict()

    @classmethod
    def model_search(cls, brand_code, query):
        brand_doc=brands_collection.find_one({"brand_code": brand_code})
        if not brand_doc:
            raise ValueError("brand not found")
        regex={"$regex": query, "$options": "i"}
        docs=list(models_collection.find(
            {"brand_id": brand_doc["_id"], "$or": [
                {"model_name": regex},
                {"model_code": regex}
            ]}
        ))
        return [cls.from_dict(doc).to_dict() for doc in docs]

    @classmethod
    def model_update(cls, brand_code, model_code, updates: dict):
        brand_doc=brands_collection.find_one({"brand_code": brand_code})
        if not brand_doc:
            raise ValueError("brand not found")
        model_doc=models_collection.find_one({"brand_id": brand_doc["_id"], "model_code": model_code})
        if not model_doc:
            raise ValueError("model not found")
        allowed_fields=["model_name", "image_url"]
        update_data={}
        for field in allowed_fields:
            if field in updates:
                if field=="model_name":
                    if not isinstance(updates["model_name"], str) or not (2 <= len(updates["model_name"].strip()) <= 50):
                        raise ValueError("invalid model_name")
                    update_data["model_name"]=updates["model_name"].strip()
                elif field=="image_url":
                    if not isinstance(updates["image_url"], str) or not updates["image_url"].strip():
                        raise ValueError("invalid image_url")
                    update_data["image_url"]=updates["image_url"].strip()
        if not update_data:
            raise ValueError("no valid fields to update")
        result=models_collection.update_one({"_id": model_doc["_id"]}, {"$set": update_data})
        if result.modified_count==0:
            raise RuntimeError("update failed")
        updated_doc=models_collection.find_one({"_id": model_doc["_id"]})
        return cls.from_dict(updated_doc)


class Category:
    def __init__(self, model_id, category_name, category_code, image_url, created_at=None, _id=None):
        self.id=_id
        self.model_id=model_id
        self.category_name=category_name
        self.category_code=category_code
        self.image_url=image_url
        self.created_at=created_at or datetime.now(timezone.utc)

    @staticmethod
    def validate_fields(category_name, category_code, image_url):
        category_name=str(category_name).strip()
        category_code=str(category_code).strip()
        image_url=str(image_url).strip()
        if not re.match(r"^[A-Za-z0-9 ]+$", str(category_name)) or not re.match(r"^.{2,50}$", str(category_name)):
            raise ValueError("invalid category_name: " + (
                    "category_name too long/short" if not re.match(r"^.{2,50}$", str(category_name)) 
                    else "invalid characters"
                )
            )
        if not re.match(r"^[A-Z0-9]+$", str(category_code)) or not re.match(r"^.{2,10}$", str(category_code)):
            raise ValueError("invalid category_code: " + (
                    "category_code too long/short" if not re.match(r"^.{2,10}$", str(category_code)) 
                    else "invalid characters"
                )
            )
        if not image_url or not isinstance(image_url, str):
            raise ValueError("invalid image_url: must be a non-empty string")

    def to_dict(self):
        return {
            "_id": str(self.id) if self.id else None,
            "model_id": str(self.model_id),
            "category_name": self.category_name,
            "category_code": self.category_code,
            "image_url": self.image_url,
            "created_at": str(self.created_at),
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            model_id=data.get("model_id"),
            category_name=data.get("category_name"),
            category_code=data.get("category_code"),
            image_url=data.get("image_url"),
            created_at=data.get("created_at"),
            _id=data.get("_id"),
        )

    @classmethod
    def categories_list(cls, brand_code, model_code, limit=20):
        brand_doc=brands_collection.find_one({"brand_code": brand_code})
        if not brand_doc:
            raise ValueError("brand not found")
        model_doc=models_collection.find_one({"brand_id": brand_doc["_id"], "model_code": model_code})
        if not model_doc:
            raise ValueError("model not found")
        docs=list(categories_collection.find({"model_id": model_doc["_id"]}).limit(limit))
        return [cls.from_dict(doc).to_dict() for doc in docs]

    @classmethod
    def category_insert(cls, brand_code, model_code, category_name, category_code, image_url):
        cls.validate_fields(category_name, category_code, image_url)
        brand_doc=brands_collection.find_one({"brand_code": brand_code})
        if not brand_doc:
            raise ValueError("brand not found")
        model_doc=models_collection.find_one({"brand_id": brand_doc["_id"], "model_code": model_code})
        if not model_doc:
            raise ValueError("model not found")
        if categories_collection.find_one({"model_id": model_doc["_id"], "category_code": category_code}):
            raise ValueError("category_code already exists for this model")
        category_doc={
            "model_id": model_doc["_id"],
            "category_name": category_name,
            "category_code": category_code,
            "image_url": image_url,
            "created_at": datetime.now(timezone.utc)
        }
        result=categories_collection.insert_one(category_doc)
        category_doc["_id"]=result.inserted_id
        return cls.from_dict(category_doc)

    @classmethod
    def category_delete(cls, brand_code, model_code, category_code):
        brand_doc=brands_collection.find_one({"brand_code": brand_code})
        if not brand_doc:
            raise ValueError("brand not found")
        model_doc=models_collection.find_one({"brand_id": brand_doc["_id"], "model_code": model_code})
        if not model_doc:
            raise ValueError("model not found")
        category_doc=categories_collection.find_one({"model_id": model_doc["_id"], "category_code": category_code})
        if not category_doc:
            raise ValueError("category not found")
        category_id=category_doc["_id"]
        try:
            client=settings.MONGO_DB.client
            with client.start_session() as session:
                with session.start_transaction():
                    products_collection.delete_many({"category_id": category_id}, session=session)
                    categories_collection.delete_one({"_id": category_id}, session=session)
            return True
        except Exception:
            try:
                products_collection.delete_many({"category_id": category_id})
                categories_collection.delete_one({"_id": category_id})
                return True
            except PyMongoError as e:
                raise RuntimeError(f"database error during cascade delete: {e}") from e

    @classmethod
    def category_fetch(cls, brand_code, model_code, category_code):
        brand_doc=brands_collection.find_one({"brand_code": brand_code})
        if not brand_doc:
            raise ValueError("brand not found")
        model_doc=models_collection.find_one({"brand_id": brand_doc["_id"], "model_code": model_code})
        if not model_doc:
            raise ValueError("model not found")
        doc=categories_collection.find_one({"model_id": model_doc["_id"], "category_code": category_code})
        if not doc:
            raise ValueError("category not found")
        return cls.from_dict(doc).to_dict()
    
    @classmethod
    def category_search(cls, brand_code, model_code, query):
        brand_doc=brands_collection.find_one({"brand_code": brand_code})
        if not brand_doc:
            raise ValueError("brand not found")
        model_doc=models_collection.find_one({"brand_id": brand_doc["_id"], "model_code": model_code})
        if not model_doc:
            raise ValueError("model not found")
        regex={"$regex": query, "$options": "i"}
        docs=list(categories_collection.find(
            {"model_id": model_doc["_id"], "$or": [
                {"category_name": regex},
                {"category_code": regex}
            ]}
        ))
        return [cls.from_dict(doc).to_dict() for doc in docs]

    @classmethod
    def category_update(cls, brand_code, model_code, category_code, updates: dict):
        brand_doc=brands_collection.find_one({"brand_code": brand_code})
        if not brand_doc:
            raise ValueError("brand not found")
        model_doc=models_collection.find_one({"brand_id": brand_doc["_id"], "model_code": model_code})
        if not model_doc:
            raise ValueError("model not found")
        category_doc=categories_collection.find_one({"model_id": model_doc["_id"], "category_code": category_code})
        if not category_doc:
            raise ValueError("category not found")
        allowed_fields=["category_name", "image_url"]
        update_data={}
        for field in allowed_fields:
            if field in updates:
                if field=="category_name":
                    if not isinstance(updates["category_name"], str) or not (2 <= len(updates["category_name"].strip()) <= 50):
                        raise ValueError("invalid category_name")
                    update_data["category_name"]=updates["category_name"].strip()
                elif field=="image_url":
                    if not isinstance(updates["image_url"], str) or not updates["image_url"].strip():
                        raise ValueError("invalid image_url")
                    update_data["image_url"]=updates["image_url"].strip()
        if not update_data:
            raise ValueError("no valid fields to update")
        result=categories_collection.update_one({"_id": category_doc["_id"]}, {"$set": update_data})
        if result.modified_count==0:
            raise RuntimeError("update failed")
        updated_doc=categories_collection.find_one({"_id": category_doc["_id"]})
        return cls.from_dict(updated_doc)


class Product:
    def __init__(self, category_id, product_name, product_code, code, 
                 description, price, stock, image_url, 
                 created_at=None, reviews=None, offers=None, _id=None):
        self.id=_id
        self.category_id=category_id
        self.product_name=product_name
        self.product_code=product_code
        self.code=code
        self.description=description
        self.price=price
        self.stock=stock
        self.image_url=image_url
        self.created_at=created_at or datetime.now(timezone.utc)
        self.reviews=reviews or []
        self.offers=offers or {}

    @staticmethod
    def validate_fields(product_name, product_code, description, price, stock, image_url):
        if not isinstance(product_name, str) or not (2 <= len(product_name.strip()) <= 50):
            raise ValueError("invalid product_name")
        if not re.match(r"^[A-Z0-9]+$", str(product_code).strip()):
            raise ValueError("invalid product_code")
        if not isinstance(description, str) or len(description.strip())==0:
            raise ValueError("invalid description")
        if not isinstance(price, (int, float)) or price < 0:
            raise ValueError("invalid price")
        if not isinstance(stock, int) or stock < 0:
            raise ValueError("invalid stock")
        if not isinstance(image_url, str) or len(image_url.strip())==0:
            raise ValueError("invalid image_url")

    def to_dict(self):
        return {
            "_id": str(self.id) if self.id else None,
            "category_id": str(self.category_id),
            "product_name": self.product_name,
            "product_code": self.product_code,
            "code": self.code,
            "description": self.description,
            "price": self.price,
            "stock": self.stock,
            "image_url": self.image_url,
            "created_at": str(self.created_at),
            "reviews": self.reviews,
            "offers": self.offers,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            category_id=data.get("category_id"),
            product_name=data.get("product_name"),
            product_code=data.get("product_code"),
            code=data.get("code"),
            description=data.get("description"),
            price=data.get("price"),
            stock=data.get("stock"),
            image_url=data.get("image_url"),
            created_at=data.get("created_at"),
            reviews=data.get("reviews", []),
            offers=data.get("offers", {}),
            _id=data.get("_id"),
        )

    @classmethod
    def products_list(cls, brand_code, model_code, category_code, limit=20):
        brand_doc=brands_collection.find_one({"brand_code": brand_code})
        if not brand_doc:
            raise ValueError("brand not found")
        model_doc=models_collection.find_one({"brand_id": brand_doc["_id"], "model_code": model_code})
        if not model_doc:
            raise ValueError("model not found")
        category_doc=categories_collection.find_one({"model_id": model_doc["_id"], "category_code": category_code})
        if not category_doc:
            raise ValueError("category not found")
        docs=list(products_collection.find({"category_id": category_doc["_id"]}).limit(limit))
        return [cls.from_dict(doc).to_dict() for doc in docs]

    @classmethod
    def product_insert(cls, brand_code, model_code, category_code, product_name, product_code, description, price, stock, image_url):
        cls.validate_fields(product_name, product_code, description, price, stock, image_url)
        brand_doc=brands_collection.find_one({"brand_code": brand_code})
        if not brand_doc:
            raise ValueError("brand not found")
        model_doc=models_collection.find_one({"brand_id": brand_doc["_id"], "model_code": model_code})
        if not model_doc:
            raise ValueError("model not found")
        category_doc=categories_collection.find_one({"model_id": model_doc["_id"], "category_code": category_code})
        if not category_doc:
            raise ValueError("category not found")
        if products_collection.find_one({"category_id": category_doc["_id"], "product_code": product_code}):
            raise ValueError("product_code already exists for this category")
        code=f"{brand_doc['brand_code']}-{model_doc['model_code']}-{category_doc['category_code']}-{product_code}"
        product_doc={
            "category_id": category_doc["_id"],
            "product_name": product_name,
            "product_code": product_code,
            "code": code,
            "description": description,
            "price": price,
            "stock": stock,
            "image_url": image_url,
            "created_at": datetime.now(timezone.utc),
            "reviews": [],
            "offers": {}
        }
        result=products_collection.insert_one(product_doc)
        product_doc["_id"]=result.inserted_id
        return cls.from_dict(product_doc)

    @classmethod
    def product_delete(cls, brand_code, model_code, category_code, product_code):
        brand_doc=brands_collection.find_one({"brand_code": brand_code})
        if not brand_doc:
            raise ValueError("brand not found")
        model_doc=models_collection.find_one({"brand_id": brand_doc["_id"], "model_code": model_code})
        if not model_doc:
            raise ValueError("model not found")
        category_doc=categories_collection.find_one({"model_id": model_doc["_id"], "category_code": category_code})
        if not category_doc:
            raise ValueError("category not found")
        result=products_collection.delete_one({"category_id": category_doc["_id"], "product_code": product_code})
        if result.deleted_count==0:
            raise ValueError("product not found")
        return True

    @classmethod
    def product_fetch(cls, brand_code, model_code, category_code, product_code):
        brand_doc=brands_collection.find_one({"brand_code": brand_code})
        if not brand_doc:
            raise ValueError("brand not found")
        model_doc=models_collection.find_one({"brand_id": brand_doc["_id"], "model_code": model_code})
        if not model_doc:
            raise ValueError("model not found")
        category_doc=categories_collection.find_one({"model_id": model_doc["_id"], "category_code": category_code})
        if not category_doc:
            raise ValueError("category not found")
        doc=products_collection.find_one({"category_id": category_doc["_id"], "product_code": product_code})
        if not doc:
            raise ValueError("product not found")
        return cls.from_dict(doc).to_dict()

    @classmethod
    def product_search(cls, brand_code, model_code, category_code, query):
        brand_doc=brands_collection.find_one({"brand_code": brand_code})
        if not brand_doc:
            raise ValueError("brand not found")
        model_doc=models_collection.find_one({"brand_id": brand_doc["_id"], "model_code": model_code})
        if not model_doc:
            raise ValueError("model not found")
        category_doc=categories_collection.find_one({"model_id": model_doc["_id"], "category_code": category_code})
        if not category_doc:
            raise ValueError("category not found")
        regex={"$regex": query, "$options": "i"}
        docs=list(products_collection.find(
            {"category_id": category_doc["_id"], "$or": [
                {"product_name": regex},
                {"product_code": regex},
                {"description": regex}
            ]}
        ))
        return [cls.from_dict(doc).to_dict() for doc in docs]


    @classmethod
    def product_update(cls, brand_code, model_code, category_code, product_code, updates: dict):
        brand_doc=brands_collection.find_one({"brand_code": brand_code})
        if not brand_doc:
            raise ValueError("brand not found")
        model_doc=models_collection.find_one({"brand_id": brand_doc["_id"], "model_code": model_code})
        if not model_doc:
            raise ValueError("model not found")
        category_doc=categories_collection.find_one({"model_id": model_doc["_id"], "category_code": category_code})
        if not category_doc:
            raise ValueError("category not found")
        product_doc=products_collection.find_one({
            "category_id": category_doc["_id"],
            "product_code": product_code
        })
        if not product_doc:
            raise ValueError("product not found")
        allowed_fields=["product_name", "description", "price", "stock", "image_url", "offers"]
        update_data={}
        for field in allowed_fields:
            if field in updates:
                if field=="price":
                    try:
                        update_data["price"]=int(updates["price"])
                    except (ValueError, TypeError):
                        raise ValueError("price must be an integer")
                elif field=="stock":
                    try:
                        update_data["stock"]=int(updates["stock"])
                    except (ValueError, TypeError):
                        raise ValueError("stock must be an integer")
                elif field=="offers":
                    offers=updates["offers"]
                    if not isinstance(offers, dict):
                        raise ValueError("offers must be an object with discount, validity, description")
                    required_fields=["discount", "validity", "description"]
                    for rf in required_fields:
                        if rf not in offers:
                            raise ValueError(f"missing offer field: {rf}")
                    structured_offer={}
                    try:
                        structured_offer["discount"]=float(offers["discount"])
                    except (ValueError, TypeError):
                        raise ValueError("discount must be a number")

                    validity=offers.get("validity")
                    if not isinstance(validity, dict) or "from" not in validity or "to" not in validity:
                        raise ValueError("validity must be an object with 'from' and 'to' fields (timestamps)")
                    try:
                        structured_offer["validity"]={
                            "from": int(validity["from"]),
                            "to": int(validity["to"])
                        }
                    except (ValueError, TypeError):
                        raise ValueError("'from' and 'to' inside validity must be integers (timestamps)")
                    structured_offer["description"]=str(offers["description"]).strip()
                    update_data["offers"]=structured_offer
                else:
                    update_data[field]=str(updates[field]).strip()
        if not update_data:
            raise ValueError("no valid fields to update")
        result=products_collection.update_one(
            {"_id": product_doc["_id"]},
            {"$set": update_data}
        )
        if result.modified_count==0:
            raise RuntimeError("update failed")
        updated_doc=products_collection.find_one({"_id": product_doc["_id"]})
        now=datetime.now(timezone.utc)
        affected_carts=carts_collection.find({"items.product_id": updated_doc["_id"]})
        for cart in affected_carts:
            new_subtotal=Cart.calculate_subtotal(cart["items"])
            carts_collection.update_one(
                {"_id": cart["_id"]},
                {"$set": {"subtotal": new_subtotal, "updated_at": now}}
            )
        return cls.from_dict(updated_doc)


class Admin:
    @classmethod
    def audits_list(cls, limit: int=50):
        try:
            cursor=audits_collection.find().limit(limit)
            logs=list(cursor)
            for log in logs:
                log["_id"]=str(log["_id"])
            return {"count": len(logs), "logs": logs}
        except PyMongoError as e:
            raise RuntimeError(f"database error fetching audits: {e}")

    @classmethod
    def audit_search(cls, query: str, sort_field: str="-timestamp", limit: int=50):
        try:
            if not query:
                raise ValueError("query is required")
            regex={"$regex": query, "$options": "i"}
            search_filter={
                "$or": [
                    {"collection": regex},
                    {"operation": regex},
                    {"document_key._id": regex},
                    {"full_document": regex},
                    {"update_description.updatedFields": regex},
                ]
            }
            direction=-1 if sort_field.startswith("-") else 1
            field=sort_field.lstrip("-")
            docs=list(audits_collection.find(search_filter).sort(field, direction).limit(limit))
            for doc in docs:
                doc["_id"]=str(doc["_id"])
            return {"count": len(docs), "logs": docs}
        except PyMongoError as e:
            raise RuntimeError(f"database error searching audits: {e}")