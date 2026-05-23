"""
ModelHub API — DeepSeek出海版 后端服务
Flask应用，提供OpenAI兼容的Chat Completions API
定价为美元（USD），Lemon Squeezy收款后按汇率换算
"""

import os
import json
import time
import uuid
import re
import hashlib
import hmac
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from flask import Flask, request, jsonify, make_response, send_from_directory, session
from functools import wraps

STATIC_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)

# Secret key for Flask sessions
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "mh-session-secret-change-in-prod")

# ===== 配置 =====
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "sk-77d2408c2e014c12958c38c9159124ed")
SERVE_STATIC = os.environ.get("SERVE_STATIC", "true").lower() == "true"
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
ADMIN_API_KEY = os.environ.get("ADMIN_API_KEY", "mh-admin-secret-change-me")

# Lemon Squeezy
LEMONSQUEEZY_API_KEY = os.environ.get("LEMONSQUEEZY_API_KEY", "")
LEMONSQUEEZY_STORE_ID = os.environ.get("LEMONSQUEEZY_STORE_ID", "369169")
LEMONSQUEEZY_WEBHOOK_SECRET = os.environ.get("LEMONSQUEEZY_WEBHOOK_SECRET", "")

# CNY→USD 汇率（Lemon Squeezy 收 CNY，余额存 USD）
CNY_TO_USD_RATE = 6.75

# 订阅方案（美元价格）
PLANS = {
    "backpack": {"name": "Backpack", "monthly_credits": 100000000, "price": 15, "max_keys": 1, "features": ["100M tokens/month included", "All models", "1 API key", "Standard rate limits", "OpenAI-compatible API"], "price_cny": 100},
    "launch": {"name": "Launch", "monthly_credits": 500000000, "price": 65, "max_keys": 5, "features": ["500M tokens/month included", "Priority routing", "5 API keys + team", "High rate limits", "Usage analytics", "Priority support"], "price_cny": 438},
}

# 用户数据库（简易文件版，后续可换SQLite）
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
USERS_FILE = os.path.join(DATA_DIR, "users.json")
os.makedirs(DATA_DIR, exist_ok=True)

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

def get_user(api_key):
    users = load_users()
    for uid, info in users.items():
        # 单 key（旧格式兼容）
        if info.get("api_key") == api_key:
            return uid, info
        # 多 key（新格式）
        for k in info.get("api_keys", []):
            if k.get("key") == api_key and k.get("revoked", False) == False:
                return uid, info
    return None, None

# ===== 定价 (USD per 1M tokens) =====
MODELS = {
    "deepseek-v4-flash": {
        "id": "deepseek-v4-flash",
        "object": "model",
        "created": int(time.time()),
        "owned_by": "modelhub",
        "pricing": {
            "input": 0.15,       # $0.15 per 1M tokens
            "output": 0.30,      # $0.30 per 1M tokens
            "input_cache_hit": 0.04,
        }
    },
    "deepseek-reasoner": {
        "id": "deepseek-reasoner",
        "object": "model",
        "created": int(time.time()),
        "owned_by": "modelhub",
        "pricing": {
            "input": 0.25,
            "output": 0.65,
        },
        "status": "coming_soon"
    }
}

MODEL_MAP = {
    "deepseek-v4-flash": "deepseek-chat",
    "deepseek-reasoner": "deepseek-reasoner",
}

TOKEN_ALLOWANCE = {
    "backpack": 100_000_000,
    "launch": 500_000_000,
}

# ===== 中间件 =====
def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        match = re.match(r"^Bearer\s+(.+)$", auth)
        if not match:
            return jsonify({"error": {"message": "Missing or invalid API key", "type": "auth_error", "code": 401}}), 401
        
        api_key = match.group(1)
        uid, user = get_user(api_key)
        if not user:
            return jsonify({"error": {"message": "Invalid API key", "type": "auth_error", "code": 401}}), 401
        
        if user.get("balance", 0) <= 0:
            return jsonify({"error": {"message": "Insufficient credits. Please top up.", "type": "insufficient_quota", "code": 402}}), 402
        
        request.user_id = uid
        request.user = user
        return f(*args, **kwargs)
    return decorated

