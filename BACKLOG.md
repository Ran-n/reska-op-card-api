# Backlog

## Index

| # | Item | Section |
|---|---|---|
| 1 | Add colour and rarity filters to `GET /cards/` | [Cards router](#cards-router) |
| 2 | Add `Promo` set type seed row | [Data](#data) |
| 3 | HTTPS in production via Certbot + uvicorn | [Infrastructure](#infrastructure) |

---

## Data

### 2 — Add `Promo` set type seed row

Reska's Collection tab has Promo and Other sub-tabs. `Promo` and `Other` rows need to exist in the `set_type` table.

---

## Cards router

### 1 — Add colour and rarity filters to `GET /cards/`

`GET /cards/` currently accepts `name`, `set_id`, and `cardtype_id` only.
Reska's Browse tab needs to filter by colour and rarity as well.

**Required query params to add:**
- `color_id: int | None` — filter by colour (via `card_color` junction)
- `rarity_id: int | None` — filter by rarity (via `card.rarity_fk`)

Both should be optional and composable with existing filters.

---

## Infrastructure

### 3 — HTTPS in production via Certbot + uvicorn

**Context:** Locally, HTTPS is handled by mkcert — self-signed certs trusted by the local OS, loaded by uvicorn via `SSL_CERTFILE`/`SSL_KEYFILE` in `.env`. In production on a real server with a public domain, mkcert certs won't work (they're only trusted on the machine that generated them). A real CA-issued cert is needed.

**Problem:** Without HTTPS in production, HTTP Basic auth credentials for `/admin/keys` are sent in cleartext — base64 is not encryption.

**Solution:** Use Certbot to get a free, publicly trusted cert from Let's Encrypt, then point uvicorn at it.

**Prerequisites:**
- A Linux/Mac server (Certbot doesn't support Windows well)
- A real domain pointing at the server's public IP (e.g. `api.reska.com`)
- Ports 80 and 443 open in the firewall

**Steps:**

1. Install Certbot on the server:
   ```
   sudo apt install certbot
   ```

2. Issue a cert (standalone mode — Certbot temporarily spins up its own HTTP server on port 80 to prove domain ownership to Let's Encrypt):
   ```
   sudo certbot certonly --standalone -d api.reska.com
   ```
   Cert and key land at:
   - `/etc/letsencrypt/live/api.reska.com/fullchain.pem`
   - `/etc/letsencrypt/live/api.reska.com/privkey.pem`

3. Set in `.env` on the production server:
   ```
   SSL_CERTFILE=/etc/letsencrypt/live/api.reska.com/fullchain.pem
   SSL_KEYFILE=/etc/letsencrypt/live/api.reska.com/privkey.pem
   ```
   The CLI already reads these and passes them to uvicorn — no other code changes needed.

4. Auto-renewal: Let's Encrypt certs expire every 90 days. Set up a cron job:
   ```
   0 3 * * * certbot renew --quiet && systemctl restart reska-op-card-api
   ```
   (Adjust the restart command to however the service is managed — systemd unit, pm2, etc.)

**Note:** Certbot needs port 80 open during renewal for the HTTP challenge. If uvicorn is already using port 80 (unlikely — it defaults to 8000), use `--webroot` mode instead of `--standalone`.

---
