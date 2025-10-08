from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from pymongo import MongoClient
from twilio.rest import Client
from datetime import datetime
import os, json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# === MongoDB Connection ===
client = MongoClient(os.getenv("MONGO_URI"))
db = client["MySpares_db"]
users_col = db["users"]
otp_pending_col = db["otp_pending"]

# === Twilio Setup ===
twilio_client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
verify_sid = os.getenv("TWILIO_VERIFY_SID")

# ===============================
# 🔹 SEND OTP FOR REGISTRATION
# ===============================
@csrf_exempt
def register_send_otp(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            phone = data.get("phone")
            name = data.get("name")

            if not phone or not name:
                return JsonResponse({"error": "Name and phone are required"}, status=400)

            # Check if user already exists
            if users_col.find_one({"phone": phone}):
                return JsonResponse({"message": "User already registered"}, status=400)

            # Send OTP via Twilio
            verification = twilio_client.verify.v2.services(verify_sid).verifications.create(
                to=phone, channel="sms"
            )

            # Store temporary registration data
            otp_pending_col.update_one(
                {"phone": phone},
                {"$set": {"name": name, "phone": phone, "requested_at": datetime.utcnow()}},
                upsert=True
            )

            return JsonResponse({"message": f"OTP sent to {phone}", "status": verification.status})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Invalid request method"}, status=405)


# ===============================
# 🔹 VERIFY OTP & COMPLETE REGISTRATION
# ===============================
@csrf_exempt
def register_verify_otp(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            phone = data.get("phone")
            otp = data.get("otp")

            if not phone or not otp:
                return JsonResponse({"error": "Phone and OTP are required"}, status=400)

            # Verify OTP with Twilio
            verification_check = twilio_client.verify.v2.services(verify_sid).verification_checks.create(
                to=phone, code=otp
            )

            if verification_check.status != "approved":
                return JsonResponse({"message": "Invalid OTP"}, status=400)

            pending = otp_pending_col.find_one({"phone": phone})
            if not pending:
                return JsonResponse({"error": "No registration pending for this number"}, status=400)

            users_col.insert_one({
                "name": pending["name"],
                "phone": phone,
                "created_at": datetime.utcnow()
            })

            otp_pending_col.delete_one({"phone": phone})

            return JsonResponse({
                "message": "Registration successful",
                "name": pending["name"],
                "phone": phone
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Invalid request method"}, status=405)


# ===============================
# 🔹 SEND OTP FOR LOGIN
# ===============================
@csrf_exempt
def login_send_otp(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            phone = data.get("phone")

            if not phone:
                return JsonResponse({"error": "Phone is required"}, status=400)

            user = users_col.find_one({"phone": phone})
            if not user:
                return JsonResponse({"message": "User not registered"}, status=400)

            verification = twilio_client.verify.v2.services(verify_sid).verifications.create(
                to=phone, channel="sms"
            )

            return JsonResponse({"message": f"OTP sent to {phone}", "status": verification.status})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Invalid request method"}, status=405)


# ===============================
# 🔹 VERIFY LOGIN OTP
# ===============================
@csrf_exempt
def login_verify_otp(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            phone = data.get("phone")
            otp = data.get("otp")

            if not phone or not otp:
                return JsonResponse({"error": "Phone and OTP are required"}, status=400)

            verification_check = twilio_client.verify.v2.services(verify_sid).verification_checks.create(
                to=phone, code=otp
            )

            if verification_check.status != "approved":
                return JsonResponse({"message": "Invalid OTP"}, status=400)

            user = users_col.find_one({"phone": phone})
            if not user:
                return JsonResponse({"error": "User not found"}, status=404)

            return JsonResponse({
                "message": "Login successful",
                "user": {
                    "name": user["name"],
                    "phone": user["phone"],
                    "created_at": user["created_at"]
                }
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Invalid request method"}, status=405)


# ===============================
# 🔹 GET USER PROFILE
# ===============================
def get_user_profile(request, phone):
    try:
        user = users_col.find_one({"phone": phone})
        if not user:
            return JsonResponse({"error": "User not found"}, status=404)

        return JsonResponse({
            "name": user["name"],
            "phone": user["phone"],
            "created_at": user["created_at"]
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
