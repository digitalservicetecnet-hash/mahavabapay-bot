import os
import httpx

class ChapaProvider:
    """Chapa Payment Integration"""
    
    def __init__(self):
        self.secret = os.getenv("CHAPA_SECRET")
        self.base_url = "https://api.chapa.co/v1"

    async def create_charge(self, tx_id, amount, currency="ETB", email=None, phone=None):
        """Create a payment charge"""
        payload = {
            "amount": str(amount),
            "currency": currency,
            "tx_ref": f"MAH-{tx_id}",
            "callback_url": os.getenv("CHAPA_CALLBACK"),
            "return_url": os.getenv("CHAPA_RETURN_URL"),
            "customization": {
                "title": "MahavabaPay",
                "description": "Wallet Top-up"
            },
        }
        
        if email:
            payload["email"] = email
        if phone:
            payload["phone_number"] = phone
        
        async with httpx.AsyncClient() as client:
            res = await client.post(
                f"{self.base_url}/transaction/initialize",
                json=payload,
                headers={"Authorization": f"Bearer {self.secret}"}
            )
        
        return res.json()

    async def verify_payment(self, tx_ref):
        """Verify payment status"""
        async with httpx.AsyncClient() as client:
            res = await client.get(
                f"{self.base_url}/transaction/verify/{tx_ref}",
                headers={"Authorization": f"Bearer {self.secret}"}
            )
        
        return res.json()

    async def get_banks(self):
        """Get list of supported banks"""
        async with httpx.AsyncClient() as client:
            res = await client.get(
                f"{self.base_url}/banks",
                headers={"Authorization": f"Bearer {self.secret}"}
            )
        
        return res.json()

    async def transfer(self, account_number, bank_code, amount, currency="ETB"):
        """Transfer funds to bank account"""
        payload = {
            "account_number": account_number,
            "bank_code": bank_code,
            "amount": str(amount),
            "currency": currency,
            "reference": f"MAH-TRANSFER-{int(time.time())}"
        }
        
        async with httpx.AsyncClient() as client:
            res = await client.post(
                f"{self.base_url}/transfers",
                json=payload,
                headers={"Authorization": f"Bearer {self.secret}"}
            )
        
        return res.json()
