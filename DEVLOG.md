# EventPro – Full Development Log
> Built with Kiro AI | Python 3.14 + Django 5.2 + SQLite/MySQL

---

## Project Overview
A full-featured bespoke event management system for Wristbands Nigeria (wristbands.ng).
Manages concerts, conferences, meetups and any event type with QR check-in, real-time dashboards, offline scanning and Excel import/export.

---

## Tech Stack
| Layer | Technology |
|---|---|
| Backend | Python 3.14, Django 5.2 |
| Database | SQLite (dev) / MySQL (production) |
| Real-time | Django Channels 4.1 + Daphne 4.1 (WebSockets) |
| Task Queue | Celery + Redis (optional) |
| Frontend | Bootstrap 5.3, custom CSS, Chart.js |
| QR Codes | qrcode library (server-side generation) |
| QR Scanning | jsQR (client-side, works offline) |
| Excel | openpyxl |
| Offline PWA | Service Worker + IndexedDB |
| Load Balancer | Nginx (least_conn, 4 Gunicorn workers) |
| App Server | Daphne (ASGI) |

---

## Colour Palette (wristbands.ng)
| Role | Hex |
|---|---|
| Primary (magenta) | `#ac2376` |
| Accent (orange-red) | `#e6573f` |
| Dark background | `#0d0d12` |
| Card background | `#181418` |
| Muted text | `#7a6872` |

---

## Project Structure
```
eventpro/
├── eventpro/          # Django project (settings, urls, asgi, wsgi, celery)
├── events/            # Event model, form fields, public views, dashboard views
├── registrations/     # Registration model, registration views, dashboard views
├── accounts/          # Admin user profiles, login/logout/profile views
├── checkin/           # Full check-in system (QR scanner, PWA, import, dashboard)
├── templates/
│   ├── base.html                        # Public site base
│   ├── home.html                        # Homepage with hero, featured events
│   ├── events/
│   │   ├── events_list.html
│   │   └── event_detail.html
│   ├── registrations/
│   │   ├── register.html                # Dynamic registration form
│   │   ├── success.html                 # Post-registration success page
│   │   └── closed.html                  # Registration closed/full page
│   ├── emails/
│   │   └── confirmation.html            # Beautiful HTML confirmation email
│   ├── dashboard/
│   │   ├── base.html                    # Dashboard sidebar layout
│   │   ├── index.html                   # Dashboard overview with charts
│   │   ├── events/
│   │   │   ├── list.html
│   │   │   ├── create.html
│   │   │   ├── edit.html
│   │   │   ├── form_builder.html        # Drag-and-drop form field builder
│   │   │   └── confirm_delete.html
│   │   └── registrations/
│   │       ├── list.html
│   │       ├── event_registrations.html
│   │       └── manual_add.html
│   ├── accounts/
│   │   ├── login.html
│   │   ├── profile.html
│   │   └── lockout.html
│   └── checkin/
│       ├── event_select.html            # Event selector with share modal + scanner QR
│       ├── scanner.html                 # Basic online QR scanner
│       ├── pwa_scanner.html             # PWA offline-capable scanner
│       ├── dashboard.html               # Per-event real-time check-in dashboard
│       ├── overview.html                # All-events check-in overview
│       ├── import_guests.html           # Excel guest list import
│       └── manual_checkin_list.html     # Manual name-based check-in
├── static/
│   ├── css/
│   │   ├── main.css                     # Public site styles
│   │   ├── dashboard.css                # Admin dashboard styles
│   │   └── scanner-pwa.css              # PWA scanner styles
│   ├── js/
│   │   ├── main.js                      # Public site JS
│   │   ├── dashboard.js                 # Dashboard JS (sidebar, alerts)
│   │   ├── scanner-pwa.js               # Full offline PWA scanner engine
│   │   └── sw.js                        # Service Worker for offline support
│   └── img/
│       ├── icon-192.png                 # PWA icon
│       └── icon-512.png                 # PWA icon
├── nginx/
│   ├── nginx.conf                       # Load balancer config (4 upstream workers)
│   └── proxy_params                     # Nginx proxy headers
├── media/
│   ├── qrcodes/                         # Generated QR codes per registrant
│   ├── event_banners/                   # Event banner images
│   └── avatars/                         # Admin profile photos
├── .env                                 # Local environment variables
├── .env.example                         # Template for production env
├── requirements.txt                     # Python dependencies
├── manage.py
├── gunicorn.conf.py                     # Gunicorn config for production
└── DEVLOG.md                            # This file
```

---

## Apps & Models

### events app
- **Event** — UUID pk, title, slug, description, event_type, banner, venue, city, country, start/end dates, capacity, status, color_theme, is_featured
- **FormField** — per-event custom fields: text, email, tel, number, textarea, select, radio, checkbox, date, file

