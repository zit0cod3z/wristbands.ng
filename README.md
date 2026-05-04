# WristbandsNG – Event Management System

A full-featured, beautiful event management platform built with Django + MySQL.

## Features
- **Public site** – Homepage, event listings, event detail pages
- **Dynamic registration forms** – Per-event custom fields (text, email, phone, select, radio, checkbox, date, file, textarea)
- **QR code generation** – Unique QR per registrant, auto-generated on registration
- **Beautiful confirmation emails** – HTML email with QR code attached
- **Admin dashboard** – Stats, charts, event management, form builder
- **Registration management** – View, search, manual add, send QR manually
- **Excel export** – One-click export of all registrations per event
- **Load balancing** – Nginx upstream with 4 Gunicorn workers + Redis caching
- **Security** – Brute-force protection (django-axes), CSRF, rate limiting

## Quick Start

```bash
cd eventpro
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
cp .env.example .env           # Edit with your credentials
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## URLs
| URL | Description |
|-----|-------------|
| `/` | Public homepage |
| `/events/` | All events listing |
| `/events/<slug>/` | Event detail page |
| `/registrations/<slug>/` | Registration form for event |
| `/accounts/login/` | Admin login |
| `/dashboard/` | Admin dashboard |
| `/dashboard/events/` | Manage events |
| `/dashboard/events/create/` | Create new event |
| `/dashboard/events/<id>/form-builder/` | Build registration form |
| `/dashboard/registrations/` | All registrations |
| `/dashboard/registrations/<event_id>/` | Event registrations |
| `/dashboard/registrations/<event_id>/export/` | Export to Excel |

## Load Balancing (Production)
Run 4 Gunicorn processes on ports 8001–8004, Nginx distributes traffic:
```bash
gunicorn -c gunicorn.conf.py --bind 0.0.0.0:8001 eventpro.wsgi:application &
gunicorn -c gunicorn.conf.py --bind 0.0.0.0:8002 eventpro.wsgi:application &
gunicorn -c gunicorn.conf.py --bind 0.0.0.0:8003 eventpro.wsgi:application &
gunicorn -c gunicorn.conf.py --bind 0.0.0.0:8004 eventpro.wsgi:application &
```
Then point Nginx at `nginx/nginx.conf`.

## Stack
- **Backend**: Python 3.11 + Django 4.2
- **Database**: MySQL 8 (via mysqlclient)
- **Cache/Queue**: Redis + Celery
- **Email**: SMTP (Gmail/SendGrid)
- **QR Codes**: qrcode library
- **Excel**: openpyxl
- **Load Balancer**: Nginx (least_conn upstream)
- **App Server**: Gunicorn (gthread workers)
- **Frontend**: Bootstrap 5.3 + custom CSS + Chart.js
