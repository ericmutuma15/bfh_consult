import hashlib
import hmac
import os
import random
import string
import jwt
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
import requests as http_requests

SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
ALGORITHM = "HS256"

# Password hashing

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hash_: str) -> bool:
    return hash_password(password) == hash_

# JWT

def create_access_token(data: dict, expires_delta: timedelta = timedelta(hours=1)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        return None

# OTP

def generate_otp(length=6):
    return ''.join(random.choices(string.digits, k=length))

def send_email_otp(email: str, code: str):
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    if not (smtp_host and smtp_user and smtp_pass):
        print(f"[DEV] Email OTP to {email}: {code}")
        return
    msg = MIMEText(f"Your OTP code is: {code}")
    msg["Subject"] = "Your OTP Code"
    msg["From"] = smtp_user
    msg["To"] = email
    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_user, [email], msg.as_string())

def send_sms_otp(phone: str, code: str):
    # Example: Twilio or Africa's Talking
    sms_api_url = os.getenv("SMS_API_URL")
    sms_api_key = os.getenv("SMS_API_KEY")
    if not (sms_api_url and sms_api_key):
        print(f"[DEV] SMS OTP to {phone}: {code}")
        return
    # Example POST (customize for your provider)
    http_requests.post(sms_api_url, json={"to": phone, "message": f"Your OTP code is: {code}", "apiKey": sms_api_key})

def send_otp_stub(destination: str, code: str, type_: str):
    if type_ == "email":
        send_email_otp(destination, code)
    elif type_ == "phone":
        send_sms_otp(destination, code)
    else:
        print(f"[DEV] OTP to {destination}: {code}")
