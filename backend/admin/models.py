from django.conf import settings
from pymongo.errors import PyMongoError
from datetime import datetime, timezone
import re

brands_collection=settings.MONGO_DB["brands"]
brands_collection.create_index("brand_code", unique=True)


class Brand:
    def __init__(self, brand_name, brand_code, image_url, created_at=None, _id=None):
        self.id=_id
        self.brand_name=brand_name
        self.brand_code=brand_code
        self.image_url=image_url
        self.created_at=created_at or datetime.now(timezone.utc)

    @staticmethod
    def validate_fields(brand_name, brand_code, image_url):
        if not re.match(r"^[A-Za-z ]+$", str(brand_name)) or not re.match(r"^.{2,50}$", str(brand_name)):
            raise ValueError("invalid brand_name: " + (
                "too long/short" if not re.match(r"^.{2,50}$", str(brand_name))
                else "invalid characters"
            ))

        if not re.match(r"^[A-Z]{2,10}$", str(brand_code)):
            raise ValueError("invalid brand_code: must be 2–10 uppercase letters")

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