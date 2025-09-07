from django.conf import settings
from pymongo.errors import PyMongoError
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import re
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

users_collection=settings.MONGO_DB["users"]
users_collection.create_index("phone_number", unique=True)

blacklisted_tokens_collection=settings.MONGO_DB["blacklisted_tokens"]


class User:
    def __init__(self, username, phone_number, password_hash, created_at=None, _id=None):
        self.id=_id
        self.username=username
        self.phone_number=str(phone_number)
        self.password_hash=password_hash
        self.created_at=created_at or datetime.utcnow()

    @staticmethod
    def validate_fields(username, phone_number, password):
        if not re.match(r"^[A-Za-z0-9_]+$", str(username)) or not re.match(r"^.{1,24}$", str(username)):
            raise ValueError("invalid username: " + (
                    "username too long" if not re.match(r"^.{1,24}$", str(username)) 
                    else "invalid characters"
                )
            )
        if not re.match(r"^\d{10,15}$", str(phone_number)):
            raise ValueError("invalid phone number")
        
        if not re.match(r"^(?=.*[A-Z])(?=.*[a-z])(?=.*[\W_]).{1,14}$", str(password)):
            raise ValueError("invalid password: " + (
                    "password too long" if not re.match(r"^.{1,14}$", str(password)) 
                    else "must include uppercase, lowercase, and special character"
                )
            )

    @staticmethod
    def hash_password(password):
        return generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self, include_password=False):
        data={
            "_id": str(self.id) if self.id else None,
            "username": str(self.username),
            "phone_number": str(self.phone_number),
            "created_at": str(self.created_at),
        }
        if include_password:
            data["password_hash"]=str(self.password_hash)
        return data

    @classmethod
    def from_dict(cls, data):
        return cls(
            username=data.get("username"),
            phone_number=data.get("phone_number"),
            password_hash=data.get("password_hash"),
            created_at=data.get("created_at"),
            _id=data.get("_id"),
        )

    @classmethod
    def create(cls, username, phone_number, password):
        cls.validate_fields(username, phone_number)

        if users_collection.find_one({"phone_number": str(phone_number)}):
            raise ValueError("phone number already registered")

        user_doc={
            "username": str(username),
            "phone_number": str(phone_number),
            "password_hash": cls.hash_password(password),
            "created_at": datetime.utcnow()
        }
        try:
            result=users_collection.insert_one(user_doc)
            user_doc["_id"]=result.inserted_id
            return cls.from_dict(user_doc)
        except PyMongoError as e:
            print(f"[DB ERROR] failed to insert user: {e}")
            raise RuntimeError("database error: unable to register user")
        

class TokenManager:
    @staticmethod
    def generate_tokens(user: User):
        refresh=RefreshToken()
        refresh["user_id"]=str(user.id)
        refresh["phone_number"]=user.phone_number

        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }

    @staticmethod
    def refresh_tokens(refresh_token: str):
        try:
            refresh=RefreshToken(refresh_token)
            new_access=refresh.access_token
            return {
                "refresh": str(refresh),
                "access": str(new_access),
            }
        except TokenError as e:
            raise ValueError("invalid or expired refresh token") from e

    @staticmethod
    def blacklist_token(refresh_token: str):
        try:
            blacklisted_tokens_collection.insert_one({
                "token": refresh_token,
                "blacklisted_at": datetime.utcnow()
            })
        except PyMongoError as e:
            print(f"[DB ERROR] failed to blacklist token: {e}")
            raise RuntimeError("server error: unable to blacklist token")

    @staticmethod
    def is_blacklisted(refresh_token: str)->bool:
        return blacklisted_tokens_collection.find_one({"token": refresh_token}) is not None