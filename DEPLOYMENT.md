# MahavabaPay Deployment Guide

## Prerequisites

- Docker & Docker Compose
- PostgreSQL 15+
- Redis 7+
- Telegram Bot Token
- Payment provider API keys

## Local Development Setup

### 1. Clone Repository

```bash
git clone https://github.com/digitalservicetecnet-hash/mahavabapay-bot.git
cd mahavabapay-bot
```

### 2. Configure Environment

```bash
cp .env.sample .env
```

Edit `.env` and add your credentials:
- `TELEGRAM_BOT_TOKEN` - Get from @BotFather
- Database credentials
- Payment provider API keys

### 3. Start Services

```bash
cd infra
docker-compose up --build -d
```

### 4. Apply Database Migrations

```bash
docker exec -it mahavabapay-db psql -U mahavaba -d mahavaba -f /migrations/schema.sql
```

### 5. Verify Services

```bash
docker-compose ps
docker-compose logs -f bot
```

## Production Deployment

### Option 1: Railway

1. Install Railway CLI:
```bash
npm install -g @railway/cli
```

2. Login and initialize:
```bash
railway login
railway init
```

3. Add environment variables:
```bash
railway variables set TELEGRAM_BOT_TOKEN=your_token
railway variables set DATABASE_URL=your_db_url
# ... add all other variables
```

4. Deploy:
```bash
railway up
```

### Option 2: Docker Swarm

1. Initialize swarm:
```bash
docker swarm init
```

2. Deploy stack:
```bash
docker stack deploy -c infra/docker-compose.yml mahavaba
```

3. Check services:
```bash
docker service ls
docker service logs mahavaba_bot
```

### Option 3: Kubernetes

1. Create namespace:
```bash
kubectl create namespace mahavabapay
```

2. Create secrets:
```bash
kubectl create secret generic mahavaba-secrets \
  --from-literal=telegram-token=your_token \
  --from-literal=db-password=your_password \
  -n mahavabapay
```

3. Apply manifests:
```bash
kubectl apply -f infra/k8s/ -n mahavabapay
```

## Monitoring Setup

### Prometheus

Access at: `http://localhost:9090`

### Grafana

1. Access at: `http://localhost:3000`
2. Default credentials: `admin/admin`
3. Add Prometheus data source: `http://prometheus:9090`
4. Import dashboards

## Telegram Bot Setup

### 1. Create Bot

Talk to @BotFather on Telegram:
```
/newbot
```

Follow prompts to get your bot token.

### 2. Set Bot Commands

```
/setcommands

start - Initialize wallet
balance - Check balance
deposit - Deposit funds
withdraw - Withdraw funds
trade - Trade crypto
history - Transaction history
help - Get help
```

### 3. Set Bot Description

```
/setdescription

MahavabaPay - Microsecond payment processing system supporting MPesa, Telebirr, Chapa, and crypto trading.
```

## Payment Provider Setup

### MPesa (Daraja API)

1. Register at https://developer.safaricom.co.ke
2. Create app and get credentials
3. Configure callback URLs
4. Test in sandbox first

### Telebirr

1. Contact Telebirr for merchant account
2. Get API credentials
3. Configure webhook URL
4. Test integration

### Chapa

1. Register at https://chapa.co
2. Get API key from dashboard
3. Configure callback and return URLs
4. Test with test mode

### OKX

1. Create account at https://www.okx.com
2. Generate API keys (with withdrawal permissions)
3. Whitelist IP addresses
4. Enable 2FA

## Database Backup

### Manual Backup

```bash
docker exec mahavabapay-db pg_dump -U mahavaba mahavaba > backup.sql
```

### Automated Backup

Add to crontab:
```bash
0 2 * * * docker exec mahavabapay-db pg_dump -U mahavaba mahavaba > /backups/mahavaba_$(date +\%Y\%m\%d).sql
```

## Scaling

### Horizontal Scaling

1. Scale bot instances:
```bash
docker-compose up --scale bot=3
```

2. Scale workers:
```bash
docker-compose up --scale worker=5
```

### Redis Cluster

For high availability, use Redis Cluster:
```bash
docker-compose -f infra/docker-compose.redis-cluster.yml up
```

### Database Replication

Set up PostgreSQL streaming replication for read replicas.

## Security Checklist

- [ ] Change default admin password
- [ ] Enable SSL/TLS for all connections
- [ ] Use secrets manager (Vault, AWS Secrets Manager)
- [ ] Enable firewall rules
- [ ] Set up rate limiting
- [ ] Enable audit logging
- [ ] Implement 2FA for withdrawals
- [ ] Regular security audits
- [ ] Keep dependencies updated

## Troubleshooting

### Bot Not Responding

```bash
docker-compose logs bot
# Check if token is correct
# Verify network connectivity
```

### Database Connection Issues

```bash
docker-compose logs db
# Check DATABASE_URL format
# Verify PostgreSQL is running
```

### Redis Connection Issues

```bash
docker-compose logs redis
# Check REDIS_URL
# Verify Redis is accessible
```

### Payment Provider Errors

- Check API credentials
- Verify callback URLs are accessible
- Check provider status pages
- Review provider logs

## Performance Tuning

### PostgreSQL

Edit `postgresql.conf`:
```
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 4MB
min_wal_size = 1GB
max_wal_size = 4GB
```

### Redis

```
maxmemory 2gb
maxmemory-policy allkeys-lru
```

## Monitoring Alerts

Set up alerts for:
- High error rate
- Queue backlog
- Database connection pool exhaustion
- High latency
- Failed transactions
- Low balance warnings

## Support

- Email: support@mahavabapay.com
- Telegram: @mahavabapay
- GitHub Issues: https://github.com/digitalservicetecnet-hash/mahavabapay-bot/issues
