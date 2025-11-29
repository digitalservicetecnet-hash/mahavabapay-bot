import os
import httpx
import json
import hashlib
import base64
import time

class TelebirrProvider:
    """Telebirr Payment Integration"""
    
    def __init__(self):
        self.app_id = os.getenv("TELEBIRR_APP_ID")
        self.app_key = os.getenv("TELEBIRR_APP_KEY")
        self.short_code = os.getenv("TELEBIRR_SHORTCODE")
        self.notify_url = os.getenv("TELEBIRR_CALLBACK")
        self.base_url = "https://app.telebirr.com"

    def _sign(self, payload: dict):
        """Generate signature for request"""
        text = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
        sign = hashlib.sha256((text + self.app_key).encode()).hexdigest()
        return sign

    async def init_payment(self, amount, phone, tx_id):
        """Initialize payment request"""
        payload = {
            "appId": self.app_id,
            "shortCode": self.short_code,
            "subject": "MahavabaPay Topup",
            "outTradeNo": str(tx_id),
            "amount": str(amount),
            "notifyUrl": self.notify_url,
            "receiveName": phone,
            "timestamp": str(int(time.time() * 1000))
        }
        payload["signature"] = self._sign(payload)

        async with httpx.AsyncClient() as client:
            res = await client.post(
                f"{self.base_url}/api/v1/init",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
        
        return res.json()

    async def query_payment(self, tx_id):
        """Query payment status"""
        payload = {
            "appId": self.app_id,
            "outTradeNo": str(tx_id),
            "timestamp": str(int(time.time() * 1000))
        }
        payload["signature"] = self._sign(payload)

        async with httpx.AsyncClient() as client:
            res = await client.post(
                f"{self.base_url}/api/v1/query",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
        
        return res.json()

    def verify_callback(self, data: dict, signature: str):
        """Verify callback signature"""
        expected_sig = self._sign(data)
        return expected_sig == signature
