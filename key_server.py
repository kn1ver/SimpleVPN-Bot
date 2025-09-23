
"""
One-time activation key server for x-ui + client program.

FastAPI server that:
- Allows admin to generate one-time keys
- Accepts activation requests from client programs:
    POST /activate { "key": "...", "fingerprint": "optional-device-id" }
  On successful activation:
    - calls x-ui API to create a client (UUID)
    - marks the key as used and saves metadata
    - returns the generated connection string (vless://...) or full config JSON

Configuration via environment variables:
- XUI_URL (eg http://127.0.0.1:54321)
- XUI_USER
- XUI_PASS
- INBOUND_ID (integer)
- ADMIN_SECRET (simple auth for key generation)
- SERVER_HOSTNAME (public hostname used in vless link)
- LISTEN_PORT (port to run this FastAPI app)

This is a simple reference implementation. Use HTTPS in production and secure the admin endpoint.
"""

import os
import uuid
import sqlite3
import time
from datetime import datetime, timedelta
from typing import Optional
import requests
from fastapi import FastAPI, HTTPException, Body, Depends, Header
from pydantic import BaseModel

DB_PATH = os.environ.get("KEY_DB", "key_server.db")
XUI_URL = os.environ.get("XUI_URL", "http://127.0.0.1:54321")
XUI_USER = os.environ.get("XUI_USER", "admin")
XUI_PASS = os.environ.get("XUI_PASS", "admin")
INBOUND_ID = int(os.environ.get("INBOUND_ID", "1"))
ADMIN_SECRET = os.environ.get("ADMIN_SECRET", "changeme")
SERVER_HOSTNAME = os.environ.get("SERVER_HOSTNAME", "your.server.com")
# optional: port the x-ui inbound is listening on override
XUI_PUBLIC_PORT = os.environ.get("XUI_PUBLIC_PORT", None)  # if not set, use inbound.port

app = FastAPI(title="One-time Key Activation Server")

def ensure_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS keys (
        key TEXT PRIMARY KEY,
        status TEXT,
        created_at INTEGER,
        expires_at INTEGER,
        used_at INTEGER,
        used_by TEXT,
        xui_client_id TEXT,
        xui_inbound_id INTEGER,
        metadata TEXT
    )
    """)
    conn.commit()
    conn.close()

ensure_db()

def add_key_to_db(k: str, ttl_seconds: Optional[int]):
    now = int(time.time())
    exp = None
    if ttl_seconds:
        exp = now + int(ttl_seconds)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO keys (key, status, created_at, expires_at) VALUES (?, ?, ?, ?)",
              (k, "unused", now, exp))
    conn.commit()
    conn.close()

def mark_key_used(k: str, fingerprint: str, xui_client_id: str, inbound_id:int, metadata:Optional[str]=None):
    now = int(time.time())
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""UPDATE keys SET status = ?, used_at = ?, used_by = ?, xui_client_id = ?, xui_inbound_id = ?, metadata = ? WHERE key = ?""",
              ("used", now, fingerprint, xui_client_id, inbound_id, metadata, k))
    conn.commit()
    conn.close()

