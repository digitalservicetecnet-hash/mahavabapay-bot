# bot/app.py
import os
import logging
import asyncio
from decimal import Decimal
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import sqlalchemy as sa
import json
from dotenv import load_dotenv
import aioredis
from datetime import datetime

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("mahavabapay")

# DB setup (SQLAlchemy Core)
engine = create_async_engine(DATABASE_URL, echo=False, future=True)
AsyncSessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

metadata = sa.MetaData()

users = sa.Table(
    "users", metadata,
    sa.Column("id", sa.BigInteger, primary_key=True),
    sa.Column("telegram_id", sa.BigInteger, unique=True, nullable=False),
    sa.Column("username", sa.String),
    sa.Column("phone", sa.String),
    sa.Column("email", sa.String),
    sa.Column("kyc_status", sa.String),
    sa.Column("kyc_data", sa.JSON),
    sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
    sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"))
)

wallets = sa.Table(
    "wallets", metadata,
    sa.Column("id", sa.BigInteger, primary_key=True),
    sa.Column("user_id", sa.BigInteger, sa.ForeignKey("users.id", ondelete="CASCADE")),
    sa.Column("currency", sa.String, nullable=False),
    sa.Column("balance", sa.Numeric(30,8), server_default="0"),
    sa.Column("reserved", sa.Numeric(30,8), server_default="0"),
    sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
    sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
    sa.UniqueConstraint("user_id", "currency", name="u_wallet_user_currency")
)

transactions = sa.Table(
    "transactions", metadata,
    sa.Column("id", sa.BigInteger, primary_key=True),
    sa.Column("wallet_id", sa.BigInteger, sa.ForeignKey("wallets.id")),
    sa.Column("type", sa.String, nullable=False),
    sa.Column("amount", sa.Numeric(30,8), nullable=False),
    sa.Column("currency", sa.String, nullable=False),
    sa.Column("status", sa.String, nullable=False, server_default="pending"),
    sa.Column("external_ref", sa.String),
    sa.Column("metadata", sa.JSON),
    sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
    sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"))
)

# Redis queue
redis = None

# Telegram bot
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

# UTIL: DB helper
async def get_or_create_user(telegram_id:int, username:str=None, phone:str=None, db:AsyncSession=None):
    q = sa.select(users).where(users.c.telegram_id==telegram_id).limit(1)
    r = await db.execute(q)
    row = r.first()
    if row:
        return row._mapping
    ins = users.insert().values(telegram_id=telegram_id, username=username, phone=phone)
    res = await db.execute(ins)
    await db.commit()
    uid = res.inserted_primary_key[0]
    q2 = sa.select(users).where(users.c.id==uid)
    r2 = await db.execute(q2)
    return r2.first()._mapping

# UTIL: create/get wallet (currency default 'ETB')
async def get_or_create_wallet(user_id:int, currency:str='ETB', db:AsyncSession=None):
    q = sa.select(wallets).where(sa.and_(wallets.c.user_id==user_id, wallets.c.currency==currency)).limit(1)
    r = await db.execute(q)
    row = r.first()
    if row:
        return row._mapping
    ins = wallets.insert().values(user_id=user_id, currency=currency, balance=0)
    res = await db.execute(ins)
    await db.commit()
    wid = res.inserted_primary_key[0]
    q2 = sa.select(wallets).where(wallets.c.id==wid)
    r2 = await db.execute(q2)
    return r2.first()._mapping

# Placeholder: enqueue a payment request in redis for async worker
async def enqueue_payment_request(payload:dict):
    await redis.lpush("payments:queue", json.dumps(payload))

# Command handlers
@dp.message(Command(commands=["start"]))
async def cmd_start(message: Message):
    async with AsyncSessionLocal() as db:
        user = await get_or_create_user(message.from_user.id, message.from_user.username, None, db=db)
        await get_or_create_wallet(user['id'], "ETB", db=db)
    
    welcome_text = """
🎉 እንኳን ደህና መጡ MahavabaPay Bot!

የክፍያ ቦትዎን ለመጀመር የሚከተሉትን ትዕዛዞች ይጠቀሙ:

💰 /balance - የሂሳብ ቀሪ ሂሳብ ይመልከቱ
📥 /deposit - ገንዘብ ያስገቡ
📤 /withdraw - ገንዘብ ያውጡ
💱 /trade - ክሪፕቶ ይገበያዩ
📊 /history - የግብይት ታሪክ
ℹ️ /help - እገዛ

🔐 ደህንነትዎ ቅድሚያችን ነው!
    """
    await message.reply(welcome_text)

