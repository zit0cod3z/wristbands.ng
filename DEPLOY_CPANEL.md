# Deploying WristbandsNG to cPanel (wristbands.ng)
## Production deployment guide

---

## OVERVIEW

cPanel shared hosting does NOT support Django directly.
You need a **VPS** (Virtual Private Server) or **cPanel with Python support**.

### Option A — cPanel with Python App (Recommended for beginners)
Some cPanel hosts support Python apps via Passenger WSGI.
Check if your host has "Setup Python App" in cPanel.

### Option B — VPS via cPanel/WHM (Recommended for production)
A VPS gives you full control. NameCheap, Hostinger, and DigitalOcean all offer VPS.

---

## OPTION A — cPanel Python App (if your host supports it)

### Step 1 — Check Python Support
Log into cPanel → look for **"Setup Python App"** in the Software section.
If it's there, your host supports Python.

### Step 2 — Create Python App
1. Click **Setup Python App**
2. Python version: **3.11** (or highest available)
3. Application root: `wristbandsng`
4. Application URL: your domain
5. Application startup file: `eventpro/wsgi.py`
6. Application Entry point: `application`
7. Click **Create**

### Step 3 — Upload Files
Use cPanel File Manager or FTP to upload your project files to the application root.

### Step 4 — Install Dependencies
In cPanel Python App → click **Run pip install** → paste:
```
Django==5.2
daphne==4.1.2
channels==4.1.0
Pillow==11.1.0
qrcode==8.0
django-crispy-forms==2.3
crispy-bootstrap5==2024.10
openpyxl==3.1.5
gunicorn==23.0.0
django-cors-headers==4.6.0
whitenoise==6.8.2
django-axes==7.0.1
mysqlclient==2.2.4
```

### Step 5 — Create MySQL Database
1. cPanel → **MySQL Databases**
2. Create database: `wristbandsng_db`
3. Create user: `wbng_user` with strong password
4. Add user to database with ALL PRIVILEGES

### Step 6 — Configure .env
Upload `.env` file with production values (see `.env.production.example`)

### Step 7 — Run Migrations
In cPanel Python App → Terminal:
```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput
```

---

## OPTION B — VPS Deployment (Full Production)

### Prerequisites
- VPS with Ubuntu 22.04 (minimum 1GB RAM)
- SSH access
- Domain pointed to VPS IP

### Step 1 — Connect to VPS
```bash
ssh root@YOUR_VPS_IP
```

### Step 2 — Install System Dependencies
```bash
apt update && apt upgrade -y
apt install -y python3.11 python3.11-venv python3-pip nginx mysql-server git
```

### Step 3 — Create App User
```bash
useradd -m -s /bin/bash wbng
su - wbng
```

### Step 4 — Clone Your Repository
```bash
git clone https://github.com/YOUR_USERNAME/wristbandsng.git
cd wristbandsng/eventpro
```

### Step 5 — Set Up Python Environment
```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 6 — Configure Environment
```bash
cp .env.production.example .env
nano .env   # fill in all values
```

### Step 7 — Set Up MySQL
```bash
mysql -u root -p
CREATE DATABASE wristbandsng_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'wbng_user'@'localhost' IDENTIFIED BY 'StrongPassword123!';
GRANT ALL PRIVILEGES ON wristbandsng_db.* TO 'wbng_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### Step 8 — Run Migrations
```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput
mkdir -p media/qrcodes media/event_banners media/avatars
```

### Step 9 — Create Systemd Service
```bash
# As root:
cat > /etc/systemd/system/wristbandsng.service << EOF
[Unit]
Description=WristbandsNG Daphne ASGI Server
After=network.target

[Service]
User=wbng
Group=wbng
WorkingDirectory=/home/wbng/wristbandsng/eventpro
Environment="PATH=/home/wbng/wristbandsng/eventpro/venv/bin"
ExecStart=/home/wbng/wristbandsng/eventpro/venv/bin/daphne \
    -b 127.0.0.1 \
    -p 8000 \
    eventpro.asgi:application
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable wristbandsng
systemctl start wristbandsng
systemctl status wristbandsng
```

### Step 10 — Configure Nginx
```bash
cat > /etc/nginx/sites-available/wristbandsng << EOF
server {
    listen 80;
    server_name wristbands.ng www.wristbands.ng;
    return 301 https://\$host\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name wristbands.ng www.wristbands.ng;

    ssl_certificate     /etc/letsencrypt/live/wristbands.ng/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/wristbands.ng/privkey.pem;
    ssl_protocols       TLSv1.2 TLSv1.3;

    # Static files — served directly by Nginx (fast)
    location /static/ {
        alias /home/wbng/wristbandsng/eventpro/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Media files — served directly by Nginx (images, QR codes)
    location /media/ {
        alias /home/wbng/wristbandsng/eventpro/media/;
        expires 7d;
        add_header Cache-Control "public";
    }

    # Everything else → Daphne (Django)
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$http_host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
EOF

ln -s /etc/nginx/sites-available/wristbandsng /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx
```

### Step 11 — SSL Certificate (Free via Let's Encrypt)
```bash
apt install -y certbot python3-certbot-nginx
certbot --nginx -d wristbands.ng -d www.wristbands.ng
# Follow prompts — certificate auto-renews
```

### Step 12 — Update .env for Production
```bash
nano .env
# Set:
# DEBUG=False
# HTTPS=True
# ALLOWED_HOSTS=wristbands.ng,www.wristbands.ng
# CSRF_TRUSTED_ORIGINS=https://wristbands.ng,https://www.wristbands.ng
```

```bash
systemctl restart wristbandsng
```

---

## IMAGE SERVING — HOW IT WORKS

### On Render
Django serves media files directly via the `re_path` in `urls.py`.
Images (event banners, QR codes) are accessible at:
`https://wristbandsng.onrender.com/media/event_banners/filename.jpg`

### On VPS with Nginx
Nginx serves `/media/` directly from disk — **faster, no Django overhead**.
Images are accessible at:
`https://wristbands.ng/media/event_banners/filename.jpg`

### What this means for your templates
All image tags use `{{ event.banner.url }}` and `{{ registration.qr_code.url }}`.
Django automatically generates the correct full URL based on `MEDIA_URL` setting.
**No changes needed in templates — they work on both Render and VPS.**

---

## POST-DEPLOYMENT CHECKLIST

- [ ] Homepage loads at your domain
- [ ] Admin login works
- [ ] Create a test event
- [ ] Register as a guest — receive confirmation email with QR code
- [ ] QR code displays in email body ✓
- [ ] Open scanner on phone — camera works (HTTPS required)
- [ ] Scan the QR code — guest checks in
- [ ] Check-in dashboard shows real-time update
- [ ] Export registrations to Excel
- [ ] God mode login works (`wbng_root` / your password)
- [ ] God mode user NOT visible in admin list ✓

---

## MAINTENANCE

### Update the application
```bash
cd /home/wbng/wristbandsng
git pull origin main
source eventpro/venv/bin/activate
pip install -r eventpro/requirements.txt
python eventpro/manage.py migrate
python eventpro/manage.py collectstatic --noinput
systemctl restart wristbandsng
```

### Backup database
```bash
mysqldump -u wbng_user -p wristbandsng_db > backup_$(date +%Y%m%d).sql
```

### View logs
```bash
journalctl -u wristbandsng -f
```
