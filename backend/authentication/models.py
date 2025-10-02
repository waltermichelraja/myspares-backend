from pymongo.errors import PyMongoError
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone, timedelta
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from .admin import *
from client.models import Cart, Address
import re


class Auth:
    def __init__(self, username, phone_number, password_hash, created_at=None, _id=None):
        self.id=_id
        self.username=username
        self.phone_number=str(phone_number)
        self.password_hash=password_hash
        self.created_at=created_at or datetime.now(timezone.utc)

    @staticmethod
    def validate_fields(username, phone_number, password):
        if not re.match(r"^[A-Za-z ]+$", str(username)) or not re.match(r"^.{4,24}$", str(username)):
            raise ValueError("invalid username: " + (
                "username too long/short" if not re.match(r"^.{4,24}$", str(username))
                else "invalid characters"
            ))
        if not re.match(r"^\d{10,15}$", str(phone_number)):
            raise ValueError("invalid phone number: must be 10–15 digits")

        if not re.match(r"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[\W_]).{4,16}$", str(password)):
            raise ValueError("invalid password: " + (
                "password too long/short" if not re.match(r"^.{4,16}$", str(password))
                else "must include uppercase, lowercase, number, and special character"
            ))

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
        cls.validate_fields(username, phone_number, password)
        try:
            if users_collection.find_one({"phone_number": str(phone_number)}):
                raise ValueError("phone number already registered")

            user_doc={
                "username": str(username),
                "phone_number": str(phone_number),
                "password_hash": cls.hash_password(password),
                "created_at": datetime.now(timezone.utc),
            }
            result=users_collection.insert_one(user_doc)
            user_doc["_id"]=result.inserted_id
            user=cls.from_dict(user_doc)
            try:
                Cart.create_cart(user_id=str(user.id))
            except Exception as cart_err:
                print(f"[WARN] failed to auto-create cart for user {user.id}: {cart_err}")
            try:
                Address.create_address(
                    user_id=str(user.id),
                    name=user.username,
                    phone_number=user.phone_number
                )
            except Exception as addr_err:
                print(f"[WARN] failed to auto-create address for user {user.id}: {addr_err}")
            return user
        except PyMongoError as e:
            print(f"[DB ERROR] failed to insert/find user: {e}")
            raise RuntimeError("database error: unable to register user")


class TokenManager:
    @staticmethod
    def generate_tokens(user: Auth):
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
    def blacklist_token(refresh_token: str, access_token: str=None, user_id: str=None):
        try:
            doc={
                "user_id": user_id,
                "token": {
                    "refresh": refresh_token,
                    "access": access_token,
                },
                "blacklisted_at": datetime.now(timezone.utc),
            }
            blacklisted_tokens_collection.insert_one(doc)
        except PyMongoError as e:
            print(f"[DB ERROR] failed to blacklist tokens: {e}")
            raise RuntimeError("server error: unable to blacklist tokens")

    @staticmethod
    def is_blacklisted_refresh(refresh_token: str) -> bool:
        try:
            return blacklisted_tokens_collection.find_one({"token.refresh": refresh_token}) is not None
        except PyMongoError as e:
            print(f"[DB ERROR] failed to check refresh blacklist: {e}")
            raise RuntimeError("server error: unable to check token blacklist")

    @staticmethod
    def is_blacklisted_access(access_token: str) -> bool:
        try:
            return blacklisted_tokens_collection.find_one({"token.access": access_token}) is not None
        except PyMongoError as e:
            print(f"[DB ERROR] failed to check access blacklist: {e}")
            raise RuntimeError("server error: unable to check token blacklist")

    @staticmethod
    def verify_access_token(token: str):
        if TokenManager.is_blacklisted_access(token):
            raise ValueError("blacklisted access token")
        try:
            access=AccessToken(token)
            return dict(access.payload)
        except(TokenError, InvalidToken) as e:
            raise ValueError("invalid or expired access token") from e

    @staticmethod
    def cleanup_old_tokens(days=7):
        cutoff=datetime.now(timezone.utc)-timedelta(days=days)
        try:
            result=blacklisted_tokens_collection.delete_many(
                {"blacklisted_at": {"$lt": cutoff}}
            )
            print(f"[CLEANUP] removed {result.deleted_count} old blacklisted tokens") # DEBUG
        except PyMongoError as e:
            print(f"[DB ERROR] failed to clean old blacklisted tokens: {e}") # DEBUG