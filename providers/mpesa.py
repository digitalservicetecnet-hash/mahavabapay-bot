import os
import time
import base64
import httpx
from typing import Dict

class MPesaProvider:
    """MPesa Daraja API Integration"""
    
    def __init__(self):
        self.consumer_key = os.getenv("MPESA_API_KEY")
        self.consumer_secret = os.getenv("MPESA_API_SECRET")
        self.short_code = os.getenv("MPESA_SHORTCODE")
        self.passkey = os.getenv("MPESA_PASSKEY")
        self.base = "https://sandbox.safaricom.co.ke"  # Change to production URL
        self._token = None
        self._token_expiry = 0

    async def _get_token(self):
        """Get OAuth access token"""
        if self._token and time.time() < self._token_expiry:
            return self._token

        auth = base64.b64encode(
            f"{self.consumer_key}:{self.consumer_secret}".encode()
        ).decode()
        
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                self.base + "/oauth/v1/generate?grant_type=client_credentials",
                headers={"Authorization": f"Basic {auth}"}
            )
        
        data = resp.json()
        self._token = data["access_token"]
        self._token_expiry = time.time() + 3400
        return self._token

    async def stk_push(self, amount, phone, tx_id):
        """Initiate STK Push for deposit"""
        token = await self._get_token()
        timestamp = time.strftime("%Y%m%d%H%M%S")
        password = base64.b64encode(
            f"{self.short_code}{self.passkey}{timestamp}".encode()
        ).decode()

        payload = {
            "BusinessShortCode": self.short_code,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": str(amount),
            "PartyA": phone,
            "PartyB": self.short_code,
            "PhoneNumber": phone,
            "CallBackURL": os.getenv("MPESA_CALLBACK_URL"),
            "AccountReference": str(tx_id),
            "TransactionDesc": "MahavabaPay Deposit"
        }

        async with httpx.AsyncClient() as client:
            res = await client.post(
                self.base + "/mpesa/stkpush/v1/processrequest",
                json=payload,
                headers={"Authorization": f"Bearer {token}"}
            )
        
        return res.json()

    async def b2c_payment(self, amount, phone, tx_id):
        """Business to Customer payment for withdrawal"""
        token = await self._get_token()
        
        payload = {
            "InitiatorName": "testapi",
            "SecurityCredential": "your_security_credential",
            "CommandID": "BusinessPayment",
            "Amount": str(amount),
            "PartyA": self.short_code,
            "PartyB": phone,
            "Remarks": "MahavabaPay Withdrawal",
            "QueueTimeOutURL": os.getenv("MPESA_TIMEOUT_URL"),
            "ResultURL": os.getenv("MPESA_RESULT_URL"),
            "Occasion": str(tx_id)
        }
        
        async with httpx.AsyncClient() as client:
            res = await client.post(
                self.base + "/mpesa/b2c/v1/paymentrequest",
                json=payload,
                headers={"Authorization": f"Bearer {token}"}
            )
        
        return res.json()

    async def confirm(self, mpesa_receipt_number):
        """Verify transaction status"""
        # Implement transaction status query
        return {"status": "success"}
