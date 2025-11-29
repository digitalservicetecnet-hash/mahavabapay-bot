# worker/worker.py
import os
import asyncio
import json
import logging
from dotenv import load_dotenv
import aioredis
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import sqlalchemy as sa
from decimal import Decimal
import httpx
from datetime import datetime

load_dotenv()
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
DATABASE_URL = os.getenv("DATABASE_URL")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger("mahavaba_worker")

engine = create_async_engine(DATABASE_URL, future=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
metadata = sa.MetaData()

# Define tables
users = sa.Table("users", metadata, autoload_with=engine)
wallets = sa.Table("wallets", metadata, autoload_with=engine)
transactions = sa.Table("transactions", metadata, autoload_with=engine)
payment_requests = sa.Table("payment_requests", metadata, autoload_with=engine)

async def process_one(redis):
    """Process one payment request from the queue"""
    raw = await redis.rpop("payments:queue")
    if not raw:
        return False
    
    payload = json.loads(raw)
    logger.info("Processing payment: %s", payload)
    
    action = payload.get("action")
    tx_id = payload.get("tx_id")
    
    async with AsyncSessionLocal() as db:
        # Load transaction
        qtx = sa.select(transactions).where(transactions.c.id==tx_id).limit(1)
        r = await db.execute(qtx)
        txrow = r.first()
        
        if not txrow:
            logger.error("Transaction not found: %s", tx_id)
            return True
        
        tx = txrow._mapping
        
        try:
            if action == "deposit":
                # Simulate provider confirmation (replace with real provider call)
                logger.info("Processing deposit for tx=%s", tx_id)
                
                # Simulate MPesa/Telebirr/Chapa API call
                await asyncio.sleep(0.1)  # Simulate network delay
                prov = {
                    "status": "success", 
                    "ref": f"mpesa-{int(datetime.utcnow().timestamp()*1000)}"
                }
                
                # Update wallet balance atomically
                qw = sa.select(wallets).where(wallets.c.id==tx['wallet_id']).with_for_update()
                rr = await db.execute(qw)
                w = rr.first()._mapping
                
                new_balance = Decimal(w['balance']) + Decimal(tx['amount'])
                upd = wallets.update().where(wallets.c.id==w['id']).values(balance=new_balance)
                await db.execute(upd)
                
                # Update transaction status
                upd_tx = transactions.update().where(transactions.c.id==tx['id']).values(
                    status="completed", 
                    external_ref=prov["ref"], 
                    updated_at=sa.text("now()")
                )
                await db.execute(upd_tx)
                await db.commit()
                
                logger.info("✅ Deposit completed: tx=%s, amount=%s %s", 
                           tx_id, tx['amount'], tx['currency'])
                
            elif action == "withdraw":
                # Simulate provider withdrawal
                logger.info("Processing withdrawal for tx=%s", tx_id)
                
                # Check balance and deduct
                qw = sa.select(wallets).where(wallets.c.id==tx['wallet_id']).with_for_update()
                rr = await db.execute(qw)
                w = rr.first()._mapping
                
                if Decimal(w['balance']) < Decimal(tx['amount']):
                    upd_tx = transactions.update().where(transactions.c.id==tx['id']).values(
                        status="failed", 
                        metadata={"error": "Insufficient funds"}
                    )
                    await db.execute(upd_tx)
                    await db.commit()
                    logger.error("❌ Insufficient funds for tx=%s", tx_id)
                else:
                    # Simulate provider call
                    await asyncio.sleep(0.1)
                    prov = {
                        "status": "success", 
                        "ref": f"bank-{int(datetime.utcnow().timestamp()*1000)}"
                    }
                    
                    new_balance = Decimal(w['balance']) - Decimal(tx['amount'])
                    await db.execute(
                        wallets.update().where(wallets.c.id==w['id']).values(balance=new_balance)
                    )
                    await db.execute(
                        transactions.update().where(transactions.c.id==tx['id']).values(
                            status="completed", 
                            external_ref=prov["ref"], 
                            updated_at=sa.text("now()")
                        )
                    )
                    await db.commit()
                    
                    logger.info("✅ Withdrawal completed: tx=%s, amount=%s %s", 
                               tx_id, tx['amount'], tx['currency'])
            else:
                logger.warning("Unknown action: %s", action)
                
        except Exception as e:
            logger.exception("❌ Error processing tx %s: %s", tx_id, e)
            # Update transaction as failed
            try:
                await db.execute(
                    transactions.update().where(transactions.c.id==tx['id']).values(
                        status="failed",
                        metadata={"error": str(e)}
                    )
                )
                await db.commit()
            except:
                pass
    
    return True

async def run():
    """Main worker loop"""
    redis = await aioredis.from_url(REDIS_URL)
    logger.info("🚀 MahavabaPay Worker started")
    logger.info("📡 Connected to Redis: %s", REDIS_URL)
    logger.info("🗄️  Connected to Database")
    
    while True:
        try:
            got = await process_one(redis)
            if not got:
                await asyncio.sleep(0.2)  # Reduce CPU when idle
        except Exception as e:
            logger.exception("Worker error: %s", e)
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(run())
