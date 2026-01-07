"""
Razorpay Integration Service
Nirman AI - Indian Payment Gateway Integration

Features:
- Payment orders
- Payment verification
- Subscriptions
- Refunds
- Payouts
- Virtual accounts
- QR codes
- Payment links
"""

import httpx
import os
import json
import hmac
import hashlib
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import uuid
import base64

from app.db.mongo import db

# Razorpay Configuration
RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET", "")
RAZORPAY_WEBHOOK_SECRET = os.environ.get("RAZORPAY_WEBHOOK_SECRET", "")
RAZORPAY_API_URL = "https://api.razorpay.com/v1"


async def save_razorpay_integration(
    user_id: str,
    key_id: str,
    key_secret: str,
    merchant_id: Optional[str] = None
) -> Dict:
    """Save Razorpay integration to database"""
    now = datetime.now(timezone.utc).isoformat()
    
    integration = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "integration_type": "razorpay",
        "status": "connected",
        "key_id": key_id,
        "key_secret": key_secret,  # Encrypt in production!
        "merchant_id": merchant_id,
        "scopes": ["payments", "subscriptions", "refunds", "payouts"],
        "connected_at": now,
        "created_at": now,
        "updated_at": now,
    }
    
    await db.user_integrations.update_one(
        {"user_id": user_id, "integration_type": "razorpay"},
        {"$set": integration},
        upsert=True
    )
    
    return integration


async def get_razorpay_integration(user_id: str) -> Optional[Dict]:
    """Get user's Razorpay integration"""
    return await db.user_integrations.find_one(
        {"user_id": user_id, "integration_type": "razorpay"},
        {"_id": 0}
    )


async def disconnect_razorpay(user_id: str) -> bool:
    """Disconnect Razorpay integration"""
    result = await db.user_integrations.delete_one(
        {"user_id": user_id, "integration_type": "razorpay"}
    )
    return result.deleted_count > 0


