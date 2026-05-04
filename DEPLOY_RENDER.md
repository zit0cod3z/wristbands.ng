# Deploying WristbandsNG to Render
## Step-by-step guide for testing and pitching

---

## Why Render First?
- Free HTTPS certificate (fixes camera access on mobile)
- Zero server configuration
- Deploys from GitHub in minutes
- Perfect for demos and pitching to CTO/CEO

---

## STEP 1 — Prepare Your Repository

```bash
# In your project folder (eventpro/)
cd eventpro

# Initialise git if not already done
git init
git add .
git commit -m "WristbandsNG initial deployment"

# Create a GitHub repository at github.com
# Then connect it:
git remote add origin https://github.com/YOUR_USERNAME/wristbandsng.git
git branch -M main
git push -u origin main
```

**Important — make sure these files are NOT in .gitignore:**
- `requirements.txt` ✓
- `build.sh` ✓
- `render.yaml` ✓

**Make sure these ARE in .gitignore:**
- `.env` ✓ (never commit secrets)
- `db.sqlite3` ✓
- `media/` ✓ (except .gitkeep files)

---

## STEP 2 — Create Render Account

1. Go to **render.com** → Sign Up (free)
2. Connect your GitHub account
3. Click **New** → **Web Service**
4. Select your `wristbandsng` repository
5. Render auto-detects `render.yaml` — click **Create Web Service**

---

## STEP 3 — Set Environment Variables

In Render dashboard → your service → **Environment** tab, add:

| Key | Value |
|-----|-------|
| `SECRET_KEY` | Generate: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` |
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | `*.onrender.com` |
| `HTTPS` | `True` |
| `CSRF_TRUSTED_ORIGINS` | `https://wristbandsng.onrender.com` |
| `CORS_ORIGINS` | `https://wristbandsng.onrender.com` |
| `EMAIL_HOST_USER` | `kizdakus@gmail.com` |
| `EMAIL_HOST_PASSWORD` | `your_gmail_app_password` |
| `DEFAULT_FROM_EMAIL` | `WristbandsNG <kizdakus@gmail.com>` |
| `GOD_USERNAME` | `your_secret_username` |
| `GOD_PASSWORD` | `YourStrongPassword@2025!` |

---

## STEP 4 — Create Superuser on Render

After first deploy, go to Render dashboard → your service → **Shell** tab:

```bash
python manage.py createsuperuser
```

Enter username, email, password when prompted.

---

## STEP 5 — Your Live URLs

After deploy (takes 3-5 minutes):

| Page | URL |
|------|-----|
| Homepage | `https://wristbandsng.onrender.com/` |
| Admin Login | `https://wristbandsng.onrender.com/accounts/login/` |
| Dashboard | `https://wristbandsng.onrender.com/dashboard/` |
| Check-in | `https://wristbandsng.onrender.com/checkin/` |
| QR Scanner | `https://wristbandsng.onrender.com/checkin/<event-id>/pwa/` |

---

## STEP 6 — Test the QR Scanner on Your Phone

1. Open `https://wristbandsng.onrender.com/checkin/` on your phone
2. Log in with your admin credentials
3. Select your event → Open Scanner
4. Allow camera access
5. Scan a guest's QR code — it checks them in instantly ✓

---

## IMPORTANT RENDER LIMITATIONS (Free Tier)

| Limitation | Impact | Solution |
|------------|--------|----------|
| Spins down after 15 min inactivity | First request takes ~30s | Upgrade to $7/month paid plan |
| Ephemeral disk | Uploaded images reset on redeploy | Add Render Disk ($1/month) or use Cloudinary |
| 512MB RAM | Fine for demos | Upgrade for production |
| No custom domain on free | URL is `.onrender.com` | Upgrade to add your domain |

**For your CTO/CEO pitch:** Use the free tier for the demo. The $7/month paid plan removes all limitations.

---

## TROUBLESHOOTING

**Build fails:**
```bash
# Check build.sh is executable
chmod +x build.sh
git add build.sh
git commit -m "fix build.sh permissions"
git push
```

**500 error after deploy:**
- Check Render logs (dashboard → Logs tab)
- Most common cause: missing environment variable
- Ensure `SECRET_KEY` is set

**Images not showing:**
- On Render free tier, uploaded images are ephemeral
- Re-upload after each deploy, or add a Render Disk

**WebSocket not connecting:**
- Render supports WebSockets on paid plans
- On free tier, real-time updates fall back to polling (every 8-15 seconds) — still works