# ===== 路由 =====

@app.route("/")
def home():
    if SERVE_STATIC:
        return send_from_directory(STATIC_DIR, "index.html")
    return jsonify({"name": "ModelHub API", "version": "1.0.0", "status": "operational"})

@app.route("/pricing.html")
@app.route("/pricing")
def pricing_page():
    if SERVE_STATIC:
        return send_from_directory(STATIC_DIR, "pricing.html")
    return jsonify({"error": "Static not enabled"}), 404

@app.route("/docs.html")
@app.route("/docs")
def docs_page():
    if SERVE_STATIC:
        return send_from_directory(STATIC_DIR, "docs.html")
    return jsonify({"error": "Static not enabled"}), 404

@app.route("/privacy.html")
@app.route("/privacy")
def privacy_page():
    if SERVE_STATIC:
        return send_from_directory(STATIC_DIR, "privacy.html")
    return jsonify({"error": "Static not enabled"}), 404

@app.route("/v1/models", methods=["GET"])
@require_api_key
def list_models():
    return jsonify({
        "object": "list",
        "data": [m for m in MODELS.values() if m.get("status") != "coming_soon"]
    })

@app.route("/v1/chat/completions", methods=["POST"])
@require_api_key
def chat_completions():
    body = request.get_json(silent=True)
    if not body:
        return jsonify({"error": {"message": "Invalid JSON body", "type": "invalid_request_error", "code": 400}}), 400
    
    model = body.get("model", "")
    upstream_model = MODEL_MAP.get(model)
    
    if not upstream_model:
        return jsonify({"error": {"message": f"Unknown model: {model}", "type": "invalid_request_error", "code": 400}}), 400
    
    if model in MODELS and MODELS[model].get("status") == "coming_soon":
        return jsonify({"error": {"message": f"Model {model} is not yet available", "type": "model_not_available", "code": 400}}), 400
    
    messages = body.get("messages", [])
    input_text = json.dumps(messages)
    estimated_input_tokens = max(100, len(input_text) // 2)
    
    pricing = MODELS[model]["pricing"]
    estimated_cost = (estimated_input_tokens / 1000000) * pricing["input"]
    
    user = request.user
    if user["balance"] < estimated_cost:
        return jsonify({
            "error": {
                "message": f"Insufficient balance. You have ${user['balance']:.4f} but this request needs ~${estimated_cost:.4f}.",
                "type": "insufficient_quota",
                "code": 402
            }
        }), 402
    
    try:
        upstream_body = {
            "model": upstream_model,
            "messages": messages,
            "temperature": body.get("temperature", 1.0),
            "max_tokens": body.get("max_tokens", 4096),
            "stream": body.get("stream", False),
        }
        
        req = Request(
            f"{DEEPSEEK_BASE_URL}/chat/completions",
            data=json.dumps(upstream_body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
            },
            method="POST"
        )
        
        resp = urlopen(req, timeout=60)
        result = json.loads(resp.read().decode("utf-8"))
        
        input_tokens = result.get("usage", {}).get("prompt_tokens", estimated_input_tokens)
        output_tokens = result.get("usage", {}).get("completion_tokens", 0)
        
        input_cost = (input_tokens / 1000000) * pricing["input"]
        output_cost = (output_tokens / 1000000) * pricing["output"]
        total_cost = round(input_cost + output_cost, 6)
        
        # 扣费（USD）
        users = load_users()
        if request.user_id in users:
            users[request.user_id]["balance"] = round(users[request.user_id]["balance"] - total_cost, 6)
            users[request.user_id]["total_spent"] = round(users[request.user_id].get("total_spent", 0) + total_cost, 6)
            users[request.user_id]["total_requests"] = users[request.user_id].get("total_requests", 0) + 1
            save_users(users)
        
        result["usage"]["cost_usd"] = total_cost
        result["model"] = model
        
        return jsonify(result)
        
    except HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        try:
            error_json = json.loads(error_body)
        except:
            error_json = {"message": error_body[:200]}
        
        return jsonify({
            "error": {
                "message": f"Upstream error: {error_json.get('message', 'Unknown')}",
                "type": "upstream_error",
                "code": e.code
            }
        }), e.code
    
    except URLError as e:
        return jsonify({
            "error": {
                "message": f"Failed to reach upstream: {str(e.reason)}",
                "type": "upstream_connection_error",
                "code": 502
            }
        }), 502
    
    except Exception as e:
        return jsonify({
            "error": {
                "message": f"Internal error: {str(e)}",
                "type": "internal_error",
                "code": 500
            }
        }), 500


# ===== Lemon Squeezy Webhook =====
import hashlib
import hmac

@app.route("/webhook/lemon-squeezy", methods=["POST"])
def lemon_squeezy_webhook():
    signature = request.headers.get("X-Signature", "")
    body = request.get_data(as_text=True)
    
    if LEMONSQUEEZY_WEBHOOK_SECRET:
        expected = hmac.new(LEMONSQUEEZY_WEBHOOK_SECRET.encode(), body.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, signature):
            return jsonify({"error": "Invalid signature"}), 401
    
    data = request.get_json(silent=True) or {}
    event_name = data.get("meta", {}).get("event_name", "")
    custom_data = data.get("meta", {}).get("custom_data", {})
    
    if event_name == "order_created":
        user_id = custom_data.get("user_id", "")
        variant_id = str(data.get("data", {}).get("attributes", {}).get("variant_id", ""))
        
        if user_id:
            users = load_users()
            if user_id in users:
                # Lemon Squeezy 收 CNY，换算成 USD 存入用户余额
                # Variant → CNY amount
                variant_cny = {"1674045": 100, "1674083": 438, "1674087": 33, "1674096": 168, "1674097": 675}
                amount_cny = variant_cny.get(variant_id, 0)
                amount_usd = round(amount_cny / CNY_TO_USD_RATE, 2)
                
                users[user_id]["balance"] = round(users[user_id].get("balance", 0) + amount_usd, 6)
                users[user_id]["total_deposited"] = round(users[user_id].get("total_deposited", 0) + amount_usd, 6)
                
                # If subscription, update plan and reset monthly tokens
                if variant_id == "1674045" or variant_id == "1674083":
                    plan_name = "backpack" if variant_id == "1674045" else "launch"
                    users[user_id]["plan"] = plan_name
                    users[user_id]["subscription_active"] = True
                    users[user_id]["monthly_tokens_used"] = 0
                    users[user_id]["monthly_reset_at"] = time.time() + 2592000
                
                save_users(users)
                return jsonify({"status": "ok"}), 200
    
    return jsonify({"status": "ignored"}), 200


# ===== 订阅 & 账户API =====

@app.route("/v1/account", methods=["GET"])
@require_api_key
def get_account():
    user = request.user
    plan = user.get("plan", "free")
    plan_info = PLANS.get(plan, {"monthly_credits": 0, "name": "Free"})
    monthly_used = user.get("monthly_tokens_used", 0)
    
    reset_at = user.get("monthly_reset_at", 0)
    if reset_at and time.time() > reset_at:
        monthly_used = 0
        users = load_users()
        if request.user_id in users:
            users[request.user_id]["monthly_tokens_used"] = 0
            users[request.user_id]["monthly_reset_at"] = time.time() + 2592000
            save_users(users)
    
    return jsonify({
        "user_id": request.user_id,
        "email": user.get("email", ""),
        "api_key": user.get("api_key", ""),
        "balance": user.get("balance", 0),
        "currency": "USD",
        "plan": plan,
        "plan_name": plan_info.get("name", "Free"),
        "monthly_tokens_included": plan_info.get("monthly_credits", 0),
        "monthly_tokens_used": monthly_used,
        "monthly_tokens_remaining": max(0, plan_info.get("monthly_credits", 0) - monthly_used),
        "total_spent": user.get("total_spent", 0),
        "total_requests": user.get("total_requests", 0),
        "subscription_active": user.get("subscription_active", False),
        "checkout_urls": {
            "backpack": f"https://modelhub-api.lemonsqueezy.com/checkout/buy/1674045?checkout[custom][user_id]={request.user_id}",
            "launch": f"https://modelhub-api.lemonsqueezy.com/checkout/buy/1674083?checkout[custom][user_id]={request.user_id}",
        }
    })


@app.route("/v1/account/upgrade", methods=["POST"])
@require_api_key
def upgrade_plan():
    body = request.get_json(silent=True) or {}
    plan = body.get("plan", "")
    
    if plan not in PLANS:
        return jsonify({"error": {"message": f"Unknown plan: {plan}", "type": "invalid_request", "code": 400}}), 400
    
    variant_map = {"backpack": 1674045, "launch": 1674083}
    variant_id = variant_map.get(plan)
    checkout_url = f"https://modelhub-api.lemonsqueezy.com/checkout/buy/{variant_id}?checkout[custom][user_id]={request.user_id}"
    
    return jsonify({
        "checkout_url": checkout_url,
        "plan": plan,
        "price": PLANS[plan]["price"],
        "currency": "USD"
    })


@app.route("/v1/account/topup", methods=["POST"])
@require_api_key
def topup():
    body = request.get_json(silent=True) or {}
    amount = body.get("amount")
    
    valid_amounts = {5: 1674087, 25: 1674096, 100: 1674097}
    if amount not in valid_amounts:
        return jsonify({"error": {"message": "Invalid amount. Choose $5, $25, or $100.", "type": "invalid_request", "code": 400}}), 400
    
    variant_id = valid_amounts[amount]
    checkout_url = f"https://modelhub-api.lemonsqueezy.com/checkout/buy/{variant_id}?checkout[custom][user_id]={request.user_id}"
    
    return jsonify({
        "checkout_url": checkout_url,
        "amount": amount,
        "currency": "USD"
    })


# ===== Dashboard 静态页面 =====

@app.route("/dashboard")
@app.route("/dashboard.html")
def dashboard_page():
    if SERVE_STATIC:
        return send_from_directory(STATIC_DIR, "dashboard.html")
    return jsonify({"error": "Static not enabled"}), 404


# ===== 注册 & 登录 (无需API Key) =====

@app.route("/v1/auth/signup", methods=["POST"])
def auth_signup():
    """注册新用户，自动生成 API Key，赠送 $5 免费额度"""
    body = request.get_json(silent=True) or {}
    email = (body.get("email") or "").strip().lower()
    
    if not email or "@" not in email:
        return jsonify({"error": {"message": "Valid email is required", "type": "validation_error", "code": 400}}), 400
    
    users = load_users()
    
    # Check duplicate email
    for uid, info in users.items():
        if info.get("email", "").lower() == email:
            return jsonify({"error": {"message": "Email already registered. Please login instead.", "type": "duplicate_email", "code": 409}}), 409
    
    user_id = uuid.uuid4().hex[:16]
    key_id = uuid.uuid4().hex[:8]
    api_key = f"mh-sk-{uuid.uuid4().hex[:32]}"
    
    users[user_id] = {
        "email": email,
        "api_key": api_key,  # 旧格式兼容
        "api_keys": [
            {"id": key_id, "key": api_key, "name": "Default", "created_at": time.time(), "last_used": 0, "revoked": False}
        ],
        "balance": 5.0,
        "total_spent": 0,
        "total_requests": 0,
        "created_at": time.time(),
        "status": "active",
        "plan": "free",
        "subscription_active": False,
        "monthly_tokens_used": 0,
        "monthly_reset_at": 0,
        "total_deposited": 5.0
    }
    
    save_users(users)
    
    return jsonify({
        "user_id": user_id,
        "api_key": api_key,
        "email": email,
        "balance": 5.0,
        "message": "Welcome! $5 free credits added to your account."
    }), 201


@app.route("/v1/auth/login", methods=["POST"])
def auth_login():
    """通过邮箱+API Key登录"""
    body = request.get_json(silent=True) or {}
    email = (body.get("email") or "").strip().lower()
    api_key = (body.get("api_key") or "").strip()
    
    users = load_users()
    for uid, info in users.items():
        if info.get("email", "").lower() == email:
            if info.get("api_key") == api_key:
                return jsonify({"user_id": uid, "email": email, "message": "Logged in"})
            for k in info.get("api_keys", []):
                if k.get("key") == api_key and not k.get("revoked"):
                    return jsonify({"user_id": uid, "email": email, "message": "Logged in"})
    
    return jsonify({"error": {"message": "Invalid email or API key", "type": "auth_error", "code": 401}}), 401


# ===== API Key 管理 =====

@app.route("/v1/account/keys", methods=["GET"])
@require_api_key
def list_api_keys():
    """列出用户的所有 API Key"""
    user = request.user
    keys = user.get("api_keys", [])
    # 如果有旧格式的 api_key 但不在 keys 里，补进去
    old_key = user.get("api_key", "")
    if old_key and not any(k.get("key") == old_key for k in keys):
        keys.insert(0, {"id": "default", "key": old_key[:16] + "...", "name": "Default", "created_at": user.get("created_at", 0), "last_used": 0, "revoked": False, "truncated": True})
    
    # Sanitize: never send full key back (except newly created ones)
    safe_keys = []
    for k in keys:
        safe_k = dict(k)
        if not k.get("truncated"):
            safe_k["key"] = k["key"][:16] + "..."
        safe_keys.append(safe_k)
    
    return jsonify({"keys": safe_keys})


@app.route("/v1/account/keys", methods=["POST"])
@require_api_key
def create_api_key():
    """创建新的 API Key"""
    body = request.get_json(silent=True) or {}
    name = (body.get("name") or "New Key").strip()
    
    users = load_users()
    user = users.get(request.user_id, {})
    
    # Check key limit by plan
    plan = user.get("plan", "free")
    max_keys = PLANS.get(plan, {}).get("max_keys", 1)
    existing = len(user.get("api_keys", []))
    if existing >= max_keys:
        return jsonify({"error": {"message": f"Key limit reached ({max_keys} max for {plan} plan). Upgrade to create more.", "type": "key_limit", "code": 403}}), 403
    
    key_id = uuid.uuid4().hex[:8]
    new_key = f"mh-sk-{uuid.uuid4().hex[:32]}"
    
    if "api_keys" not in users[request.user_id]:
        # migrate old format: keep existing key
        old_key = users[request.user_id].get("api_key", "")
        users[request.user_id]["api_keys"] = [
            {"id": "default", "key": old_key, "name": "Default", "created_at": users[request.user_id].get("created_at", 0), "last_used": 0, "revoked": False}
        ]
    
    users[request.user_id]["api_keys"].append({
        "id": key_id,
        "key": new_key,
        "name": name,
        "created_at": time.time(),
        "last_used": 0,
        "revoked": False
    })
    save_users(users)
    
    return jsonify({"id": key_id, "key": new_key, "name": name}), 201


@app.route("/v1/account/keys/<key_id>", methods=["DELETE"])
@require_api_key
def revoke_api_key(key_id):
    """撤销 API Key"""
    users = load_users()
    if request.user_id not in users:
        return jsonify({"error": "User not found"}), 404
    
    keys = users[request.user_id].get("api_keys", [])
    for k in keys:
        if k.get("id") == key_id:
            k["revoked"] = True
            save_users(users)
            return jsonify({"status": "revoked", "id": key_id})
    
    return jsonify({"error": "Key not found"}), 404


# ===== 管理API =====

@app.route("/v1/admin/users", methods=["POST"])
def admin_create_user():
    auth = request.headers.get("Authorization", "")
    if auth != f"Bearer {ADMIN_API_KEY}":
        return jsonify({"error": "Unauthorized"}), 401
    
    body = request.get_json(silent=True) or {}
    email = body.get("email", f"user_{uuid.uuid4().hex[:8]}@modelhub-api.com")
    initial_balance = float(body.get("initial_balance", 5.0))
    
    users = load_users()
    user_id = uuid.uuid4().hex[:16]
    key_id = uuid.uuid4().hex[:8]
    api_key = f"mh-sk-{uuid.uuid4().hex[:32]}"
    
    users[user_id] = {
        "email": email,
        "api_key": api_key,
        "api_keys": [
            {"id": key_id, "key": api_key, "name": "Default", "created_at": time.time(), "last_used": 0, "revoked": False}
        ],
        "balance": initial_balance,
        "total_spent": 0,
        "total_requests": 0,
        "created_at": time.time(),
        "status": "active",
        "plan": "free",
        "subscription_active": False,
        "monthly_tokens_used": 0,
        "monthly_reset_at": 0,
        "total_deposited": initial_balance
    }
    
    save_users(users)
    
    return jsonify({
        "user_id": user_id,
        "api_key": api_key,
        "email": email,
        "balance": initial_balance
    }), 201


@app.route("/v1/admin/balance/<user_id>", methods=["POST"])
def admin_add_balance(user_id):
    auth = request.headers.get("Authorization", "")
    if auth != f"Bearer {ADMIN_API_KEY}":
        return jsonify({"error": "Unauthorized"}), 401
    
    body = request.get_json(silent=True) or {}
    amount = float(body.get("amount", 0))
    
    users = load_users()
    if user_id not in users:
        return jsonify({"error": "User not found"}), 404
    
    users[user_id]["balance"] = round(users[user_id]["balance"] + amount, 6)
    save_users(users)
    
    return jsonify({
        "user_id": user_id,
        "new_balance": users[user_id]["balance"],
        "added": amount
    })


@app.route("/v1/admin/users", methods=["GET"])
def admin_list_users():
    auth = request.headers.get("Authorization", "")
    if auth != f"Bearer {ADMIN_API_KEY}":
        return jsonify({"error": "Unauthorized"}), 401
    
    users = load_users()
    result = []
    for uid, info in users.items():
        result.append({
            "user_id": uid,
            "email": info.get("email", ""),
            "balance": info.get("balance", 0),
            "total_spent": info.get("total_spent", 0),
            "total_requests": info.get("total_requests", 0),
            "created_at": info.get("created_at", 0),
            "plan": info.get("plan", "free"),
            "api_key_count": len(info.get("api_keys", [])),
        })
    
    return jsonify({"users": result})


# ===== =====

if __name__ == "__main__":
    print("=" * 50)
    print("ModelHub API Server")
    print("=" * 50)
    print()
    print("DeepSeek API Key: " + DEEPSEEK_API_KEY[:8] + "...")
    print("Serve static HTML: ", SERVE_STATIC)
    print()
    
    if not os.path.exists(USERS_FILE) or os.path.getsize(USERS_FILE) < 10:
        users = {}
        default_key = "mh-sk-tes" + "t-ke" + "y-please-change-in-production"
        users["admin"] = {"email": "admin@modelhub-api.com", "api_key": default_key, "balance": 15.0, "total_spent": 0, "total_requests": 0, "created_at": time.time(), "status": "active"}
        save_users(users)
        print(f"Created default test user - API Key: {default_key} ($15)")
    
    print("Endpoints:")
    print(f"  GET  /                    — Website")
    print(f"  POST /v1/chat/completions — Chat")
    print(f"  GET  /v1/models           — Models")
    print(f"  GET  /v1/account          — Account/plan")
    print(f"  POST /v1/account/upgrade  — Upgrade")
    print(f"  POST /v1/account/topup    — Top up")
    print(f"  POST /v1/auth/signup       — Sign up (email → API key)")
    print(f"  POST /v1/auth/login        — Login")
    print(f"  GET  /v1/account/keys      — List API keys")
    print(f"  POST /v1/account/keys      — Create API key")
    print(f"  DELETE /v1/account/keys/id — Revoke API key")
    print(f"  GET  /dashboard            — Dashboard")
    print(f"  POST /webhook/lemon-squeezy — Payments")
    print(f"  GET  /v1/admin/users       — Admin")
    print()
    print("Plans: Backpack $15/mo (100M tokens), Launch $65/mo (500M tokens)")
    print(f"Store ID: {LEMONSQUEEZY_STORE_ID}")
    print()
    print("Starting on 0.0.0.0:18080")
    app.run(host="0.0.0.0", port=18080, debug=True)
