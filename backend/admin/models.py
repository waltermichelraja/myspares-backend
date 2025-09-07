from django.conf import settings
from pymongo.errors import PyMongoError
from datetime import datetime, timezone
import re

brands_collection=settings.MONGO_DB["brands"]
models_collection=settings.MONGO_DB["models"]
categories_collection=settings.MONGO_DB["categories"]

if "model_code_1" in models_collection.index_information():
    models_collection.drop_index("model_code_1")

if "category_code_1" in categories_collection.index_information():
    categories_collection.drop_index("category_code_1")

brands_collection.create_index("brand_code", unique=True)
models_collection.create_index([("brand_id", 1), ("model_code", 1)], unique=True)
categories_collection.create_index([("model_id", 1), ("category_code", 1)], unique=True)


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
    def brands_list(cls):
        try:
            docs=list(brands_collection.find())
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
        result=brands_collection.delete_one({"brand_code": brand_code})
        if result.deleted_count==0:
            raise ValueError("brand not found")
        return True

    @classmethod
    def brand_fetch(cls, brand_code):
        doc=brands_collection.find_one({"brand_code": brand_code})
        if not doc:
            raise ValueError("brand not found")
        return cls.from_dict(doc).to_dict()


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
    def models_list(cls, brand_code):
        brand_doc=brands_collection.find_one({"brand_code": brand_code})
        if not brand_doc:
            raise ValueError("brand not found")
        docs=list(models_collection.find({"brand_id": brand_doc["_id"]}))
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
        result=models_collection.delete_one({"brand_id": brand_doc["_id"], "model_code": model_code})
        if result.deleted_count==0:
            raise ValueError("model not found")
        return True

    @classmethod
    def model_fetch(cls, brand_code, model_code):
        brand_doc=brands_collection.find_one({"brand_code": brand_code})
        if not brand_doc:
            raise ValueError("brand not found")
        doc=models_collection.find_one({"brand_id": brand_doc["_id"], "model_code": model_code})
        if not doc:
            raise ValueError("model not found")
        return cls.from_dict(doc).to_dict()


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
    def categories_list(cls, brand_code, model_code):
        brand_doc=brands_collection.find_one({"brand_code": brand_code})
        if not brand_doc:
            raise ValueError("brand not found")
        model_doc=models_collection.find_one({"brand_id": brand_doc["_id"], "model_code": model_code})
        if not model_doc:
            raise ValueError("model not found")
        docs=list(categories_collection.find({"model_id": model_doc["_id"]}))
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
        result=categories_collection.delete_one({"model_id": model_doc["_id"], "category_code": category_code})
        if result.deleted_count==0:
            raise ValueError("category not found")
        return True

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
