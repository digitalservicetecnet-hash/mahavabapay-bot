import os
import hmac
import hashlib
import time
import httpx
import base64
import json

class OKXProvider:
    """OKX Exchange Integration"""
    
    def __init__(self):
        self.key = os.getenv("OKX_API_KEY")
        self.secret = os.getenv("OKX_API_SECRET")
        self.passphrase = os.getenv("OKX_PASSPHRASE")
        self.base_url = "https://www.okx.com"

    def _sign(self, timestamp, method, request_path, body=""):
        """Generate signature for API request"""
        message = f"{timestamp}{method.upper()}{request_path}{body}"
        mac = hmac.new(
            self.secret.encode(), 
            message.encode(), 
            hashlib.sha256
        )
        return base64.b64encode(mac.digest()).decode()

    async def get_balance(self, currency=None):
        """Get account balance"""
        timestamp = str(time.time())
        request_path = "/api/v5/account/balance"
        
        if currency:
            request_path += f"?ccy={currency}"
        
        sign = self._sign(timestamp, "GET", request_path)
        
        async with httpx.AsyncClient() as client:
            res = await client.get(
                self.base_url + request_path,
                headers={
                    "OK-ACCESS-KEY": self.key,
                    "OK-ACCESS-SIGN": sign,
                    "OK-ACCESS-TIMESTAMP": timestamp,
                    "OK-ACCESS-PASSPHRASE": self.passphrase,
                    "Content-Type": "application/json"
                }
            )
        
        return res.json()

    async def withdraw(self, amount, to_address, currency="USDT", chain="TRC20"):
        """Withdraw cryptocurrency"""
        timestamp = str(time.time())
        request_path = "/api/v5/asset/withdrawal"
        
        body = json.dumps({
            "ccy": currency,
            "amt": str(amount),
            "dest": "4",  # On-chain withdrawal
            "toAddr": to_address,
            "chain": chain,
            "fee": "1"
        })
        
        sign = self._sign(timestamp, "POST", request_path, body)
        
        async with httpx.AsyncClient() as client:
            res = await client.post(
                self.base_url + request_path,
                headers={
                    "OK-ACCESS-KEY": self.key,
                    "OK-ACCESS-SIGN": sign,
                    "OK-ACCESS-TIMESTAMP": timestamp,
                    "OK-ACCESS-PASSPHRASE": self.passphrase,
                    "Content-Type": "application/json"
                },
                content=body
            )
        
        return res.json()

    async def place_order(self, symbol, side, amount, order_type="market"):
        """Place a trading order"""
        timestamp = str(time.time())
        request_path = "/api/v5/trade/order"
        
        body = json.dumps({
            "instId": symbol,
            "tdMode": "cash",
            "side": side.lower(),
            "ordType": order_type,
            "sz": str(amount)
        })
        
        sign = self._sign(timestamp, "POST", request_path, body)
        
        async with httpx.AsyncClient() as client:
            res = await client.post(
                self.base_url + request_path,
                headers={
                    "OK-ACCESS-KEY": self.key,
                    "OK-ACCESS-SIGN": sign,
                    "OK-ACCESS-TIMESTAMP": timestamp,
                    "OK-ACCESS-PASSPHRASE": self.passphrase,
                    "Content-Type": "application/json"
                },
                content=body
            )
        
        return res.json()

    async def get_ticker(self, symbol):
        """Get ticker information"""
        async with httpx.AsyncClient() as client:
            res = await client.get(
                f"{self.base_url}/api/v5/market/ticker?instId={symbol}"
            )
        
        return res.json()