### registrations app
- **Registration** — UUID pk, event FK, registration_code (unique), name, email, status, qr_code, checked_in, checked_in_at, email_sent, ip_address
- **RegistrationData** — stores dynamic form field responses per registration

### accounts app
- **AdminProfile** — extends User with role (superadmin/admin/moderator), avatar, phone, bio

### checkin app
- **CheckInLog** — logs every scan attempt (success or fail) with device info, scanned code, timestamp, scanned_by

---

## URL Map
| URL | Description |
|---|---|
| `/` | Public homepage |
| `/events/` | All events listing |
| `/events/<slug>/` | Event detail page |
| `/registrations/<slug>/` | Dynamic registration form |
| `/registrations/success/<id>/` | Registration success + QR display |
| `/accounts/login/` | Admin login |
| `/accounts/logout/` | Logout |
| `/accounts/profile/` | Admin profile settings |
| `/dashboard/` | Admin dashboard overview |
| `/dashboard/events/` | Manage all events |
| `/dashboard/events/create/` | Create new event |
| `/dashboard/events/<id>/edit/` | Edit event |
| `/dashboard/events/<id>/form-builder/` | Build registration form fields |
| `/dashboard/registrations/` | All registrations by event |
| `/dashboard/registrations/<event_id>/` | Registrations for one event |
| `/dashboard/registrations/<event_id>/export/` | Export registrations to Excel |
| `/dashboard/registrations/manual-add/<event_id>/` | Manually add a registrant |
| `/checkin/` | Check-in event selector |
| `/checkin/overview/` | All-events check-in overview dashboard |
| `/checkin/export-all/` | Export all events check-in data (one sheet per event) |
| `/checkin/<event_id>/scanner/` | Basic online QR scanner |
| `/checkin/<event_id>/pwa/` | PWA offline-capable scanner (installable) |
| `/checkin/<event_id>/scan/` | AJAX scan endpoint |
| `/checkin/<event_id>/dashboard/` | Per-event real-time check-in dashboard |
| `/checkin/<event_id>/stats/` | Live stats JSON endpoint |
| `/checkin/<event_id>/export/` | Export checked-in guests to Excel |
| `/checkin/<event_id>/manual/<reg_id>/` | Toggle check-in for one registrant |
| `/checkin/<event_id>/import/` | Import guest list from Excel |
| `/checkin/<event_id>/manual-checkin/` | Manual name-based check-in search |
| `/checkin/<event_id>/offline-registrations/` | Download all regs for offline cache |
| `/checkin/<event_id>/sync-offline/` | Flush offline queue to server |
| `/checkin/<event_id>/scanner-qr/` | QR code image of the scanner URL |
| `/sw.js` | Service Worker (PWA) |
| `/manifest.json` | PWA Web App Manifest |
| `/django-admin/` | Native Django admin |

---

## Key Features Built

### 1. Public Event Site
- Animated hero with floating cards, gradient text, stats
- Featured events section, upcoming events grid
- Event detail pages with capacity progress bars
- Mobile responsive (Bootstrap 5.3)

### 2. Dynamic Registration Forms
- Admin builds custom forms per event using a visual form builder
- Supports: text, email, phone, number, textarea, select dropdown, radio buttons, checkboxes, date picker, file upload
- Name + Email always included by default
- Duplicate email prevention per event

### 3. QR Code System
- Unique QR generated per registrant on registration
- QR data format: `EVENTPRO|<uuid>|<reg_code>|<event_title>`
- QR stored as PNG in `media/qrcodes/`
- QR attached to confirmation email and displayed on success page

### 4. Confirmation Emails
- Beautiful HTML email with event details, registration code, QR code
- wristbands.ng colour scheme
- Falls back to console backend in development (no SMTP needed)
- Sends automatically on registration or manual add

### 5. Admin Dashboard
- Stats cards: total events, published, registrations, upcoming
- Monthly registrations bar chart (Chart.js)
- Events by type doughnut chart
- Recent events and registrations tables
- Full CRUD for events with banner upload, colour theme picker

### 6. Form Builder
- Add/remove fields per event
- Field types with options (comma-separated for select/radio/checkbox)
- Live preview of form structure
- Link to live registration page

### 7. Registration Management
- Per-event registration tables with search
- View full registrant details in modal
- Send QR manually to any registrant
- Manual registration entry (admin adds someone directly)
- Excel export with styled headers, alternating rows, all custom fields

### 8. QR Check-in System (Online)
- Scanner page works in any browser on any device
- jsQR decodes QR client-side (no server round-trip for decode)
- AJAX POST to server for validation and check-in
- WebSocket broadcast via Django Channels to all connected dashboards
- Colour + vibration feedback (green=success, yellow=duplicate, red=invalid)
- Duplicate prevention: same QR cannot check in twice
- Manual toggle check-in from dashboard