def get_key_row(k: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT key, status, created_at, expires_at, used_at, used_by, xui_client_id, xui_inbound_id, metadata FROM keys WHERE key = ?", (k,))
    row = c.fetchone()
    conn.close()
    return row

class GenerateKeyRequest(BaseModel):
    count: int = 1
    ttl_seconds: Optional[int] = None  # how long key is valid for activation

class ActivateRequest(BaseModel):
    key: str
    fingerprint: Optional[str] = None

# --- X-UI helper functions ---

_session = requests.Session()
def xui_login():
    # login to x-ui, session cookie will be stored in _session
    r = _session.post(f"{XUI_URL}/login", json={"username": XUI_USER, "password": XUI_PASS}, timeout=10)
    r.raise_for_status()
    return True

def xui_get_inbound(inbound_id:int):
    r = _session.get(f"{XUI_URL}/xui/API/inbounds/get/{inbound_id}", timeout=10)
    r.raise_for_status()
    return r.json()

def xui_add_client(inbound_id:int, client_uuid:str, email:str):
    # This uses the documented endpoint /addClient/ (POST)
    payload = {
        "id": inbound_id,
        "settings": {
            "clients": [
                {
                    "id": client_uuid,
                    "email": email,
                    "enable": True
                }
            ]
        }
    }
    r = _session.post(f"{XUI_URL}/xui/API/inbounds/addClient/", json=payload, timeout=10)
    r.raise_for_status()
    return r.json()

def build_vless_from_inbound(inbound_json, client_uuid:str, email:str):
    # inbound_json assumed to be result of xui_get_inbound()['obj'] or similar
    # Try to be robust about structure
    if isinstance(inbound_json, dict) and "obj" in inbound_json:
        obj = inbound_json["obj"]
    else:
        obj = inbound_json

    port = obj.get("port")
    stream = obj.get("streamSettings", {})
    proto = obj.get("protocol", "vless")
    # reality settings are usually in streamSettings -> realitySettings
    reality = stream.get("realitySettings") or stream.get("reality")
    sni = ""
    pbk = ""
    sid = ""
    if reality:
        sni_list = reality.get("serverNames") or reality.get("serverName") or []
        if isinstance(sni_list, list) and len(sni_list)>0:
            sni = sni_list[0]
        elif isinstance(sni_list, str):
            sni = sni_list
        pbk = reality.get("publicKey") or reality.get("public-key") or reality.get("public_key") or ""
        short_ids = reality.get("shortIds") or reality.get("shortId") or []
        if isinstance(short_ids, list) and len(short_ids)>0:
            sid = short_ids[0]
        elif isinstance(short_ids, str):
            sid = short_ids

    server = SERVER_HOSTNAME
    if XUI_PUBLIC_PORT:
        port = XUI_PUBLIC_PORT
    # Build query params for reality (common fields)
    # minimal: security=reality&pbk=...&sid=...&sni=...
    query = f"security=reality&encryption=none"
    if sni:
        query += f"&sni={sni}"
    if pbk:
        query += f"&pbk={pbk}"
    if sid:
        query += f"&sid={sid}"
    # Add flow/other if available
    flow = obj.get("flow") or ""
    if flow:
        query += f"&flow={flow}"
    # type and transport
    transport = stream.get("network") or stream.get("type") or "tcp"
    query += f"&type={transport}"
    # final link
    link = f"vless://{client_uuid}@{server}:{port}?{query}#{email}"
    return link

# --- API endpoints ---

def admin_auth(x_admin_secret: Optional[str] = Header(None)):
    if x_admin_secret != ADMIN_SECRET:
        raise HTTPException(status_code=401, detail="invalid admin secret")

@app.post("/admin/generate", dependencies=[Depends(admin_auth)])
def admin_generate(req: GenerateKeyRequest):
    created = []
    for _ in range(max(1, req.count)):
        k = str(uuid.uuid4()).replace("-", "")[:20]  # short key
        add_key_to_db(k, req.ttl_seconds)
        created.append(k)
    return {"created": created}

@app.post("/activate")
def activate(req: ActivateRequest):
    # validate key
    row = get_key_row(req.key)
    if not row:
        raise HTTPException(status_code=404, detail="key_not_found")
    key, status, created_at, expires_at, used_at, used_by, xui_client_id, xui_inbound_id, metadata = row
    now = int(time.time())
    if status != "unused":
        raise HTTPException(status_code=400, detail="key_already_used_or_invalid")
    if expires_at and now > expires_at:
        raise HTTPException(status_code=400, detail="key_expired")

    # login to x-ui
    try:
        xui_login()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"xui_login_failed: {e}")

    # create a unique client UUID and use fingerprint or key as email to identify owner
    client_uuid = str(uuid.uuid4())
    email = req.fingerprint or req.key  # using fingerprint if provided, else key

    try:
        add_res = xui_add_client(INBOUND_ID, client_uuid, email)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"xui_add_client_failed: {e}")

    # fetch inbound details to build connection string
    try:
        inbound = xui_get_inbound(INBOUND_ID)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"xui_get_inbound_failed: {e}")

    try:
        link = build_vless_from_inbound(inbound, client_uuid, email)
    except Exception as e:
        link = None

    # mark key used
    mark_key_used(req.key, req.fingerprint or "", client_uuid, INBOUND_ID, metadata=str(add_res))

    return {"status": "ok", "link": link, "client_uuid": client_uuid, "email": email}

@app.get("/admin/status", dependencies=[Depends(admin_auth)])
def admin_status():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT key, status, created_at, expires_at, used_at, used_by, xui_client_id FROM keys ORDER BY created_at DESC")
    rows = c.fetchall()
    conn.close()
    out = []
    for r in rows:
        out.append({
            "key": r[0],
            "status": r[1],
            "created_at": datetime.utcfromtimestamp(r[2]).isoformat() if r[2] else None,
            "expires_at": datetime.utcfromtimestamp(r[3]).isoformat() if r[3] else None,
            "used_at": datetime.utcfromtimestamp(r[4]).isoformat() if r[4] else None,
            "used_by": r[5],
            "xui_client_id": r[6]
        })
    return {"keys": out}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("key_server:app", host="0.0.0.0", port=int(os.environ.get("LISTEN_PORT", "8000")), reload=False)
