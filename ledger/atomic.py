import aioredis
import os

class AtomicLedger:
    """
    Atomic ledger for microsecond-level balance operations
    Uses Redis LUA scripts to ensure race-condition-free updates
    """
    
    def __init__(self, redis):
        self.redis = redis
        self.script = None

    async def load(self):
        """Load LUA script into Redis"""
        with open(os.path.join(os.path.dirname(__file__), "atomic_balance.lua")) as f:
            lua = f.read()
        self.script = await self.redis.script_load(lua)

    async def apply(self, user_id, currency, delta):
        """
        Apply balance change atomically
        
        Args:
            user_id: User ID
            currency: Currency code (ETB, USD, etc.)
            delta: Amount to add (positive) or subtract (negative)
        
        Returns:
            New balance or error
        """
        key = f"balance:{user_id}:{currency}"
        res = await self.redis.evalsha(self.script, 1, key, delta)
        return res

    async def get_balance(self, user_id, currency):
        """Get current balance"""
        key = f"balance:{user_id}:{currency}"
        balance = await self.redis.get(key)
        return float(balance) if balance else 0.0

    async def set_balance(self, user_id, currency, amount):
        """Set balance directly (use with caution)"""
        key = f"balance:{user_id}:{currency}"
        await self.redis.set(key, str(amount))

    async def reserve_funds(self, user_id, currency, amount):
        """Reserve funds for pending transaction"""
        key = f"reserved:{user_id}:{currency}"
        current = await self.redis.get(key)
        current = float(current) if current else 0.0
        await self.redis.set(key, str(current + amount))

    async def release_reserved(self, user_id, currency, amount):
        """Release reserved funds"""
        key = f"reserved:{user_id}:{currency}"
        current = await self.redis.get(key)
        current = float(current) if current else 0.0
        await self.redis.set(key, str(max(0, current - amount)))
