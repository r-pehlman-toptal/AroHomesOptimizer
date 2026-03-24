# Deployment guide — Aro Homes

Covers **local `.env`**, **Docker**, and **Fly.io** using `Dockerfile`, `.dockerignore`, and `fly.toml`.

---

## Table of contents

1. [Environment variables](#1-environment-variables)
2. [Run locally](#2-run-locally)
3. [Docker (optional)](#3-docker-optional)
4. [Fly.io — setup & deploy](#4-flyio--setup--deploy)
5. [URLs](#5-urls)
6. [Troubleshooting](#6-troubleshooting)

---

## 1. Environment variables

| Variable | Purpose |
|----------|--------|
| `DB_URL` or `DATABASE_URL` | Postgres (required for DB-backed API routes). See `.env.example`. |
| `ATTOM_API_KEY` | Optional — Attom parcel/address features. |

**Local:** Copy `.env.example` → **`.env`** at the **repo root** (gitignored).

**Loaded by:** `src/api/main.py` and `src/db/connection.py` via `load_dotenv()`.

**Production (Fly):** Do **not** put secrets in Git. Use:

```bash
fly secrets set DB_URL="postgresql+psycopg2://..."
fly secrets set ATTOM_API_KEY="your_key"
```

Or `fly secrets import < .env` from a **local** file (never commit).

---

## 2. Run locally

```bash
cd "/path/to/Aro Homes"
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Ensure **`.env`** exists, then from **repo root**:

```bash
uvicorn src.api.main:app --reload
```

- http://127.0.0.1:8000/health  
- http://127.0.0.1:8000/docs  
- http://127.0.0.1:8000/app  

---

## 3. Docker (optional)

```bash
docker build -t aro-homes .
docker run --rm -p 8080:8080 -e PORT=8080 \
  -e DB_URL="postgresql+psycopg2://..." \
  aro-homes
```

`.dockerignore` excludes `.env` so secrets are not baked into the image.

---

## 4. Fly.io — setup & deploy

1. Install [flyctl](https://fly.io/docs/hands-on/install-flyctl/) · `fly auth login`

2. **Create the app** (first time only):

   ```bash
   fly launch
   ```

   Use existing `Dockerfile` / `fly.toml` when prompted. If **`aro-homes`** is taken, pick a unique name and set `app = "..."` in **`fly.toml`**.

3. **Secrets:**

   ```bash
   fly secrets set DB_URL="postgresql+psycopg2://..."
   ```

4. **Deploy:**

   ```bash
   fly deploy
   ```

5. Logs: `fly logs` · Status: `fly status`

**Account issues:** If Fly shows “high risk”, complete verification at https://fly.io/high-risk-unlock

---

## 5. URLs

Replace `your-app` with the `app` name in **`fly.toml`**:

| URL | Purpose |
|-----|--------|
| `https://your-app.fly.dev/health` | Health check |
| `https://your-app.fly.dev/docs` | API docs |
| `https://your-app.fly.dev/app` | Web UI |

---

## 6. Troubleshooting

| Issue | Fix |
|--------|-----|
| **Could not find App** | Run `fly launch` or `fly apps create <name>`; match `app` in `fly.toml`. |
| **Database URL not configured** | `fly secrets set DB_URL=...` |
| **502** | `fly logs` — check port 8080, `internal_port` in `fly.toml`. |
| **Build fails (geopandas)** | Dockerfile installs GDAL/GEOS/PROJ; adjust `apt` if pip still fails. |
| **OOM** | Increase `[[vm]]` memory in `fly.toml` or `fly scale memory`.

---

## Quick reference

```bash
fly auth login
fly launch          # first time
fly secrets set DB_URL="..."
fly deploy
```

After **GitHub** updates: `git pull` then **`fly deploy`** (unless CI deploys for you).
