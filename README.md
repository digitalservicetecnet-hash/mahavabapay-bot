# MahavabaPay Bot

**Microsecond Payment Processing System with Telegram Bot Integration**

## Features

- 🚀 Microsecond-level payment processing
- 💰 Multi-currency wallet support (ETB, USD, USDT, BTC)
- 🔄 Real-time transaction processing with Redis queue
- 💳 Multiple payment providers:
  - MPesa (Daraja API)
  - Telebirr
  - Chapa
  - OKX Exchange
  - Bank API
- 🤖 Telegram Bot interface
- 📊 Admin dashboard (React + Tailwind)
- 🔐 Secure authentication & KYC
- 📈 Real-time analytics & monitoring

## Architecture

```
mahavabapay-bot/
├── bot/              # Telegram bot service
├── worker/           # Payment processing worker
├── admin/            # Admin dashboard API
├── admin-frontend/   # React admin UI
├── providers/        # Payment provider integrations
├── ledger/           # Redis atomic ledger
├── migrations/       # Database schemas
└── infra/            # Docker & deployment configs
```

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Node.js 18+ (for admin frontend)
- Python 3.11+
- PostgreSQL 15
- Redis 7

### Installation

1. Clone the repository:
```bash
git clone https://github.com/digitalservicetecnet-hash/mahavabapay-bot.git
cd mahavabapay-bot
```

2. Copy environment file:
```bash
cp .env.sample .env
```

3. Configure your `.env` file with:
   - Telegram Bot Token
   - Database credentials
   - Payment provider API keys
   - Redis URL

4. Start services:
```bash
docker-compose -f infra/docker-compose.yml up --build -d
```

5. Apply database migrations:
```bash
docker exec -it mahavabapay-db psql -U mahavaba -d mahavaba -f /migrations/schema.sql
```

### Telegram Bot Commands

- `/start` - Initialize wallet
- `/balance` - Check wallet balance
- `/deposit <amount> <currency> <phone>` - Deposit funds
- `/withdraw <amount> <currency> <phone>` - Withdraw funds
- `/trade <BUY/SELL> <symbol> <amount>` - Trade crypto

## Configuration

### Environment Variables

```env
# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token

# Database
DATABASE_URL=postgresql+asyncpg://mahavaba:mahavaba_pass@db:5432/mahavaba

# Redis
REDIS_URL=redis://redis:6379/0

# MPesa
MPESA_API_KEY=your_key
MPESA_API_SECRET=your_secret
MPESA_SHORTCODE=your_shortcode
MPESA_PASSKEY=your_passkey
MPESA_CALLBACK_URL=https://yourdomain.com/mpesa/callback

# Telebirr
TELEBIRR_APP_ID=your_app_id
TELEBIRR_APP_KEY=your_app_key
TELEBIRR_SHORTCODE=your_shortcode
TELEBIRR_CALLBACK=https://yourdomain.com/telebirr/callback

# Chapa
CHAPA_SECRET=your_secret
CHAPA_CALLBACK=https://yourdomain.com/chapa/callback
CHAPA_RETURN_URL=https://yourdomain.com/chapa/return

# OKX
OKX_API_KEY=your_key
OKX_API_SECRET=your_secret
OKX_PASSPHRASE=your_passphrase

# Bank API
BANK_API_BASE=https://bank-api.example.com
BANK_API_KEY=your_key

# Admin
ADMIN_BASIC_USER=admin
ADMIN_BASIC_PASS=changeme

# Service
SERVICE_REGION=ET
LOG_LEVEL=INFO
```

## Payment Provider Integration

### MPesa (Daraja API)
- STK Push for deposits
- B2C for withdrawals
- Callback verification

### Telebirr
- Payment initialization
- Signature verification
- Webhook handling

### Chapa
- Charge creation
- Payment verification
- Multi-currency support

### OKX Exchange
- Crypto trading
- Withdrawals
- Market data

## Security

- ✅ TLS/SSL encryption
- ✅ API key authentication
- ✅ Webhook signature verification
- ✅ Idempotency keys
- ✅ Rate limiting
- ✅ KYC verification
- ✅ 2FA for withdrawals
- ✅ Audit logging

## Microsecond Processing

For true microsecond-level performance:

1. **In-Memory Ledger**: Redis with LUA scripts for atomic operations
2. **Write-Behind Pattern**: Async PostgreSQL replication
3. **Colocated Infrastructure**: Same AZ/rack deployment
4. **Low-Latency Network**: RDMA/FastPath hardware
5. **Optimistic Concurrency**: Lock-free balance updates

## Monitoring

- Prometheus metrics
- Grafana dashboards
- Real-time alerts
- Transaction tracking
- Queue monitoring

## Production Deployment

### Using Railway

```bash
railway login
railway init
railway up
```

### Using Docker Swarm

```bash
docker stack deploy -c infra/docker-compose.yml mahavaba
```

### Using Kubernetes

```bash
kubectl apply -f infra/k8s/
```

## API Documentation

### Admin API Endpoints

- `GET /api/transactions` - List transactions
- `GET /api/users` - List users
- `GET /api/wallets` - List wallets
- `POST /api/payouts` - Create payout
- `GET /api/analytics` - Get analytics

## Development

### Running Tests

```bash
# Backend tests
cd bot && python -m pytest

# Frontend tests
cd admin-frontend && npm test
```

### Code Style

```bash
# Python
black bot/ worker/
flake8 bot/ worker/

# JavaScript
cd admin-frontend && npm run lint
```

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## License

MIT License - see LICENSE file

## Support

- 📧 Email: support@mahavabapay.com
- 💬 Telegram: @mahavabapay
- 🐛 Issues: [GitHub Issues](https://github.com/digitalservicetecnet-hash/mahavabapay-bot/issues)

## Roadmap

- [ ] Mobile app (React Native)
- [ ] Multi-language support
- [ ] Advanced analytics
- [ ] Merchant API
- [ ] Recurring payments
- [ ] Invoice generation
- [ ] QR code payments
- [ ] NFC support

---

**Built with ❤️ for Ethiopia's payment infrastructure**
