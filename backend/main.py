from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import hmac
import hashlib
import json
import os
import sqlite3
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Code Reviewer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

fail_counts = {}


# ─── Signature verification ────────────────────────────────────────────────────

def verify_signature(payload: bytes, sig_header: str) -> bool:
    secret = os.getenv("GITHUB_WEBHOOK_SECRET", "").encode()
    expected = "sha256=" + hmac.new(secret, payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, sig_header)


# ─── Webhook ───────────────────────────────────────────────────────────────────

@app.post("/webhook")
async def webhook(request: Request):
    payload_bytes = await request.body()
    sig = request.headers.get("X-Hub-Signature-256", "")
    client_ip = request.client.host

    if fail_counts.get(client_ip, 0) >= 3:
        raise HTTPException(status_code=403, detail="Blocked after 3 failures")

    if not verify_signature(payload_bytes, sig):
        fail_counts[client_ip] = fail_counts.get(client_ip, 0) + 1
        raise HTTPException(status_code=403, detail="Invalid signature")

    fail_counts[client_ip] = 0
    payload = json.loads(payload_bytes)
    event_type = request.headers.get("X-GitHub-Event", "")
    action = payload.get("action", "")

    if event_type == "pull_request" and action in ["opened", "synchronize", "reopened"]:
        from backend.celery_app import process_pr
        process_pr.delay(payload)
        return {"status": "queued", "action": action}

    elif event_type == "issue_comment" and action == "created":
        comment_body = payload.get("comment", {}).get("body", "")
        commenter = payload.get("comment", {}).get("user", {}).get("login", "")
        repo_name = payload["repository"]["full_name"]
        issue = payload.get("issue", {})
        pr_number = issue.get("number")
        bot_name = os.getenv("BOT_NAME", "")

        if pr_number and "pull_request" in issue and commenter != bot_name:
            from agents.agent_f import run as run_f
            run_f(repo_name, pr_number, comment_body, commenter)
            return {"status": "debate_triggered"}

    return {"status": "ignored", "event": event_type, "action": action}


# ─── Health ────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "running"}


# ─── GitHub App Install Flow ───────────────────────────────────────────────────

@app.get("/install")
async def install():
    app_name = os.getenv("GITHUB_APP_NAME", "code-reviewer-bot")
    return {"install_url": f"https://github.com/apps/{app_name}/installations/new"}


@app.get("/callback")
async def callback(installation_id: int, setup_action: str = ""):
    from storage.database import DB_PATH
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO installations VALUES (NULL,?,?,?)",
        (installation_id, "unknown", datetime.now().isoformat())
    )
    conn.commit()
    conn.close()
    return {"status": "installed", "installation_id": installation_id}


# ─── Dashboard API Endpoints ───────────────────────────────────────────────────

@app.get("/api/developer/{username}")
def dev_profile_api(username: str):
    from storage.database import get_patterns
    patterns = get_patterns(username)
    return {
        "developer": username,
        "patterns": [{"category": c, "count": n} for c, n in patterns],
        "total_flags": sum(n for _, n in patterns)
    }


@app.get("/api/drift/{repo_name:path}")
def drift_api(repo_name: str):
    from storage.database import DB_PATH
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT snapshot, created_at FROM architecture_snapshots WHERE repo=? ORDER BY created_at DESC LIMIT 1",
        (repo_name,)
    )
    row = c.fetchone()
    conn.close()
    return {
        "repo": repo_name,
        "snapshot": row[0] if row else "None",
        "at": row[1] if row else "Never"
    }


@app.get("/api/prs/{repo_name:path}")
def open_prs_api(repo_name: str):
    from storage.database import DB_PATH
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT pr_number, author, changed_files, opened_at FROM open_prs WHERE repo=?",
        (repo_name,)
    )
    rows = c.fetchall()
    conn.close()
    return {
        "open_prs": [
            {"pr": r[0], "author": r[1], "files": r[2], "opened": r[3]}
            for r in rows
        ]
    }


@app.get("/api/config")
def get_config():
    return {"threshold": 0.70, "linters": ["pylint", "flake8", "semgrep"]}


@app.post("/api/config")
async def update_config(request: Request):
    body = await request.json()
    return {"status": "updated", "config": body}
