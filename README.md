# Parcel Privé — Privacy-Based Automated Parcel Locker Delivery System
Run: `pip install -r requirements.txt` then `streamlit run Fatima_app.py`. Without DATABASE_URL it starts in **DEMO MODE** (temporary SQLite; demo logins `admin@/seller@/rider@/customer@demo.test`, password `demo12345`, demo mode only).

## Upload to GitHub (simple)
1. github.com → New repository (e.g. `parcel-prive`), keep it Public or Private.
2. Click "uploading an existing file", drag ALL files in this folder (including the `.streamlit` folder's `secrets.toml.example`, NOT any real `secrets.toml`), then Commit.

## Deploy on Streamlit Community Cloud
1. share.streamlit.io → sign in with GitHub → Create app → pick your repo, branch `main`, main file `Fatima_app.py`.
2. Advanced settings → Secrets: paste the lines from `.streamlit/secrets.toml.example` with your real values.
3. Deploy.

## Real database
Create a free PostgreSQL (e.g. Supabase or Neon), copy its connection string into the `DATABASE_URL` secret. Tables are created automatically on first start. Set `ADMIN_EMAIL` and `ADMIN_PASSWORD` secrets to create the first admin (no default admin password exists outside demo mode). Add hubs/lockers from the Admin dashboard.

## What works / what needs more
- **Works now:** sign-up/in, scrypt hashing, role checks on the server, catalogue, cart, checkout with mandatory backup hub + consent, one order per seller, state machine with history, locker reservation at arrival (transactional), backup-hub rule, "both hubs full" handling, reservation expiry, configurable pickup deadline, expiring single-use hashed QR tokens (room and pickup), in-app notifications, audit logs.
- **Needs credentials:** PostgreSQL (permanent data). Payment provider: none connected; "verified" is a manual admin action and is labelled as such.
- **Needs the other group (Fatima_hardware.py):** QR payload format and scanner output; controller protocol/host/auth; unlock command and locker-ID mapping; success/failure confirmation and timeouts; manual-override procedure. Until then no unlock is ever claimed; collection must be completed manually by an admin.

## Limits (honest list)
Streamlit sessions live in server memory per browser tab: refreshing logs you out and there is no built-in HTTPS-cookie auth; fine for a demo, not for production. Not tested by running (Streamlit was not installed where this was written) — only Python syntax-checked. Please run the testing checklist below.

## Test checklist
Customer: sign up → add to cart → checkout needs 2 different hubs + consent → order shows delivery ID. Seller: accept → preparing → ready (no customer data shown). Rider: accept → pickup → arrive → locker assigned → report deposit. Admin: verify deposit, mark payment verified. Customer: generate pickup QR (blocked until payment verified). Admin QR tab: paste token → "NOT collected, hardware not integrated" → use manual collection. Fill all lockers of both hubs (maintenance toggle) before arrival to see "Awaiting Customer Hub".
