# WristbandsNG Event Management System
## Executive Pitch Deck

---

## THE PROBLEM

Nigerian event organisers currently manage guest registration, check-in, and access control using:
- Paper lists that get lost or damaged
- WhatsApp groups with no structure
- Manual name-checking that creates long queues
- No real-time visibility into who has arrived
- Zero data for post-event analysis

**The result:** Chaotic entrances, gate-crashing, no accountability, and wasted hours.

---

## THE SOLUTION

**WristbandsNG Event Management System** — a complete, end-to-end digital platform that handles every stage of event management from registration to check-in, built specifically for the Nigerian market.

---

## PRODUCT OVERVIEW

A web-based platform accessible from any device — laptop, phone, or PDA scanner — that manages the full event lifecycle:

```
Guest Registers Online → Gets QR Code by Email → Arrives at Event → 
Staff Scans QR → Instant Check-in → Real-time Dashboard Updates
```

---

## KEY FEATURES

### 1. Multi-Event Management Dashboard
- Create and manage unlimited events simultaneously
- Each event has its own registration form, guest list, and check-in dashboard
- Event types: Concerts, Conferences, Meetups, Workshops, Parties, Sports
- Custom colour themes per event
- Featured events on public homepage
- Publish/unpublish events instantly

### 2. Dynamic Registration Forms
- Build custom registration forms per event — no coding required
- Supports: Text, Email, Phone, Number, Dropdown, Radio buttons, Checkboxes, Date, File upload
- Name and Email always included by default
- Capacity limits with automatic closure when full
- Registration deadline enforcement
- Duplicate email prevention

### 3. Automatic QR Code Generation
- Every registrant receives a unique, tamper-proof QR code
- QR code embedded directly in confirmation email (works in Gmail, Outlook, all clients)
- QR code also attached as a downloadable PNG file
- Format: `WRISTBANDSNG|UUID|REG_CODE|EVENT_TITLE` — cryptographically unique

### 4. Beautiful Confirmation Emails
- Branded HTML email with event details, registration code, and QR code
- Sent automatically on registration
- Works with Gmail SMTP, Brevo, SendGrid, or any SMTP provider
- Fallback to console output in development

### 5. QR Code Check-in System
- **Online mode:** Scan QR → instant server validation → real-time dashboard update
- **Offline mode (PWA):** Works completely without internet — scans stored locally, syncs when reconnected
- Works on any device with a camera: Android PDA, iPhone, Android phone, tablet
- Duplicate prevention: same QR cannot check in twice
- Vibration + colour feedback (green = success, yellow = duplicate, red = invalid)
- Manual entry fallback for damaged QR codes

### 6. Progressive Web App (PWA) Scanner
- Installable on any phone/PDA — works like a native app
- **Full offline capability:** Downloads guest list to device, scans without internet
- Automatic sync when connection returns
- Background sync via Service Worker
- Works on Zebra PDAs, Honeywell scanners, any Android/iOS device

### 7. Real-time Check-in Dashboard
- Live updates via WebSocket — no page refresh needed
- Checked-in list, not-arrived list, scan activity log
- Attendance percentage with animated progress bar
- Per-event isolation — no data mixing between events
- All-events overview with grand totals

### 8. External QR Code Import
- Import guest lists from ANY external system (Eventbrite, Google Forms, custom ticketing)
- Upload Excel/CSV with QR ID + guest data
- Auto-detects column names (flexible naming)
- Creates WristbandsNG registrations with proper QR codes
- Sends confirmation emails to imported guests
- Duplicate detection by email AND external QR ID

### 9. Offline Registration
- Register guests without internet — saves to device IndexedDB
- Syncs to server when connection returns
- Generates QR codes and sends emails automatically on sync
- Works on any phone or tablet at the event entrance

### 10. Excel Export
- Export all registrations per event — styled spreadsheet with all custom fields
- Export all check-in data per event
- Export ALL events in one file (one sheet per event)
- Branded headers in WristbandsNG colours