class RazorpayService:
    """
    Razorpay Payment Gateway Service
    
    Handles:
    - Payment orders and capture
    - Subscriptions and plans
    - Refunds
    - Payouts
    - Virtual accounts
    - Payment links
    - QR codes
    """
    
    CURRENCIES = ["INR", "USD", "EUR", "GBP", "SGD", "AED", "AUD", "CAD", "HKD", "JPY", "MYR"]
    
    PAYMENT_METHODS = [
        "card", "netbanking", "wallet", "emi", "upi", "bank_transfer",
        "cardless_emi", "paylater", "cod"
    ]
    
    def __init__(self, key_id: str, key_secret: str):
        self.key_id = key_id
        self.key_secret = key_secret
        self.base_url = RAZORPAY_API_URL
        
        # Basic auth credentials
        credentials = f"{key_id}:{key_secret}"
        self.auth_header = base64.b64encode(credentials.encode()).decode()
        self.headers = {
            "Authorization": f"Basic {self.auth_header}",
            "Content-Type": "application/json"
        }
    
    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make authenticated request to Razorpay API"""
        url = f"{self.base_url}{endpoint}"
        
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method, url, headers=self.headers, timeout=30.0, **kwargs
            )
            response.raise_for_status()
            return response.json() if response.text else {}
    
    # =========================================================================
    # ORDER OPERATIONS
    # =========================================================================
    
    async def create_order(
        self,
        amount: int,
        currency: str = "INR",
        receipt: str = None,
        notes: Dict = None,
        partial_payment: bool = False
    ) -> Dict[str, Any]:
        """
        Create a payment order
        
        Args:
            amount: Amount in smallest currency unit (paise for INR)
            currency: Currency code
            receipt: Unique receipt ID
            notes: Additional notes (max 15 key-value pairs)
            partial_payment: Allow partial payments
        """
        data = {
            "amount": amount,
            "currency": currency,
            "receipt": receipt or f"rcpt_{uuid.uuid4().hex[:12]}",
            "partial_payment": partial_payment
        }
        
        if notes:
            data["notes"] = notes
        
        return await self._request("POST", "/orders", json=data)
    
    async def get_order(self, order_id: str) -> Dict[str, Any]:
        """Get order details"""
        return await self._request("GET", f"/orders/{order_id}")
    
    async def list_orders(
        self,
        count: int = 10,
        skip: int = 0,
        from_date: int = None,
        to_date: int = None
    ) -> Dict[str, Any]:
        """List orders"""
        params = {"count": count, "skip": skip}
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date
        
        return await self._request("GET", "/orders", params=params)
    
    async def get_order_payments(self, order_id: str) -> Dict[str, Any]:
        """Get payments for an order"""
        return await self._request("GET", f"/orders/{order_id}/payments")
    
    # =========================================================================
    # PAYMENT OPERATIONS
    # =========================================================================
    
    async def get_payment(self, payment_id: str) -> Dict[str, Any]:
        """Get payment details"""
        return await self._request("GET", f"/payments/{payment_id}")
    
    async def capture_payment(
        self,
        payment_id: str,
        amount: int,
        currency: str = "INR"
    ) -> Dict[str, Any]:
        """Capture an authorized payment"""
        return await self._request(
            "POST",
            f"/payments/{payment_id}/capture",
            json={"amount": amount, "currency": currency}
        )
    
    async def list_payments(
        self,
        count: int = 10,
        skip: int = 0,
        from_date: int = None,
        to_date: int = None
    ) -> Dict[str, Any]:
        """List payments"""
        params = {"count": count, "skip": skip}
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date
        
        return await self._request("GET", "/payments", params=params)
    
    def verify_payment_signature(
        self,
        order_id: str,
        payment_id: str,
        signature: str
    ) -> bool:
        """Verify payment signature from checkout"""
        message = f"{order_id}|{payment_id}"
        expected = hmac.new(
            self.key_secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, signature)
    
    # =========================================================================
    # REFUND OPERATIONS
    # =========================================================================
    
    async def create_refund(
        self,
        payment_id: str,
        amount: int = None,
        speed: str = "normal",
        notes: Dict = None,
        receipt: str = None
    ) -> Dict[str, Any]:
        """
        Create a refund
        
        Args:
            payment_id: Payment to refund
            amount: Refund amount (full refund if not specified)
            speed: "normal" (5-7 days) or "optimum" (instant if eligible)
            notes: Additional notes
            receipt: Unique receipt ID
        """
        data = {"speed": speed}
        
        if amount:
            data["amount"] = amount
        if notes:
            data["notes"] = notes
        if receipt:
            data["receipt"] = receipt
        
        return await self._request("POST", f"/payments/{payment_id}/refund", json=data)
    
    async def get_refund(self, payment_id: str, refund_id: str) -> Dict[str, Any]:
        """Get refund details"""
        return await self._request("GET", f"/payments/{payment_id}/refunds/{refund_id}")
    
    async def list_refunds(self, payment_id: str = None) -> Dict[str, Any]:
        """List refunds"""
        if payment_id:
            return await self._request("GET", f"/payments/{payment_id}/refunds")
        return await self._request("GET", "/refunds")
    
    # =========================================================================
    # SUBSCRIPTION OPERATIONS
    # =========================================================================
    
    async def create_plan(
        self,
        period: str,
        interval: int,
        name: str,
        amount: int,
        currency: str = "INR",
        description: str = None,
        notes: Dict = None
    ) -> Dict[str, Any]:
        """
        Create a subscription plan
        
        Args:
            period: "daily", "weekly", "monthly", "yearly"
            interval: Billing frequency (1 = every period, 2 = every 2 periods)
            name: Plan name
            amount: Amount per billing cycle (in paise)
            currency: Currency code
            description: Plan description
            notes: Additional notes
        """
        data = {
            "period": period,
            "interval": interval,
            "item": {
                "name": name,
                "amount": amount,
                "currency": currency,
            }
        }
        
        if description:
            data["item"]["description"] = description
        if notes:
            data["notes"] = notes
        
        return await self._request("POST", "/plans", json=data)
    
    async def get_plan(self, plan_id: str) -> Dict[str, Any]:
        """Get plan details"""
        return await self._request("GET", f"/plans/{plan_id}")
    
    async def list_plans(self, count: int = 10, skip: int = 0) -> Dict[str, Any]:
        """List plans"""
        return await self._request("GET", "/plans", params={"count": count, "skip": skip})
    
    async def create_subscription(
        self,
        plan_id: str,
        customer_notify: int = 1,
        total_count: int = None,
        quantity: int = 1,
        start_at: int = None,
        notes: Dict = None,
        offer_id: str = None
    ) -> Dict[str, Any]:
        """
        Create a subscription
        
        Args:
            plan_id: Plan ID
            customer_notify: 1 to notify customer, 0 otherwise
            total_count: Total billing cycles (None for indefinite)
            quantity: Number of subscriptions
            start_at: Unix timestamp for start
            notes: Additional notes
            offer_id: Offer ID for discount
        """
        data = {
            "plan_id": plan_id,
            "customer_notify": customer_notify,
            "quantity": quantity
        }
        
        if total_count:
            data["total_count"] = total_count
        if start_at:
            data["start_at"] = start_at
        if notes:
            data["notes"] = notes
        if offer_id:
            data["offer_id"] = offer_id
        
        return await self._request("POST", "/subscriptions", json=data)
    
    async def get_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Get subscription details"""
        return await self._request("GET", f"/subscriptions/{subscription_id}")
    
    async def cancel_subscription(
        self,
        subscription_id: str,
        cancel_at_cycle_end: bool = False
    ) -> Dict[str, Any]:
        """Cancel a subscription"""
        return await self._request(
            "POST",
            f"/subscriptions/{subscription_id}/cancel",
            json={"cancel_at_cycle_end": 1 if cancel_at_cycle_end else 0}
        )
    
    async def pause_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Pause a subscription"""
        return await self._request("POST", f"/subscriptions/{subscription_id}/pause")
    
    async def resume_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Resume a paused subscription"""
        return await self._request("POST", f"/subscriptions/{subscription_id}/resume")
    
    # =========================================================================
    # CUSTOMER OPERATIONS
    # =========================================================================
    
    async def create_customer(
        self,
        name: str,
        email: str = None,
        contact: str = None,
        notes: Dict = None,
        fail_existing: int = 0
    ) -> Dict[str, Any]:
        """Create a customer"""
        data = {"name": name, "fail_existing": fail_existing}
        
        if email:
            data["email"] = email
        if contact:
            data["contact"] = contact
        if notes:
            data["notes"] = notes
        
        return await self._request("POST", "/customers", json=data)
    
    async def get_customer(self, customer_id: str) -> Dict[str, Any]:
        """Get customer details"""
        return await self._request("GET", f"/customers/{customer_id}")
    
    async def list_customers(self, count: int = 10, skip: int = 0) -> Dict[str, Any]:
        """List customers"""
        return await self._request("GET", "/customers", params={"count": count, "skip": skip})
    
    # =========================================================================
    # PAYMENT LINK OPERATIONS
    # =========================================================================
    
    async def create_payment_link(
        self,
        amount: int,
        currency: str = "INR",
        description: str = "",
        customer: Dict = None,
        notify: Dict = None,
        callback_url: str = None,
        callback_method: str = "get",
        expire_by: int = None,
        reference_id: str = None,
        notes: Dict = None
    ) -> Dict[str, Any]:
        """
        Create a payment link
        
        Args:
            amount: Amount in paise
            currency: Currency code
            description: Payment description
            customer: {"name": "", "email": "", "contact": ""}
            notify: {"sms": True, "email": True}
            callback_url: Redirect URL after payment
            callback_method: "get" or "post"
            expire_by: Unix timestamp for expiry
            reference_id: Your reference ID
            notes: Additional notes
        """
        data = {
            "amount": amount,
            "currency": currency,
            "description": description
        }
        
        if customer:
            data["customer"] = customer
        if notify:
            data["notify"] = notify
        if callback_url:
            data["callback_url"] = callback_url
            data["callback_method"] = callback_method
        if expire_by:
            data["expire_by"] = expire_by
        if reference_id:
            data["reference_id"] = reference_id
        if notes:
            data["notes"] = notes
        
        return await self._request("POST", "/payment_links", json=data)
    
    async def get_payment_link(self, link_id: str) -> Dict[str, Any]:
        """Get payment link details"""
        return await self._request("GET", f"/payment_links/{link_id}")
    
    async def cancel_payment_link(self, link_id: str) -> Dict[str, Any]:
        """Cancel a payment link"""
        return await self._request("POST", f"/payment_links/{link_id}/cancel")
    
    # =========================================================================
    # QR CODE OPERATIONS
    # =========================================================================
    
    async def create_qr_code(
        self,
        qr_type: str = "upi_qr",
        name: str = "",
        usage: str = "single_use",
        fixed_amount: bool = True,
        payment_amount: int = None,
        description: str = None,
        customer_id: str = None,
        close_by: int = None,
        notes: Dict = None
    ) -> Dict[str, Any]:
        """
        Create a QR code for payments
        
        Args:
            qr_type: "upi_qr" or "bharat_qr"
            name: QR code name
            usage: "single_use" or "multiple_use"
            fixed_amount: True for fixed, False for dynamic
            payment_amount: Amount in paise (required if fixed_amount)
            description: Description
            customer_id: Customer ID
            close_by: Unix timestamp for expiry
            notes: Additional notes
        """
        data = {
            "type": qr_type,
            "name": name,
            "usage": usage,
            "fixed_amount": fixed_amount
        }
        
        if fixed_amount and payment_amount:
            data["payment_amount"] = payment_amount
        if description:
            data["description"] = description
        if customer_id:
            data["customer_id"] = customer_id
        if close_by:
            data["close_by"] = close_by
        if notes:
            data["notes"] = notes
        
        return await self._request("POST", "/payments/qr_codes", json=data)
    
    async def get_qr_code(self, qr_id: str) -> Dict[str, Any]:
        """Get QR code details"""
        return await self._request("GET", f"/payments/qr_codes/{qr_id}")
    
    async def close_qr_code(self, qr_id: str) -> Dict[str, Any]:
        """Close a QR code"""
        return await self._request("POST", f"/payments/qr_codes/{qr_id}/close")
    
    # =========================================================================
    # PAYOUT OPERATIONS
    # =========================================================================
    
    async def create_payout(
        self,
        account_number: str,
        fund_account_id: str,
        amount: int,
        currency: str = "INR",
        mode: str = "IMPS",
        purpose: str = "refund",
        reference_id: str = None,
        narration: str = None,
        notes: Dict = None
    ) -> Dict[str, Any]:
        """
        Create a payout
        
        Args:
            account_number: Your Razorpay account number
            fund_account_id: Recipient's fund account ID
            amount: Amount in paise
            currency: Currency code
            mode: "NEFT", "RTGS", "IMPS", "UPI"
            purpose: "refund", "cashback", "payout", "salary", "utility bill", "vendor bill"
            reference_id: Your reference ID
            narration: Transaction narration
            notes: Additional notes
        """
        data = {
            "account_number": account_number,
            "fund_account_id": fund_account_id,
            "amount": amount,
            "currency": currency,
            "mode": mode,
            "purpose": purpose
        }
        
        if reference_id:
            data["reference_id"] = reference_id
        if narration:
            data["narration"] = narration
        if notes:
            data["notes"] = notes
        
        return await self._request("POST", "/payouts", json=data)
    
    async def get_payout(self, payout_id: str) -> Dict[str, Any]:
        """Get payout details"""
        return await self._request("GET", f"/payouts/{payout_id}")
    
    # =========================================================================
    # WEBHOOK VERIFICATION
    # =========================================================================
    
    def verify_webhook_signature(
        self,
        body: str,
        signature: str,
        secret: str = None
    ) -> bool:
        """Verify webhook signature"""
        webhook_secret = secret or RAZORPAY_WEBHOOK_SECRET
        expected = hmac.new(
            webhook_secret.encode(),
            body.encode(),
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, signature)
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def get_checkout_code(self, order_id: str, amount: int, name: str, description: str) -> str:
        """Generate Razorpay checkout integration code"""
        return f'''
<script src="https://checkout.razorpay.com/v1/checkout.js"></script>
<script>
var options = {{
    "key": "{self.key_id}",
    "amount": "{amount}",
    "currency": "INR",
    "name": "{name}",
    "description": "{description}",
    "order_id": "{order_id}",
    "handler": function (response) {{
        // Send to your server for verification
        fetch('/api/payment/verify', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{
                razorpay_order_id: response.razorpay_order_id,
                razorpay_payment_id: response.razorpay_payment_id,
                razorpay_signature: response.razorpay_signature
            }})
        }});
    }},
    "prefill": {{
        "name": "",
        "email": "",
        "contact": ""
    }},
    "theme": {{
        "color": "#6366f1"
    }}
}};
var rzp = new Razorpay(options);
rzp.open();
</script>
'''


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

async def get_razorpay_service(user_id: str) -> Optional[RazorpayService]:
    """Get RazorpayService for user if connected"""
    integration = await get_razorpay_integration(user_id)
    if not integration or integration.get("status") != "connected":
        return None
    
    return RazorpayService(
        integration["key_id"],
        integration["key_secret"]
    )


# Global instance for app-level payments
def get_app_razorpay() -> RazorpayService:
    """Get Razorpay service with app credentials"""
    if not RAZORPAY_KEY_ID or not RAZORPAY_KEY_SECRET:
        raise ValueError("Razorpay not configured")
    return RazorpayService(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET)
