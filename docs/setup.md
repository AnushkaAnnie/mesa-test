# Code Reviewer — Setup Guide

## Prerequisites (install once on every laptop)

1. **Python 3.11** → [python.org](https://python.org) → Download → Install
2. **VS Code** → [code.visualstudio.com](https://code.visualstudio.com) → Download → Install
3. **Git** → [git-scm.com](https://git-scm.com) → Download → Install
4. **Ollama** → [ollama.com](https://ollama.com) → Download for your OS → Install
5. **Redis** (local):
   - Windows: download from [github.com/microsoftarchive/redis/releases](https://github.com/microsoftarchive/redis/releases)
   - Mac: `brew install redis`
   - Linux: `sudo apt install redis-server`

---

## Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/code-reviewer
cd code-reviewer
```

---

## Install Python Dependencies

```bash
pip install -r requirements.txt
```

---

## Set Up Your .env File

Copy the example file:
```bash
cp .env.example .env
```

Then fill in all the values (see **API Keys** section below).

---

## Pull the LLM Model (do once, takes ~5 minutes)

```bash
ollama pull llama3
```

---

## Initialize the Database

```bash
python storage/database.py
```

---

## Run the App (4 terminals open at the same time)

**Terminal 1 — Redis:**
```bash
redis-server
```

**Terminal 2 — Celery worker:**
```bash
celery -A backend.celery_app worker --loglevel=info
```

**Terminal 3 — FastAPI server:**
```bash
uvicorn backend.main:app --reload --port 8000
```

**Terminal 4 — ngrok (for webhook testing):**
```bash
ngrok http 8000
```

---

## API Keys — Where to Get Them

### GITHUB_TOKEN
1. Go to [github.com](https://github.com) → Settings → Developer Settings → Personal Access Tokens → Tokens (classic)
2. Click **Generate New Token (classic)**
3. Select scopes: `repo`, `pull_requests`, `issues`
4. Copy the token → paste as `GITHUB_TOKEN=ghp_xxxxxxxx`

### GITHUB_WEBHOOK_SECRET
Any random string you choose — must match what you set in your GitHub App webhook settings.
Example: `GITHUB_WEBHOOK_SECRET=my_secret_123`

### GITHUB_APP_ID
After creating a GitHub App (see below), the App ID is shown on the app's settings page.

### VOYAGE_API_KEY
1. Go to [voyageai.com](https://voyageai.com) → Sign up → API Keys → Create key
2. Paste as `VOYAGE_API_KEY=pa-xxxxxxxx`

### PINECONE_API_KEY
1. Go to [pinecone.io](https://pinecone.io) → Sign up (free) → API Keys → Copy default key
2. Create an index named **past-prs** with **dimension 1024**
3. Paste as `PINECONE_API_KEY=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`

### REDIS_URL
If running Redis locally: `REDIS_URL=redis://localhost:6379/0`
On Railway: Railway auto-sets this for you.

### BOT_NAME
The GitHub username of your GitHub App bot (ends in `[bot]`).
Example: `BOT_NAME=code-reviewer-bot[bot]`

---

## Create the GitHub App

1. Go to [github.com](https://github.com) → Settings → Developer Settings → GitHub Apps → **New GitHub App**
2. Fill in:
   - **Name:** `Code Reviewer Bot`
   - **Homepage URL:** `http://localhost:8000`
   - **Webhook URL:** your ngrok URL + `/webhook` (e.g. `https://abc123.ngrok.io/webhook`)
   - **Webhook Secret:** same as your `GITHUB_WEBHOOK_SECRET`
3. Permissions:
   - Pull Requests → **Read & Write**
   - Issues → **Read & Write**
   - Contents → **Read**
4. Subscribe to events: **Pull Request**, **Issue comment**
5. Click **Create GitHub App**
6. Download the **Private Key PEM** → save as `github_app.pem` in the project root
7. Copy the **App ID** → add to `.env` as `GITHUB_APP_ID=`
8. Install the app on your test repository

---

## Daily Git Workflow (everyone does this)

**Morning (before touching any code):**
```bash
git pull
```

**End of day (before 3 PM):**
```bash
git add .
git commit -m "May 5 - YourName - what you did"
git push
```

---

## Deploy to Railway

1. Go to [railway.app](https://railway.app) → sign in with GitHub → **New Project** → Deploy from GitHub → select `code-reviewer`
2. Add a **Redis** database: + New → Database → Redis
3. Go to **Variables** → add all your `.env` values
4. Railway deploys automatically. Copy the deployment URL.
5. Update your GitHub App Webhook URL to the Railway URL + `/webhook`

## Deploy Dashboard to Vercel

```bash
cd dashboard
```
1. Go to [vercel.com](https://vercel.com) → New Project → select `code-reviewer` → set root to `dashboard`
2. Add environment variable: `REACT_APP_API_URL=your_railway_url`
3. Deploy → done!
