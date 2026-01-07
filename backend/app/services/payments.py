import httpx
import hashlib
import hmac
import base64
import json
from datetime import datetime, timezone
from app.core.config import CASHFREE_APP_ID, CASHFREE_SECRET_KEY, CASHFREE_ENV

def get_cashfree_base_url():
    if CASHFREE_ENV == 'production':
        return "https://api.cashfree.com/pg"
    return "https://sandbox.cashfree.com/pg"

async def create_cashfree_order(order_id: str, amount: float, customer_id: str, customer_email: str, customer_phone: str = "9999999999"):
    """Create a Cashfree payment order"""
    if not CASHFREE_APP_ID or not CASHFREE_SECRET_KEY:
        return {"demo_mode": True, "message": "Cashfree not configured. Demo mode active."}
    
    base_url = get_cashfree_base_url()
    headers = {
        "Content-Type": "application/json",
        "x-client-id": CASHFREE_APP_ID,
        "x-client-secret": CASHFREE_SECRET_KEY,
        "x-api-version": "2023-08-01"
    }
    
    payload = {
        "order_id": order_id,
        "order_amount": amount,
        "order_currency": "INR",
        "customer_details": {
            "customer_id": customer_id,
            "customer_email": customer_email,
            "customer_phone": customer_phone
        }
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{base_url}/orders", json=payload, headers=headers)
        return response.json()

async def verify_cashfree_payment(order_id: str):
    """Verify Cashfree payment status"""
    if not CASHFREE_APP_ID or not CASHFREE_SECRET_KEY:
        return {"order_status": "PAID", "demo_mode": True}
    
    base_url = get_cashfree_base_url()
    headers = {
        "x-client-id": CASHFREE_APP_ID,
        "x-client-secret": CASHFREE_SECRET_KEY,
        "x-api-version": "2023-08-01"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{base_url}/orders/{order_id}", headers=headers)
        return response.json()
