from twilio.rest import Client
from django.conf import settings

client=Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

def send_otp(phone_number: str):
    verification=client.verify.v2.services(settings.TWILIO_VERIFY_SID) \
        .verifications.create(to=f"+{phone_number}", channel="sms")
    return verification.status

def verify_otp(phone_number: str, code: str):
    verification_check=client.verify.v2.services(settings.TWILIO_VERIFY_SID) \
        .verification_checks.create(to=f"+{phone_number}", code=code)
    return verification_check.status=="approved"

def normalize_number(phone):
    phone=str(phone).strip()
    if phone.startswith("0"):
        phone=phone[1:]
    if not phone.startswith("+"):
        phone="+91"+phone
    return phone
