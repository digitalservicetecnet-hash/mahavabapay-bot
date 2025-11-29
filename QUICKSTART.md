# MahavabaPay Quick Start Guide

Get your payment bot running in 5 minutes!

## Step 1: Get Telegram Bot Token

1. Open Telegram and search for `@BotFather`
2. Send `/newbot` command
3. Follow the prompts to create your bot
4. Copy the bot token (looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

## Step 2: Clone and Configure

```bash
# Clone repository
git clone https://github.com/digitalservicetecnet-hash/mahavabapay-bot.git
cd mahavabapay-bot

# Copy environment file
cp .env.sample .env

# Edit .env and add your bot token
nano .env
# Set TELEGRAM_BOT_TOKEN=your_token_here
```

## Step 3: Start Services

```bash
cd infra
docker-compose up -d
```

Wait for services to start (about 30 seconds).

## Step 4: Initialize Database

```bash
docker exec -it mahavabapay-db psql -U mahavaba -d mahavaba -f /migrations/schema.sql
```

## Step 5: Test Your Bot

1. Open Telegram
2. Search for your bot by username
3. Send `/start` command
4. You should see the welcome message!

## Available Commands

- `/start` - Initialize your wallet
- `/balance` - Check your balance
- `/deposit 100 ETB +251912345678` - Deposit funds
- `/withdraw 50 ETB +251912345678` - Withdraw funds
- `/history` - View transaction history
- `/help` - Get help

## Check Logs

```bash
# Bot logs
docker-compose logs -f bot

# Worker logs
docker-compose logs -f worker

# All services
docker-compose logs -f
```

## Access Admin Dashboard

1. Open browser: `http://localhost:8000/health`
2. Should see: `{"status": "ok"}`
3. API endpoints require basic auth (admin/changeme by default)

## Monitor Services

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)

## Next Steps

### Configure Payment Providers

Edit `.env` and add your provider credentials:

```env
# MPesa
MPESA_API_KEY=your_key
MPESA_API_SECRET=your_secret
MPESA_SHORTCODE=your_shortcode

# Telebirr
TELEBIRR_APP_ID=your_app_id
TELEBIRR_APP_KEY=your_key

# Chapa
CHAPA_SECRET=your_secret

# OKX
OKX_API_KEY=your_key
OKX_API_SECRET=your_secret
```

Restart services:
```bash
docker-compose restart
```

### Enable Production Mode

1. Change database password in `.env`
2. Change admin password
3. Use production URLs for payment providers
4. Enable SSL/TLS
5. Set up domain and webhook mode

### Deploy to Production

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

## Troubleshooting

### Bot not responding?

```bash
# Check bot logs
docker-compose logs bot

# Verify token is correct
echo $TELEGRAM_BOT_TOKEN

# Restart bot
docker-compose restart bot
```

### Database connection error?

```bash
# Check database is running
docker-compose ps db

# Check connection
docker exec -it mahavabapay-db psql -U mahavaba -d mahavaba -c "SELECT 1"
```

### Redis connection error?

```bash
# Check Redis is running
docker-compose ps redis

# Test connection
docker exec -it mahavabapay-redis redis-cli ping
```

## Support

- 📧 Email: support@mahavabapay.com
- 💬 Telegram: @mahavabapay
- 🐛 Issues: [GitHub Issues](https://github.com/digitalservicetecnet-hash/mahavabapay-bot/issues)

## What's Next?

- [ ] Configure payment providers
- [ ] Set up KYC verification
- [ ] Enable 2FA for withdrawals
- [ ] Set up monitoring alerts
- [ ] Deploy to production
- [ ] Add custom features

---

**🎉 Congratulations! Your payment bot is running!**
