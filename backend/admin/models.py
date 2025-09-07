from django.conf import settings
from pymongo.errors import PyMongoError
from datetime import datetime, timezone
import re

brands_collection=settings.MONGO_DB["brands"]
models_collection=settings.MONGO_DB["models"]

brands_collection.create_index("brand_code", unique=True)
# brands_collection.create_index("brand_code", unique=True)


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
            print(f"[DB ERROR] failed to fetch brands: {e}")
            raise RuntimeError("database error: unable to fetch brands")

    @classmethod
    def brand_insert(cls, brand_name, brand_code, image_url):
        cls.validate_fields(brand_name, brand_code, image_url)
        if brands_collection.find_one({"brand_code": brand_code}):
            raise ValueError("brand_code already exists")

        try:
            brand_doc={
                "brand_name": brand_name,
                "brand_code": brand_code,
                "image_url": image_url,
                "created_at": datetime.now(timezone.utc),
            }
            result=brands_collection.insert_one(brand_doc)
            brand_doc["_id"]=result.inserted_id
            return cls.from_dict(brand_doc)
        except PyMongoError as e:
            print(f"[DB ERROR] failed to insert brand: {e}")
            raise RuntimeError("database error: unable to insert brand")

    @classmethod
    def brand_delete(cls, brand_code):
        try:
            result=brands_collection.delete_one({"brand_code": brand_code})
            if result.deleted_count == 0:
                raise ValueError("brand not found")
            return True
        except PyMongoError as e:
            print(f"[DB ERROR] failed to delete brand: {e}")
            raise RuntimeError("database error: unable to delete brand")

    @classmethod
    def brand_fetch(cls, brand_code):
        try:
            doc=brands_collection.find_one({"brand_code": brand_code})
            if not doc:
                raise ValueError("brand not found")
            return cls.from_dict(doc).to_dict()
        except PyMongoError as e:
            print(f"[DB ERROR] failed to fetch brand: {e}")
            raise RuntimeError("database error: unable to fetch brand")


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
        try:
            brand_doc=brands_collection.find_one({"brand_code": brand_code})
            if not brand_doc:
                raise ValueError("brand not found")

            docs=list(models_collection.find({"brand_id": brand_doc["_id"]}))
            return [cls.from_dict(doc).to_dict() for doc in docs]
        except PyMongoError as e:
            print(f"[DB ERROR] failed to fetch models: {e}")
            raise RuntimeError("database error: unable to fetch models")

    @classmethod
    def model_insert(cls, brand_code, model_name, model_code, image_url):
        cls.validate_fields(model_name, model_code, image_url)

        brand_doc=brands_collection.find_one({"brand_code": brand_code})
        if not brand_doc:
            raise ValueError("brand not found")
        brand_id=brand_doc["_id"]

        if models_collection.find_one({"brand_id": brand_id, "model_code": model_code}):
            raise ValueError("model_code already exists for this brand")

        try:
            model_doc={
                "brand_id": brand_id,
                "model_name": model_name,
                "model_code": model_code,
                "image_url": image_url,
                "created_at": datetime.now(timezone.utc),
            }
            result=models_collection.insert_one(model_doc)
            model_doc["_id"]=result.inserted_id
            return cls.from_dict(model_doc)
        except PyMongoError as e:
            print(f"[DB ERROR] failed to insert model: {e}")
            raise RuntimeError("database error: unable to insert model")

    @classmethod
    def model_delete(cls, brand_code, model_code):
        try:
            brand_doc=brands_collection.find_one({"brand_code": brand_code})
            if not brand_doc:
                raise ValueError("brand not found")

            result=models_collection.delete_one({"brand_id": brand_doc["_id"], "model_code": model_code})
            if result.deleted_count == 0:
                raise ValueError("model not found")
            return True
        except PyMongoError as e:
            print(f"[DB ERROR] failed to delete model: {e}")
            raise RuntimeError("database error: unable to delete model")

    @classmethod
    def model_fetch(cls, brand_code, model_code):
        try:
            brand_doc=brands_collection.find_one({"brand_code": brand_code})
            if not brand_doc:
                raise ValueError("brand not found")

            doc=models_collection.find_one({"brand_id": brand_doc["_id"], "model_code": model_code})
            if not doc:
                raise ValueError("model not found")
            return cls.from_dict(doc).to_dict()
        except PyMongoError as e:
            print(f"[DB ERROR] failed to fetch model: {e}")
            raise RuntimeError("database error: unable to fetch model")