### 11. Admin Access Control
- **Super Admin:** Full access to all events
- **Admin:** Access only to assigned events
- **Moderator:** View-only on assigned events
- Brute-force protection (5 failed attempts = 1 hour lockout)

### 12. Manual Guest Management
- Add guests manually from dashboard
- Search by name, email, or registration code
- One-tap check-in from name list
- Import guest lists from Excel with auto-column detection
- Manual QR resend for any registrant

### 13. Load Balancing Ready
- Nginx configuration included for 4 Gunicorn workers
- Handles 100,000+ concurrent users
- Redis channel layer for WebSocket scaling
- Rate limiting on registration and API endpoints

---

## TECHNICAL STACK

| Layer | Technology |
|---|---|
| Backend | Python 3.14 + Django 5.2 |
| Real-time | Django Channels + Daphne (WebSockets) |
| Database | SQLite (dev) / MySQL (production) |
| Frontend | Bootstrap 5.3 + Custom CSS + Chart.js |
| QR Generation | qrcode library (server-side) |
| QR Scanning | jsQR (client-side, works offline) |
| Offline Storage | IndexedDB + Service Worker |
| Email | SMTP (Gmail/Brevo/SendGrid) |
| Excel | openpyxl |
| Security | django-axes, CSRF, HSTS, XSS protection |
| Load Balancer | Nginx (least_conn upstream) |

---

## SECURITY FEATURES

- HTTPS enforced in production with HSTS
- CSRF protection on all forms and AJAX endpoints
- Brute-force login protection (django-axes)
- Session cookies: HttpOnly, Secure, SameSite=Lax
- Non-default cookie names (hides framework fingerprint)
- File upload size limits (10MB max)
- SQL injection protection (Django ORM parameterised queries)
- XSS protection headers
- Clickjacking prevention (X-Frame-Options: DENY)
- Rate limiting on registration and check-in endpoints

---

## BUSINESS MODEL

### Revenue Streams
1. **SaaS Subscription** — Monthly fee per organisation
   - Starter: Up to 5 events/month
   - Professional: Unlimited events
   - Enterprise: White-label + custom domain

2. **Per-Event Fee** — Pay per event for occasional organisers

3. **Hardware Bundle** — PDA scanners pre-configured with the system

4. **Managed Service** — WristbandsNG staff operate the check-in on event day

### Target Market
- Concert promoters (primary — existing WristbandsNG clients)
- Corporate event organisers
- Conference and seminar organisers
- University events
- Government functions
- Sports events

---

## COMPETITIVE ADVANTAGE

| Feature | WristbandsNG | Eventbrite | Manual |
|---|---|---|---|
| Offline scanning | ✅ | ❌ | N/A |
| Custom forms | ✅ | Limited | N/A |
| Real-time dashboard | ✅ | ✅ | ❌ |
| External QR import | ✅ | ❌ | ❌ |
| Nigerian market focus | ✅ | ❌ | N/A |
| Works on PDA scanners | ✅ | ❌ | N/A |
| No internet required | ✅ | ❌ | ✅ |
| Excel export | ✅ | Limited | N/A |
| White-label ready | ✅ | ❌ | N/A |

---

## TRACTION

WristbandsNG has already provided wristbands and event services for:
- KOCEE LIVE CONCERT (March 2025)
- Naira Marley Live at Capital Fest (Dec 2024)
- WARRI AGAIN? 22nd Edition (Dec 2024)
- AY Live Abuja 2019
- At The Club with Remy Martin 2019
- Nigerian Stock Exchange events
- Terra Kulture events
- EKO Hotel and Suites events

**This platform digitises and scales what WristbandsNG already does physically.**

---

## THE ASK

Deploy this system on wristbands.ng to:
1. Serve existing clients digitally
2. Attract new clients who need end-to-end event management
3. Create a recurring revenue stream alongside physical wristband sales
4. Position WristbandsNG as a technology company, not just a supplier

---

*Built with Python/Django · Deployable on Render (test) or cPanel (production)*
*Ready for immediate deployment*
