"""
Cashfree Integration Service
Nirman AI - Indian Payment Gateway Integration

Features:
- Payment orders
- Payment verification
- Subscriptions
- Refunds
- Payouts
- Virtual accounts
- Payment links
- Settlements
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

# Cashfree Configuration
CASHFREE_APP_ID = os.environ.get("CASHFREE_APP_ID", "")
CASHFREE_SECRET_KEY = os.environ.get("CASHFREE_SECRET_KEY", "")
CASHFREE_ENV = os.environ.get("CASHFREE_ENV", "sandbox")  # sandbox or production

# API URLs
CASHFREE_API_URL = (
    "https://sandbox.cashfree.com/pg" if CASHFREE_ENV == "sandbox"
    else "https://api.cashfree.com/pg"
)
CASHFREE_PAYOUT_URL = (
    "https://payout-gamma.cashfree.com/payout/v1" if CASHFREE_ENV == "sandbox"
    else "https://payout-api.cashfree.com/payout/v1"
)


async def save_cashfree_integration(
    user_id: str,
    app_id: str,
    secret_key: str,
    merchant_id: Optional[str] = None
) -> Dict:
    """Save Cashfree integration to database"""
    now = datetime.now(timezone.utc).isoformat()
    
    integration = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "integration_type": "cashfree",
        "status": "connected",
        "app_id": app_id,
        "secret_key": secret_key,  # Encrypt in production!
        "merchant_id": merchant_id,
        "scopes": ["payments", "subscriptions", "refunds", "payouts"],
        "connected_at": now,
        "created_at": now,
        "updated_at": now,
    }
    
    await db.user_integrations.update_one(
        {"user_id": user_id, "integration_type": "cashfree"},
        {"$set": integration},
        upsert=True
    )
    
    return integration


async def get_cashfree_integration(user_id: str) -> Optional[Dict]:
    """Get user's Cashfree integration"""
    return await db.user_integrations.find_one(
        {"user_id": user_id, "integration_type": "cashfree"},
        {"_id": 0}
    )


async def disconnect_cashfree(user_id: str) -> bool:
    """Disconnect Cashfree integration"""
    result = await db.user_integrations.delete_one(
        {"user_id": user_id, "integration_type": "cashfree"}
    )
    return result.deleted_count > 0


