# Daraja (M-Pesa) payment API integration

import requests
import os
import base64
from datetime import datetime

DARAJA_CONSUMER_KEY = os.getenv("DARAJA_CONSUMER_KEY")
DARAJA_CONSUMER_SECRET = os.getenv("DARAJA_CONSUMER_SECRET")
DARAJA_PASSKEY = os.getenv("DARAJA_PASSKEY")
DARAJA_SHORTCODE = os.getenv("DARAJA_SHORTCODE", "174379")  # Default test shortcode
DARAJA_CALLBACK_URL = os.getenv("DARAJA_CALLBACK_URL", "https://yourdomain.com/api/daraja/callback")
DARAJA_BASE_URL = os.getenv("DARAJA_BASE_URL", "https://sandbox.safaricom.co.ke")


def get_access_token():
    url = f"{DARAJA_BASE_URL}/oauth/v1/generate?grant_type=client_credentials"
    resp = requests.get(url, auth=(DARAJA_CONSUMER_KEY, DARAJA_CONSUMER_SECRET))
    resp.raise_for_status()
    return resp.json()["access_token"]


def initiate_stk_push(phone_number: str, amount: int):
    access_token = get_access_token()
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    password = base64.b64encode(f"{DARAJA_SHORTCODE}{DARAJA_PASSKEY}{timestamp}".encode()).decode()
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "BusinessShortCode": DARAJA_SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone_number,
        "PartyB": DARAJA_SHORTCODE,
        "PhoneNumber": phone_number,
        "CallBackURL": DARAJA_CALLBACK_URL,
        "AccountReference": phone_number,
        "TransactionDesc": "Consultation Payment"
    }
    url = f"{DARAJA_BASE_URL}/mpesa/stkpush/v1/processrequest"
    resp = requests.post(url, json=payload, headers=headers)
    if resp.status_code == 200:
        return resp.json()
    else:
        return {"status": "error", "message": resp.text}
