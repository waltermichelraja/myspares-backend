from pymongo.errors import PyMongoError
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone, timedelta
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from .admin import *
from .twilio_service import *
from client.models import Cart, Address
import secrets
import hashlib
import re


class Auth:
    def __init__(self, username, phone_number, password_hash, created_at=None, _id=None):
        self.id=_id
        self.username=username
        self.phone_number=str(phone_number)
        self.password_hash=password_hash
        self.created_at=created_at or datetime.now(timezone.utc)

    @staticmethod
    def validate_password(password: str):
        if not re.match(r"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[\W_]).{4,16}$", str(password)):
            raise ValueError("invalid password: " + (
                "password too long/short" if not re.match(r"^.{4,16}$", str(password))
                else "must include uppercase, lowercase, number, and special character"
            ))

    @staticmethod
    def validate_fields(username, phone_number, password):
        if not re.match(r"^[A-Za-z ]+$", str(username)) or not re.match(r"^.{4,24}$", str(username)):
            raise ValueError("invalid username: " + (
                "username too long/short" if not re.match(r"^.{4,24}$", str(username))
                else "invalid characters"
            ))
        if not re.match(r"^\d{10,15}$", str(phone_number)):
            raise ValueError("invalid phone number: must be 10-15 digits")
        Auth.validate_password(password)

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
                logger.warning(f"[CREATE CART ERROR] failed to auto-create cart for user {user.id}: {cart_err}")
            try:
                Address.create_address(
                    user_id=str(user.id),
                    name=user.username,
                    phone_number=user.phone_number
                )
            except Exception as addr_err:
                logger.warning(f"[CREATE ADDRESS ERROR] failed to auto-create address for user {user.id}: {addr_err}")
            return user
        except PyMongoError as e:
            logger.error(f"[DB ERROR] failed to insert/find user: {e}")
            raise RuntimeError("database error: unable to register user")

    @classmethod
    def create_temp_user(cls, username, phone_number, password):
        cls.validate_fields(username, phone_number, password)
        phone_number=normalize_number(phone_number)
        try:
            if users_collection.find_one({"phone_number": phone_number}):
                raise ValueError("phone number already registered")
            temporary_users_collection.update_one(
                {"phone_number": phone_number},
                {"$set": {
                    "username": str(username),
                    "phone_number": str(phone_number),
                    "password_hash": cls.hash_password(password),
                    "created_at": datetime.now(timezone.utc)
                }},
                upsert=True
            )
        except PyMongoError as e:
            logger.error(f"[DB ERROR] failed to create temporary user: {e}")
            raise RuntimeError(f"failed to save temporary user: {e}")

    @classmethod
    def send_otp_to_user(cls, phone_number):
        try:
            return send_otp(normalize_number(phone_number))
        except Exception as e:
            raise RuntimeError(f"failed to send OTP: {e}")

    @classmethod
    def verify_user_otp(cls, phone_number, code):
        try:
            return verify_otp(normalize_number(phone_number), code)
        except Exception as e:
            raise RuntimeError(f"OTP verification failed: {e}")

    @classmethod
    def promote_temp_user_to_main(cls, phone_number):
        phone_number=normalize_number(phone_number)
        temp_user=temporary_users_collection.find_one({"phone_number": (phone_number)})
        if not temp_user:
            raise ValueError("no pending registration for this number")
        user_doc={
            "username": temp_user["username"],
            "phone_number": temp_user["phone_number"],
            "password_hash": temp_user["password_hash"],
            "created_at": datetime.now(timezone.utc),
        }
        try:
            result=users_collection.insert_one(user_doc)
            user_doc["_id"]=result.inserted_id
            user=cls.from_dict(user_doc)
            try:
                Cart.create_cart(user_id=str(user.id))
            except Exception as cart_err:
                logger.warning(f"[CREATE CART ERROR] failed to auto-create cart for user {user.id}: {cart_err}")
            try:
                Address.create_address(
                    user_id=str(user.id),
                    name=user.username,
                    phone_number=user.phone_number
                )
            except Exception as addr_err:
                logger.warning(f"[CREATE ADDRESS ERROR] failed to auto-create address for user {user.id}: {addr_err}")
            temporary_users_collection.delete_one({"phone_number": (phone_number)})
            return user
        except PyMongoError as e:
            logger.error(f"[DB ERROR] failed to promote temporary user: {e}")
            raise RuntimeError("database error: unable to create verified user")

    @staticmethod
    def _hash_token(token: str)->str:
        return hashlib.sha256(token.encode()).hexdigest()

    @classmethod
    def initiate_password_reset(cls, phone_number: str, otp_channel: str = "sms", validity_minutes: int = 15):
        phone=normalize_number(phone_number)
        user_doc=users_collection.find_one({"phone_number": phone})
        if not user_doc:
            logger.info(f"[RESET PASSWORD] request for non-existent number {phone} (silent)")
            return {"ok": True}
        try:
            now=datetime.now(timezone.utc)
            expires_at=now+timedelta(minutes=validity_minutes)
            password_resets_collection.update_one(
                {"phone_number": phone, "used": {"$ne": True}},
                {"$set": {
                    "phone_number": phone,
                    "user_id": user_doc["_id"],
                    "verified": False,
                    "used": False,
                    "method": "sms",
                    "created_at": now,
                    "expires_at": expires_at
                }},
                upsert=True
            )
        except PyMongoError as e:
            logger.error(f"[DB ERROR] failed to create password reset record: {e}")
            raise RuntimeError("server error: unable to initiate password reset")
        try:
            status=send_otp(phone)
            logger.info(f"[RESET PASSWORD] sent OTP to {phone}, status={status}")
            return {"ok": True, "twilio_status": status}
        except Exception as e:
            logger.error(f"[TWILIO ERROR] failed to send password reset OTP to {phone}: {e}")
            raise RuntimeError("failed to send OTP")

    @classmethod
    def verify_password_reset_otp(cls, phone_number: str, code: str, token_valid_minutes: int = 15):
        phone=normalize_number(phone_number)
        reset_doc=password_resets_collection.find_one({"phone_number": phone, "used": {"$ne": True}})
        if not reset_doc:
            raise ValueError("no pending password reset for this number")
        try:
            ok=verify_otp(phone, code)
        except Exception as e:
            logger.error(f"[TWILIO ERROR] OTP verify failed for {phone}: {e}")
            raise RuntimeError("OTP verification failed")
        if not ok:
            raise ValueError("invalid or expired OTP")
        plaintext_token=secrets.token_urlsafe(32)
        hashed=cls._hash_token(plaintext_token)
        now=datetime.now(timezone.utc)
        expires_at=now+timedelta(minutes=token_valid_minutes)
        try:
            password_resets_collection.update_one(
                {"_id": reset_doc["_id"]},
                {"$set": {
                    "hashed_token": hashed,
                    "token_created_at": now,
                    "expires_at": expires_at,
                    "verified": True,
                    "used": False
                }}
            )
            logger.info(f"[RESET PASSWORD] OTP verified for {phone}, reset token issued")
            return plaintext_token
        except PyMongoError as e:
            logger.error(f"[DB ERROR] failed to store reset token: {e}")
            raise RuntimeError("server error: unable to prepare password reset")

    @classmethod
    def reset_password_with_token(cls, token: str, new_password: str):
        cls.validate_password(new_password)
        hashed=cls._hash_token(token)
        now=datetime.now(timezone.utc)
        try:
            reset_doc=password_resets_collection.find_one({"hashed_token": hashed})
        except PyMongoError as e:
            logger.error(f"[DB ERROR] failed to lookup reset token: {e}")
            raise RuntimeError("server error")
        if not reset_doc:
            raise ValueError("invalid or expired reset token")
        if reset_doc.get("used"):
            raise ValueError("reset token already used")
        expires_at=reset_doc.get("expires_at")
        if expires_at and expires_at.tzinfo is None:
            expires_at=expires_at.replace(tzinfo=timezone.utc)
        if not expires_at or expires_at<now:
            raise ValueError("reset token expired")
        try:
            user_id=reset_doc.get("user_id")
            if not user_id:
                raise RuntimeError("password reset record malformed")
            new_hash=cls.hash_password(new_password)
            result=users_collection.update_one(
                {"_id": user_id},
                {"$set": {"password_hash": new_hash, "updated_at": now}}
            )
            if result.matched_count==0:
                raise RuntimeError("user not found")
            password_resets_collection.update_one(
                {"_id": reset_doc["_id"]},
                {"$set": {"used": True, "used_at": now}}
            )
            logger.info(f"[RESET PASSWORD] password updated for user {user_id}")
            return True
        except PyMongoError as e:
            logger.error(f"[DB ERROR] failed to reset password: {e}")
            raise RuntimeError("server error: unable to reset password")


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
            logger.error(f"[DB ERROR] failed to blacklist tokens: {e}")
            raise RuntimeError("server error: unable to blacklist tokens")

    @staticmethod
    def is_blacklisted_refresh(refresh_token: str) -> bool:
        try:
            return blacklisted_tokens_collection.find_one({"token.refresh": refresh_token}) is not None
        except PyMongoError as e:
            logger.error(f"[DB ERROR] failed to check refresh blacklist: {e}")
            raise RuntimeError("server error: unable to check token blacklist")

    @staticmethod
    def is_blacklisted_access(access_token: str) -> bool:
        try:
            return blacklisted_tokens_collection.find_one({"token.access": access_token}) is not None
        except PyMongoError as e:
            logger.error(f"[DB ERROR] failed to check access blacklist: {e}")
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