class CashfreeService:
    """
    Cashfree Payment Gateway Service
    
    Handles:
    - Payment orders and capture
    - Subscriptions and plans
    - Refunds
    - Payouts
    - Virtual accounts
    - Payment links
    - UPI autopay
    """
    
    CURRENCIES = ["INR"]
    
    PAYMENT_METHODS = [
        "cc", "dc", "nb", "upi", "wallet", "emi", "paylater", "cardlessemi"
    ]
    
    def __init__(self, app_id: str, secret_key: str, env: str = "sandbox"):
        self.app_id = app_id
        self.secret_key = secret_key
        self.env = env
        self.base_url = (
            "https://sandbox.cashfree.com/pg" if env == "sandbox"
            else "https://api.cashfree.com/pg"
        )
        self.headers = {
            "x-client-id": app_id,
            "x-client-secret": secret_key,
            "x-api-version": "2023-08-01",
            "Content-Type": "application/json"
        }
    
    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make authenticated request to Cashfree API"""
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
        order_id: str,
        order_amount: float,
        order_currency: str = "INR",
        customer_details: Dict = None,
        order_meta: Dict = None,
        order_expiry_time: str = None,
        order_note: str = None,
        order_tags: Dict = None
    ) -> Dict[str, Any]:
        """
        Create a payment order
        
        Args:
            order_id: Unique order ID
            order_amount: Amount (INR, up to 2 decimal places)
            order_currency: Currency code
            customer_details: {"customer_id": "", "customer_email": "", "customer_phone": ""}
            order_meta: {"return_url": "", "notify_url": "", "payment_methods": ""}
            order_expiry_time: ISO timestamp for expiry
            order_note: Additional note
            order_tags: Key-value tags
        """
        data = {
            "order_id": order_id,
            "order_amount": order_amount,
            "order_currency": order_currency,
        }
        
        if customer_details:
            data["customer_details"] = customer_details
        else:
            data["customer_details"] = {
                "customer_id": f"cust_{uuid.uuid4().hex[:12]}",
                "customer_phone": "9999999999"
            }
        
        if order_meta:
            data["order_meta"] = order_meta
        if order_expiry_time:
            data["order_expiry_time"] = order_expiry_time
        if order_note:
            data["order_note"] = order_note
        if order_tags:
            data["order_tags"] = order_tags
        
        return await self._request("POST", "/orders", json=data)
    
    async def get_order(self, order_id: str) -> Dict[str, Any]:
        """Get order details"""
        return await self._request("GET", f"/orders/{order_id}")
    
    async def get_order_payments(self, order_id: str) -> Dict[str, Any]:
        """Get payments for an order"""
        return await self._request("GET", f"/orders/{order_id}/payments")
    
    # =========================================================================
    # PAYMENT OPERATIONS
    # =========================================================================
    
    async def get_payment(self, order_id: str, cf_payment_id: str) -> Dict[str, Any]:
        """Get payment details"""
        return await self._request("GET", f"/orders/{order_id}/payments/{cf_payment_id}")
    
    async def pay_order(
        self,
        order_id: str,
        payment_session_id: str,
        payment_method: Dict
    ) -> Dict[str, Any]:
        """
        Process payment for an order
        
        payment_method examples:
        - UPI: {"upi": {"channel": "collect", "upi_id": "test@upi"}}
        - Card: {"card": {"channel": "link", "card_number": "", "card_expiry_mm": "", ...}}
        - NetBanking: {"netbanking": {"channel": "link", "netbanking_bank_code": 3003}}
        """
        data = {
            "payment_session_id": payment_session_id,
            "payment_method": payment_method
        }
        
        return await self._request("POST", f"/orders/{order_id}/pay", json=data)
    
    async def preauthorize(
        self,
        order_id: str,
        payment_session_id: str,
        payment_method: Dict
    ) -> Dict[str, Any]:
        """Preauthorize a payment (for later capture)"""
        data = {
            "payment_session_id": payment_session_id,
            "payment_method": payment_method,
            "authorization": {"authorize_only": True}
        }
        
        return await self._request("POST", f"/orders/{order_id}/pay", json=data)
    
    async def capture_payment(
        self,
        order_id: str,
        cf_payment_id: str,
        amount: float
    ) -> Dict[str, Any]:
        """Capture a preauthorized payment"""
        return await self._request(
            "POST",
            f"/orders/{order_id}/authorization/{cf_payment_id}/capture",
            json={"action": "CAPTURE", "amount": amount}
        )
    
    # =========================================================================
    # REFUND OPERATIONS
    # =========================================================================
    
    async def create_refund(
        self,
        order_id: str,
        refund_amount: float,
        refund_id: str = None,
        refund_note: str = None,
        refund_speed: str = "STANDARD"
    ) -> Dict[str, Any]:
        """
        Create a refund
        
        Args:
            order_id: Order ID
            refund_amount: Amount to refund
            refund_id: Unique refund ID
            refund_note: Note for refund
            refund_speed: "STANDARD" or "INSTANT"
        """
        data = {
            "refund_amount": refund_amount,
            "refund_id": refund_id or f"refund_{uuid.uuid4().hex[:12]}",
            "refund_speed": refund_speed
        }
        
        if refund_note:
            data["refund_note"] = refund_note
        
        return await self._request("POST", f"/orders/{order_id}/refunds", json=data)
    
    async def get_refund(self, order_id: str, refund_id: str) -> Dict[str, Any]:
        """Get refund details"""
        return await self._request("GET", f"/orders/{order_id}/refunds/{refund_id}")
    
    async def list_refunds(self, order_id: str) -> Dict[str, Any]:
        """List refunds for an order"""
        return await self._request("GET", f"/orders/{order_id}/refunds")
    
    # =========================================================================
    # PAYMENT LINK OPERATIONS
    # =========================================================================
    
    async def create_payment_link(
        self,
        link_id: str,
        link_amount: float,
        link_currency: str = "INR",
        link_purpose: str = "Payment",
        customer_details: Dict = None,
        link_partial_payments: bool = False,
        link_minimum_partial_amount: float = None,
        link_expiry_time: str = None,
        link_notify: Dict = None,
        link_meta: Dict = None,
        link_notes: Dict = None
    ) -> Dict[str, Any]:
        """
        Create a payment link
        
        Args:
            link_id: Unique link ID
            link_amount: Payment amount
            link_currency: Currency
            link_purpose: Purpose description
            customer_details: {"customer_phone": ""}
            link_partial_payments: Allow partial payments
            link_minimum_partial_amount: Minimum amount if partial
            link_expiry_time: ISO timestamp
            link_notify: {"send_sms": true, "send_email": true}
            link_meta: {"notify_url": "", "return_url": ""}
            link_notes: Key-value notes
        """
        data = {
            "link_id": link_id,
            "link_amount": link_amount,
            "link_currency": link_currency,
            "link_purpose": link_purpose,
            "link_partial_payments": link_partial_payments,
        }
        
        if customer_details:
            data["customer_details"] = customer_details
        else:
            data["customer_details"] = {"customer_phone": "9999999999"}
        
        if link_minimum_partial_amount:
            data["link_minimum_partial_amount"] = link_minimum_partial_amount
        if link_expiry_time:
            data["link_expiry_time"] = link_expiry_time
        if link_notify:
            data["link_notify"] = link_notify
        if link_meta:
            data["link_meta"] = link_meta
        if link_notes:
            data["link_notes"] = link_notes
        
        return await self._request("POST", "/links", json=data)
    
    async def get_payment_link(self, link_id: str) -> Dict[str, Any]:
        """Get payment link details"""
        return await self._request("GET", f"/links/{link_id}")
    
    async def cancel_payment_link(self, link_id: str) -> Dict[str, Any]:
        """Cancel a payment link"""
        return await self._request("POST", f"/links/{link_id}/cancel")
    
    # =========================================================================
    # SUBSCRIPTION OPERATIONS
    # =========================================================================
    
    async def create_subscription_plan(
        self,
        plan_id: str,
        plan_name: str,
        plan_type: str,  # "PERIODIC" or "ON_DEMAND"
        plan_recurring_amount: float,
        plan_max_amount: float = None,
        plan_intervals: int = 1,
        plan_interval_type: str = "MONTH",  # DAY, WEEK, MONTH, YEAR
        plan_currency: str = "INR",
        plan_note: str = None
    ) -> Dict[str, Any]:
        """
        Create a subscription plan
        
        Args:
            plan_id: Unique plan ID
            plan_name: Plan name
            plan_type: "PERIODIC" or "ON_DEMAND"
            plan_recurring_amount: Amount per cycle
            plan_max_amount: Max debit amount
            plan_intervals: Billing interval
            plan_interval_type: "DAY", "WEEK", "MONTH", "YEAR"
            plan_currency: Currency
            plan_note: Note
        """
        data = {
            "plan_id": plan_id,
            "plan_name": plan_name,
            "plan_type": plan_type,
            "plan_recurring_amount": plan_recurring_amount,
            "plan_intervals": plan_intervals,
            "plan_interval_type": plan_interval_type,
            "plan_currency": plan_currency,
        }
        
        if plan_max_amount:
            data["plan_max_amount"] = plan_max_amount
        if plan_note:
            data["plan_note"] = plan_note
        
        return await self._request("POST", "/subscriptions/plans", json=data)
    
    async def get_subscription_plan(self, plan_id: str) -> Dict[str, Any]:
        """Get subscription plan details"""
        return await self._request("GET", f"/subscriptions/plans/{plan_id}")
    
    async def create_subscription(
        self,
        subscription_id: str,
        plan_id: str,
        customer_details: Dict,
        authorization_details: Dict = None,
        first_charge_date: str = None,
        expires_on: str = None,
        subscription_note: str = None
    ) -> Dict[str, Any]:
        """
        Create a subscription
        
        Args:
            subscription_id: Unique subscription ID
            plan_id: Plan ID
            customer_details: {"customer_phone": "", "customer_email": "", "customer_name": ""}
            authorization_details: {"authorization_amount": 1, "authorization_amount_refund": true}
            first_charge_date: ISO date for first charge
            expires_on: ISO date for expiry
            subscription_note: Note
        """
        data = {
            "subscription_id": subscription_id,
            "plan_id": plan_id,
            "customer_details": customer_details,
        }
        
        if authorization_details:
            data["authorization_details"] = authorization_details
        if first_charge_date:
            data["first_charge_date"] = first_charge_date
        if expires_on:
            data["expires_on"] = expires_on
        if subscription_note:
            data["subscription_note"] = subscription_note
        
        return await self._request("POST", "/subscriptions", json=data)
    
    async def get_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Get subscription details"""
        return await self._request("GET", f"/subscriptions/{subscription_id}")
    
    async def cancel_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Cancel a subscription"""
        return await self._request("POST", f"/subscriptions/{subscription_id}/cancel")
    
    async def pause_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Pause a subscription"""
        return await self._request("POST", f"/subscriptions/{subscription_id}/pause")
    
    async def resume_subscription(
        self,
        subscription_id: str,
        resume_date: str = None
    ) -> Dict[str, Any]:
        """Resume a paused subscription"""
        data = {}
        if resume_date:
            data["resume_date"] = resume_date
        
        return await self._request(
            "POST",
            f"/subscriptions/{subscription_id}/resume",
            json=data
        )
    
    # =========================================================================
    # SETTLEMENT OPERATIONS
    # =========================================================================
    
    async def get_settlements(
        self,
        start_date: str = None,
        end_date: str = None,
        limit: int = 10,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get settlements"""
        params = {"limit": limit, "offset": offset}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        
        return await self._request("GET", "/settlements", params=params)
    
    async def get_settlement(self, settlement_id: str) -> Dict[str, Any]:
        """Get settlement details"""
        return await self._request("GET", f"/settlements/{settlement_id}")
    
    async def get_settlement_recon(self, settlement_id: str) -> Dict[str, Any]:
        """Get settlement reconciliation"""
        return await self._request("GET", f"/settlements/{settlement_id}/recon")
    
    # =========================================================================
    # PAYOUT OPERATIONS (RazorpayX equivalent)
    # =========================================================================
    
    async def add_beneficiary(
        self,
        beneficiary_id: str,
        name: str,
        email: str,
        phone: str,
        bank_account: str = None,
        ifsc: str = None,
        vpa: str = None,
        address: str = None
    ) -> Dict[str, Any]:
        """
        Add a payout beneficiary
        
        Args:
            beneficiary_id: Unique ID
            name: Beneficiary name
            email: Email
            phone: Phone number
            bank_account: Bank account number
            ifsc: IFSC code
            vpa: UPI VPA (optional, alternative to bank)
            address: Address
        """
        payout_url = (
            "https://payout-gamma.cashfree.com/payout/v1" if self.env == "sandbox"
            else "https://payout-api.cashfree.com/payout/v1"
        )
        
        data = {
            "beneId": beneficiary_id,
            "name": name,
            "email": email,
            "phone": phone,
        }
        
        if bank_account and ifsc:
            data["bankAccount"] = bank_account
            data["ifsc"] = ifsc
        elif vpa:
            data["vpa"] = vpa
        
        if address:
            data["address1"] = address
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{payout_url}/addBeneficiary",
                headers=self.headers,
                json=data
            )
            response.raise_for_status()
            return response.json()
    
    async def request_transfer(
        self,
        transfer_id: str,
        amount: float,
        beneficiary_id: str,
        transfer_mode: str = "banktransfer",  # banktransfer, upi, paytm, etc.
        remarks: str = None
    ) -> Dict[str, Any]:
        """
        Request a payout transfer
        
        Args:
            transfer_id: Unique transfer ID
            amount: Transfer amount
            beneficiary_id: Beneficiary ID
            transfer_mode: "banktransfer", "upi", "paytm", "amazonpay"
            remarks: Transfer remarks
        """
        payout_url = (
            "https://payout-gamma.cashfree.com/payout/v1" if self.env == "sandbox"
            else "https://payout-api.cashfree.com/payout/v1"
        )
        
        data = {
            "beneId": beneficiary_id,
            "amount": str(amount),
            "transferId": transfer_id,
            "transferMode": transfer_mode,
        }
        
        if remarks:
            data["remarks"] = remarks
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{payout_url}/requestTransfer",
                headers=self.headers,
                json=data
            )
            response.raise_for_status()
            return response.json()
    
    async def get_transfer_status(self, transfer_id: str) -> Dict[str, Any]:
        """Get transfer status"""
        payout_url = (
            "https://payout-gamma.cashfree.com/payout/v1" if self.env == "sandbox"
            else "https://payout-api.cashfree.com/payout/v1"
        )
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{payout_url}/getTransferStatus",
                headers=self.headers,
                params={"transferId": transfer_id}
            )
            response.raise_for_status()
            return response.json()
    
    # =========================================================================
    # WEBHOOK VERIFICATION
    # =========================================================================
    
    def verify_webhook_signature(
        self,
        timestamp: str,
        raw_body: str,
        signature: str
    ) -> bool:
        """Verify webhook signature"""
        data = timestamp + raw_body
        expected = hmac.new(
            self.secret_key.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, signature)
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def get_checkout_code(
        self,
        order_id: str,
        payment_session_id: str,
        return_url: str = ""
    ) -> str:
        """Generate Cashfree checkout integration code"""
        sdk_url = (
            "https://sdk.cashfree.com/js/v3/cashfree.js" if self.env == "production"
            else "https://sdk.cashfree.com/js/v3/cashfree.sandbox.js"
        )
        
        return f'''
<script src="{sdk_url}"></script>
<script>
const cashfree = Cashfree({{
    mode: "{self.env}"
}});

document.getElementById("payButton").addEventListener("click", function() {{
    cashfree.checkout({{
        paymentSessionId: "{payment_session_id}",
        redirectTarget: "_self",
        returnUrl: "{return_url}"
    }}).then(function(result) {{
        if (result.error) {{
            console.log("Payment failed:", result.error);
        }}
        if (result.redirect) {{
            console.log("Redirecting...");
        }}
        if (result.paymentDetails) {{
            console.log("Payment successful:", result.paymentDetails);
        }}
    }});
}});
</script>
<button id="payButton">Pay Now</button>
'''
    
    async def create_quick_payment(
        self,
        amount: float,
        customer_phone: str,
        customer_email: str = None,
        customer_name: str = None,
        return_url: str = None
    ) -> Dict[str, Any]:
        """
        Quick payment flow: Create order and return checkout details
        """
        order_id = f"order_{uuid.uuid4().hex[:12]}"
        
        customer_details = {"customer_phone": customer_phone}
        if customer_email:
            customer_details["customer_email"] = customer_email
        if customer_name:
            customer_details["customer_name"] = customer_name
        customer_details["customer_id"] = f"cust_{uuid.uuid4().hex[:8]}"
        
        order_meta = {}
        if return_url:
            order_meta["return_url"] = return_url
        
        order = await self.create_order(
            order_id=order_id,
            order_amount=amount,
            customer_details=customer_details,
            order_meta=order_meta if order_meta else None
        )
        
        return {
            "order_id": order_id,
            "payment_session_id": order.get("payment_session_id"),
            "order_status": order.get("order_status"),
            "checkout_code": self.get_checkout_code(
                order_id,
                order.get("payment_session_id"),
                return_url or ""
            )
        }


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

async def get_cashfree_service(user_id: str) -> Optional[CashfreeService]:
    """Get CashfreeService for user if connected"""
    integration = await get_cashfree_integration(user_id)
    if not integration or integration.get("status") != "connected":
        return None
    
    return CashfreeService(
        integration["app_id"],
        integration["secret_key"],
        CASHFREE_ENV
    )


# Global instance for app-level payments
def get_app_cashfree() -> CashfreeService:
    """Get Cashfree service with app credentials"""
    if not CASHFREE_APP_ID or not CASHFREE_SECRET_KEY:
        raise ValueError("Cashfree not configured")
    return CashfreeService(CASHFREE_APP_ID, CASHFREE_SECRET_KEY, CASHFREE_ENV)