@dp.message(Command(commands=["help"]))
async def cmd_help(message: Message):
    help_text = """
📖 MahavabaPay Bot እገዛ

**የሚገኙ ትዕዛዞች:**

💰 /balance
   የሁሉም ዋሌቶችዎን ቀሪ ሂሳብ ይመልከቱ

📥 /deposit <መጠን> <ገንዘብ> <ስልክ>
   ምሳሌ: /deposit 100 ETB +251912345678
   
📤 /withdraw <መጠን> <ገንዘብ> <ስልክ>
   ምሳሌ: /withdraw 50 ETB +251912345678

💱 /trade <BUY/SELL> <ምልክት> <መጠን>
   ምሳሌ: /trade BUY BTC 0.001

📊 /history
   የቅርብ ጊዜ ግብይቶችዎን ይመልከቱ

**የሚደገፉ ገንዘቦች:**
• ETB (Ethiopian Birr)
• USD (US Dollar)
• USDT (Tether)
• BTC (Bitcoin)
• ETH (Ethereum)

**የክፍያ ዘዴዎች:**
• MPesa
• Telebirr
• Chapa
• Bank Transfer
• Crypto Exchange

ለተጨማሪ እገዛ: support@mahavabapay.com
    """
    await message.reply(help_text)

@dp.message(Command(commands=["balance"]))
async def cmd_balance(message: Message):
    async with AsyncSessionLocal() as db:
        q = sa.select(users).where(users.c.telegram_id==message.from_user.id).limit(1)
        r = await db.execute(q)
        row = r.first()
        if not row:
            await message.reply("እባክዎን /start ይጠቀሙ ለመጀመር.")
            return
        user = row._mapping
        q2 = sa.select(wallets).where(wallets.c.user_id==user['id'])
        rr = await db.execute(q2)
        rows = rr.fetchall()
        if not rows:
            await message.reply("ዋሌት አልተፈጠረም። /start")
            return
        text = "💰 የእርስዎ ሀብት:\n\n"
        for w in rows:
            wallet = w._mapping
            text += f"• {wallet['currency']}: {wallet['balance']}\n"
        await message.reply(text)

@dp.message(Command(commands=["deposit"]))
async def cmd_deposit(message: Message):
    parts = message.text.split()
    if len(parts) < 2:
        await message.reply("❌ የምንላችሁ መጠን እና ገንዘብ አላቀረብም.\n\nምሳሌ: /deposit 100 ETB +251912345678")
        return
    try:
        amount = Decimal(parts[1])
        if amount <= 0:
            await message.reply("❌ መጠን ከ0 በላይ መሆን አለበት")
            return
    except:
        await message.reply("❌ እባክዎን ትክክለኛ የሂሳብ መጠን ያስገቡ.")
        return
    
    currency = parts[2] if len(parts) > 2 else "ETB"
    phone = parts[3] if len(parts) > 3 else None
    
    if currency not in ['ETB', 'USD', 'USDT', 'BTC', 'ETH']:
        await message.reply("❌ ያልተደገፈ ገንዘብ። የሚደገፉ: ETB, USD, USDT, BTC, ETH")
        return
    
    async with AsyncSessionLocal() as db:
        q = sa.select(users).where(users.c.telegram_id==message.from_user.id).limit(1)
        r = await db.execute(q)
        user_row = r.first()
        if not user_row:
            await message.reply("እባክዎን /start ይጠቀሙ.")
            return
        user = user_row._mapping
        w = await get_or_create_wallet(user['id'], currency, db=db)
        
        # create transaction (pending)
        ins = transactions.insert().values(
            wallet_id=w['id'], 
            type="deposit", 
            amount=amount, 
            currency=currency, 
            status="pending", 
            metadata={"via":"mpesa","phone":phone}
        )
        res = await db.execute(ins)
        await db.commit()
        tx_id = res.inserted_primary_key[0]
        
        # enqueue provider call
        payload = {
            "tx_id": tx_id, 
            "user_id": user['id'], 
            "amount": str(amount), 
            "currency": currency, 
            "phone": phone, 
            "provider":"mpesa"
        }
        await enqueue_payment_request(payload)
        
        await message.reply(f"✅ የተጠየቀ ድምር ተመዝግቧል (tx={tx_id}).\n\n⏳ እባክዎን ሲስተሙ ይታወቃል።")

