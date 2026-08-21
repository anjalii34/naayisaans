import os
from twilio.rest import Client

_client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
_verify_sid = os.getenv("TWILIO_VERIFY_SID")

def send_otp(phone_number: str):
    return _client.verify.v2.services(_verify_sid).verifications.create(
        to=phone_number, channel="sms"
    )

def check_otp(phone_number: str, code: str) -> bool:
    result = _client.verify.v2.services(_verify_sid).verification_checks.create(
        to=phone_number, code=code
    )
    return result.status == "approved"