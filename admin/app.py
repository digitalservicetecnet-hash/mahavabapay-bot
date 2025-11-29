# admin/app.py
from flask import Flask, request, jsonify, abort
from flask_cors import CORS
from functools import wraps
import os
import psycopg
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

USER = os.getenv("ADMIN_BASIC_USER", "admin")
PASS = os.getenv("ADMIN_BASIC_PASS", "changeme")
DATABASE_URL = os.getenv("DATABASE_URL", "").replace("+asyncpg", "")

def check_auth(username, password):
    return username == USER and password == PASS

def requires_auth(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return abort(401)
        return f(*args, **kwargs)
    return wrapped

def get_db():
    return psycopg.connect(DATABASE_URL)

@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "mahavabapay-admin"})

@app.route("/api/stats")
@requires_auth
def stats():
    """Get system statistics"""
    with get_db() as conn:
        with conn.cursor() as cur:
            # Total users
            cur.execute("SELECT COUNT(*) FROM users")
            total_users = cur.fetchone()[0]
            
            # Total transactions
            cur.execute("SELECT COUNT(*) FROM transactions")
            total_txs = cur.fetchone()[0]
            
            # Total volume
            cur.execute("SELECT SUM(amount) FROM transactions WHERE status='completed'")
            total_volume = cur.fetchone()[0] or 0
            
            # Pending transactions
            cur.execute("SELECT COUNT(*) FROM transactions WHERE status='pending'")
            pending_txs = cur.fetchone()[0]
            
            return jsonify({
                "total_users": total_users,
                "total_transactions": total_txs,
                "total_volume": float(total_volume),
                "pending_transactions": pending_txs
            })

@app.route("/api/transactions")
@requires_auth
def transactions():
    """Get recent transactions"""
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT t.id, t.type, t.amount, t.currency, t.status, 
                       t.created_at, u.username, u.telegram_id
                FROM transactions t
                JOIN wallets w ON t.wallet_id = w.id
                JOIN users u ON w.user_id = u.id
                ORDER BY t.created_at DESC
                LIMIT %s OFFSET %s
            """, (limit, offset))
            
            rows = cur.fetchall()
            txs = []
            for row in rows:
                txs.append({
                    "id": row[0],
                    "type": row[1],
                    "amount": float(row[2]),
                    "currency": row[3],
                    "status": row[4],
                    "created_at": row[5].isoformat(),
                    "username": row[6],
                    "telegram_id": row[7]
                })
            
            return jsonify(txs)

@app.route("/api/users")
@requires_auth
def users():
    """Get users list"""
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT u.id, u.telegram_id, u.username, u.phone, 
                       u.kyc_status, u.created_at,
                       (SELECT SUM(balance) FROM wallets WHERE user_id = u.id) as total_balance
                FROM users u
                ORDER BY u.created_at DESC
                LIMIT %s OFFSET %s
            """, (limit, offset))
            
            rows = cur.fetchall()
            users_list = []
            for row in rows:
                users_list.append({
                    "id": row[0],
                    "telegram_id": row[1],
                    "username": row[2],
                    "phone": row[3],
                    "kyc_status": row[4],
                    "created_at": row[5].isoformat(),
                    "total_balance": float(row[6] or 0)
                })
            
            return jsonify(users_list)

@app.route("/api/wallets")
@requires_auth
def wallets():
    """Get wallets list"""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT w.id, w.currency, w.balance, w.reserved, 
                       u.username, u.telegram_id
                FROM wallets w
                JOIN users u ON w.user_id = u.id
                ORDER BY w.balance DESC
            """)
            
            rows = cur.fetchall()
            wallets_list = []
            for row in rows:
                wallets_list.append({
                    "id": row[0],
                    "currency": row[1],
                    "balance": float(row[2]),
                    "reserved": float(row[3]),
                    "username": row[4],
                    "telegram_id": row[5]
                })
            
            return jsonify(wallets_list)

@app.route("/api/analytics/daily")
@requires_auth
def daily_analytics():
    """Get daily transaction analytics"""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT DATE(created_at) as date,
                       COUNT(*) as count,
                       SUM(CASE WHEN status='completed' THEN amount ELSE 0 END) as volume
                FROM transactions
                WHERE created_at >= NOW() - INTERVAL '30 days'
                GROUP BY DATE(created_at)
                ORDER BY date DESC
            """)
            
            rows = cur.fetchall()
            analytics = []
            for row in rows:
                analytics.append({
                    "date": row[0].isoformat(),
                    "count": row[1],
                    "volume": float(row[2])
                })
            
            return jsonify(analytics)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)
