# Daraja (M-Pesa) payment API stub

import requests

def initiate_stk_push(phone_number: str, amount: int):
    # This is a stub for Daraja STK Push integration.
    # In production, implement Safaricom Daraja API call here.
    return {"status": "success", "message": "STK push initiated (stub)", "phone_number": phone_number, "amount": amount}