### 9. PWA Offline Scanner
- Installable as native-like app on any phone/PDA (Add to Home Screen)
- Downloads all registrations to IndexedDB when online
- Scans and validates completely offline using local cache
- Queues offline check-ins in IndexedDB
- Auto-syncs queue to server when internet returns
- Background Sync API registered for sync even when tab is closed
- Status bar shows online/offline/syncing state
- Queue badge shows pending offline check-ins count

### 10. Share Scanner Feature
- Each event has a "Share" button on the check-in selector
- Modal shows QR code of the scanner URL (staff scan to open scanner)
- Full URL displayed with one-click copy button
- Step-by-step instructions for staff
- QR code generated in brand colour (#ac2376)

### 11. Per-Event Check-in Dashboard
- Event identity banner (name, date, venue, type) — no confusion between events
- Live stats: checked in, total, remaining, attendance %
- Animated progress bar
- Real-time checked-in list (updates via WebSocket)
- Not-arrived list with manual check-in button
- Scan activity log (last 50 scans)
- All data strictly scoped to one event

### 12. All-Events Overview
- Grand totals across all events
- Per-event row with progress bar, stats, action buttons
- Export all events in one Excel file (one sheet per event)
- Each sheet has event name, date, venue, capacity info in header

### 13. Excel Guest List Import
- Drag-and-drop or browse for .xlsx/.xls
- Auto-detects Name, Email, Phone columns (flexible column names)
- Option to mark all imported guests as pre-checked-in
- Generates QR codes for all imported guests
- Sends confirmation emails to guests with real email addresses
- Skips duplicates, reports errors per row

### 14. Manual Name Check-in
- Search by name, email or registration code
- Live search as you type (400ms debounce)
- One-tap check-in with instant UI update (no page reload)
- Undo button to reverse accidental check-ins
- Toast notification for every action
- Works on phone/tablet at event entrance

---

## Bugs Fixed During Development
| Bug | Cause | Fix |
|---|---|---|
| `No module named 'decouple'` | pip install failed on Python 3.14 | Replaced python-decouple with built-in `.env` loader |
| `Pillow` build failure | No wheel for Python 3.14 | Pillow 12.1.1 already installed system-wide |
| `Invalid filter: 'split'` | Used Python method as Django template filter | Rewrote home.html with explicit HTML |
| `no such function: MONTH` | MySQL-only SQL in SQLite | Replaced `.extra()` with `TruncMonth` from `django.db.models.functions` |
| Django admin 500 error | Python 3.14 incompatibility in Django 5.1.4 `Context.__copy__` | Upgraded to Django 5.2 |
| Port 8000 already in use | Previous Daphne process still holding socket | Killed process by PID, used port 8001 temporarily |
| Check-in page showing old template | Daphne serving cached template | Cleared `.pyc` files, restarted server |

---

## Environment Variables (.env)
```
SECRET_KEY=<generated>
DEBUG=True
ALLOWED_HOSTS=*

# Database (SQLite default, MySQL for production)
# DB_ENGINE=django.db.backends.mysql
# DB_NAME=eventpro_db
# DB_USER=root
# DB_PASSWORD=your_password
# DB_HOST=localhost
# DB_PORT=3306

# Redis (optional, for WebSocket channel layer in production)
# REDIS_URL=redis://127.0.0.1:6379/0

# Email (blank = console backend for dev)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
DEFAULT_FROM_EMAIL=EventPro <noreply@eventpro.com>

CORS_ORIGINS=http://localhost:8000
```

---

## Running the App

### Development
```bash
cd eventpro
python -m daphne -p 8000 eventpro.asgi:application
# Visit http://127.0.0.1:8000
# Admin login: admin / admin1234
```

### Production (on wristbands.ng)
```bash
# 1. Fill in .env with real values
# 2. Run migrations
python manage.py migrate
python manage.py collectstatic

# 3. Start 4 Gunicorn workers
gunicorn -c gunicorn.conf.py --bind 0.0.0.0:8001 eventpro.wsgi:application &
gunicorn -c gunicorn.conf.py --bind 0.0.0.0:8002 eventpro.wsgi:application &
gunicorn -c gunicorn.conf.py --bind 0.0.0.0:8003 eventpro.wsgi:application &
gunicorn -c gunicorn.conf.py --bind 0.0.0.0:8004 eventpro.wsgi:application &

# 4. Point Nginx at nginx/nginx.conf
# 5. For WebSockets in production, use Daphne instead of Gunicorn
python -m daphne -p 8000 eventpro.asgi:application
```

---

## Default Credentials
- **Username:** `admin`
- **Password:** `admin1234`
- **Change this before going live!**

---

*Last updated: April 2026*