@dp.message(Command(commands=["withdraw"]))
async def cmd_withdraw(message: Message):
    parts = message.text.split()
    if len(parts) < 3:
        await message.reply("❌ ለምሳሌ: /withdraw 50 ETB +251912345678")
        return
    try:
        amount = Decimal(parts[1])
        if amount <= 0:
            await message.reply("❌ መጠን ከ0 በላይ መሆን አለበት")
            return
    except:
        await message.reply("❌ እባክዎን ትክክለኛ መጠን ያስገቡ.")
        return
    
    currency = parts[2]
    phone = parts[3] if len(parts) > 3 else None
    
    async with AsyncSessionLocal() as db:
        q = sa.select(users).where(users.c.telegram_id==message.from_user.id).limit(1)
        r = await db.execute(q)
        user_row = r.first()
        if not user_row:
            await message.reply("እባክዎን /start ይጠቀሙ.")
            return
        user = user_row._mapping
        
        q2 = sa.select(wallets).where(sa.and_(wallets.c.user_id==user['id'], wallets.c.currency==currency)).limit(1)
        r2 = await db.execute(q2)
        wrow = r2.first()
        if not wrow or Decimal(wrow._mapping['balance']) < amount:
            await message.reply("❌ እባክዎን የተያዙ ዋሌት ወይም በሂሳብ ያለው ብቃት አልባ.")
            return
        w = wrow._mapping
        
        # mark transaction pending
        ins = transactions.insert().values(
            wallet_id=w['id'], 
            type="withdraw", 
            amount=amount, 
            currency=currency, 
            status="pending", 
            metadata={"phone":phone}
        )
        res = await db.execute(ins)
        await db.commit()
        tx_id = res.inserted_primary_key[0]
        
        payload = {
            "tx_id": tx_id, 
            "user_id": user['id'], 
            "amount": str(amount), 
            "currency": currency, 
            "phone": phone, 
            "provider":"mpesa"
        }
        await enqueue_payment_request(payload)
        
        await message.reply(f"✅ የወጪ ጥያቄ ተመዝግቧል (tx={tx_id}).\n\n⏳ እርምጃ በታዳጊ ይቀጥላል።")

@dp.message(Command(commands=["trade"]))
async def cmd_trade(message: Message):
    parts = message.text.split()
    if len(parts) < 4:
        await message.reply("❌ ለምሳሌ: /trade BUY BTC 0.001")
        return
    
    side = parts[1].upper()
    symbol = parts[2].upper()
    
    try:
        amt = Decimal(parts[3])
    except:
        await message.reply("❌ ትክክለኛ መጠን ያስገቡ")
        return
    
    await message.reply(f"🔄 Trade request: {side} {amt} {symbol}\n\n⏳ Processing...")

@dp.message(Command(commands=["history"]))
async def cmd_history(message: Message):
    async with AsyncSessionLocal() as db:
        q = sa.select(users).where(users.c.telegram_id==message.from_user.id).limit(1)
        r = await db.execute(q)
        row = r.first()
        if not row:
            await message.reply("እባክዎን /start ይጠቀሙ.")
            return
        user = row._mapping
        
        # Get user's wallets
        q2 = sa.select(wallets.c.id).where(wallets.c.user_id==user['id'])
        wallet_ids = [w[0] for w in await db.execute(q2)]
        
        if not wallet_ids:
            await message.reply("ምንም ግብይቶች የሉም።")
            return
        
        # Get recent transactions
        q3 = sa.select(transactions).where(
            transactions.c.wallet_id.in_(wallet_ids)
        ).order_by(transactions.c.created_at.desc()).limit(10)
        
        txs = await db.execute(q3)
        tx_list = txs.fetchall()
        
        if not tx_list:
            await message.reply("ምንም ግብይቶች የሉም።")
            return
        
        text = "📊 የቅርብ ጊዜ ግብይቶች:\n\n"
        for tx in tx_list:
            t = tx._mapping
            emoji = "📥" if t['type'] == 'deposit' else "📤"
            text += f"{emoji} {t['type'].upper()}\n"
            text += f"   መጠን: {t['amount']} {t['currency']}\n"
            text += f"   ሁኔታ: {t['status']}\n"
            text += f"   ቀን: {t['created_at'].strftime('%Y-%m-%d %H:%M')}\n\n"
        
        await message.reply(text)

# startup/shutdown
async def on_startup():
    global redis
    redis = await aioredis.from_url(REDIS_URL)
    logger.info("Connected to Redis")
    # ensure DB ready: create tables if missing (simple)
    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)
    logger.info("DB tables ensured")

async def main():
    await on_startup()
    try:
        logger.info("Starting MahavabaPay Bot...")
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
