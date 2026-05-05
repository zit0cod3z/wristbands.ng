import io
import qrcode
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.core.files.base import ContentFile
from events.models import Event
from .models import Registration, RegistrationData


def register(request, slug):
    event = get_object_or_404(Event, slug=slug, status='published')
    now = timezone.now()

    # Check registration is open — no data is affected, just blocks new entries
    if not event.registration_open:
        return render(request, 'registrations/closed.html', {'event': event, 'reason': 'registration_closed'})
    if event.registration_deadline and now > event.registration_deadline:
        return render(request, 'registrations/closed.html', {'event': event, 'reason': 'deadline'})
    if event.is_full:
        return render(request, 'registrations/closed.html', {'event': event, 'reason': 'full'})

    fields = event.form_fields.all()

    if request.method == 'POST':
        data = request.POST
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()

        if not name or not email:
            messages.error(request, 'Name and email are required.')
            return render(request, 'registrations/register.html', {'event': event, 'fields': fields})

        if Registration.objects.filter(event=event, email=email).exists():
            messages.warning(request, 'You have already registered for this event.')
            return render(request, 'registrations/register.html', {'event': event, 'fields': fields})

        ip = request.META.get('REMOTE_ADDR')
        reg = Registration.objects.create(
            event=event,
            name=name,
            email=email,
            ip_address=ip,
        )

        for field in fields:
            if field.field_type == 'checkbox':
                value = ', '.join(data.getlist(field.field_key))
            else:
                value = data.get(field.field_key, '')
            RegistrationData.objects.create(
                registration=reg,
                field_key=field.field_key,
                field_label=field.label,
                value=value,
            )

        _generate_qr(reg)

        # Send email in a background thread so the response returns immediately.
        # This prevents CancelledError when Daphne/asgiref times out waiting for
        # the synchronous view while email sending adds latency.
        import threading
        threading.Thread(
            target=_send_confirmation_email,
            args=(reg,),
            daemon=True,
        ).start()

        return redirect('registration_success', reg.id)

    return render(request, 'registrations/register.html', {'event': event, 'fields': fields})


def registration_success(request, reg_id):
    reg = get_object_or_404(Registration, pk=reg_id)
    return render(request, 'registrations/success.html', {'registration': reg})


def _generate_qr(registration):
    qr_data = f'WRISTBANDSNG|{registration.id}|{registration.registration_code}|{registration.event.title}'
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color='black', back_color='white')
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    filename = f'qr_{registration.registration_code}.png'
    registration.qr_code.save(filename, ContentFile(buffer.read()), save=True)


def _read_qr_bytes(registration):
    """
    Read QR code bytes — works with both local disk and Cloudinary storage.
    Local: reads from file path.
    Cloudinary: downloads from URL.
    """
    if not registration.qr_code:
        return None
    try:
        # Try local path first (local dev + cPanel VPS)
        with open(registration.qr_code.path, 'rb') as f:
            return f.read()
    except (NotImplementedError, AttributeError, FileNotFoundError, ValueError):
        # Cloudinary storage raises NotImplementedError for .path
        # Fall back to downloading from URL
        try:
            import urllib.request
            with urllib.request.urlopen(registration.qr_code.url) as resp:
                return resp.read()
        except Exception:
            return None


def _send_confirmation_email(registration):
    import logging
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.mime.image import MIMEImage

    logger = logging.getLogger(__name__)
    try:
        subject = f'Your Registration Confirmed – {registration.event.title}'

        # Read QR image bytes — works with local disk AND Cloudinary
        qr_bytes = _read_qr_bytes(registration)

        # Render HTML email template
        html_content = render_to_string('emails/confirmation.html', {
            'registration': registration,
            'use_cid': True,
            'qr_available': bool(qr_bytes),
        })

        # Plain text fallback
        text_content = (
            f'Hi {registration.name},\n\n'
            f'Your registration for {registration.event.title} is confirmed.\n'
            f'Registration Code: {registration.registration_code}\n\n'
            f'Your QR code is attached to this email.\n\n'
            f'Event: {registration.event.title}\n'
            f'Date: {registration.event.start_date.strftime("%B %d, %Y")}\n'
            f'Venue: {registration.event.venue}\n'
        )

        smtp_user     = getattr(settings, 'EMAIL_HOST_USER', '')
        smtp_password = getattr(settings, 'EMAIL_HOST_PASSWORD', '')
        resend_key    = getattr(settings, 'RESEND_API_KEY', '')

        if smtp_user and smtp_password:
            # ── Gmail / SMTP (primary — works on Render with app password) ──
            # Build MIME message with inline QR + attachment
            msg_mixed = MIMEMultipart('mixed')
            msg_mixed['Subject'] = subject
            msg_mixed['From']    = settings.DEFAULT_FROM_EMAIL
            msg_mixed['To']      = registration.email

            msg_related = MIMEMultipart('related')
            msg_mixed.attach(msg_related)

            msg_alt = MIMEMultipart('alternative')
            msg_related.attach(msg_alt)
            msg_alt.attach(MIMEText(text_content, 'plain', 'utf-8'))
            msg_alt.attach(MIMEText(html_content, 'html',  'utf-8'))

            if qr_bytes:
                img_inline = MIMEImage(qr_bytes, _subtype='png')
                img_inline.add_header('Content-ID', '<qrcode>')
                img_inline.add_header('Content-Disposition', 'inline',
                                      filename=f'qr_{registration.registration_code}.png')
                msg_related.attach(img_inline)

                img_attach = MIMEImage(qr_bytes, _subtype='png')
                img_attach.add_header('Content-Disposition', 'attachment',
                                      filename=f'qr_{registration.registration_code}.png')
                msg_mixed.attach(img_attach)

            host = getattr(settings, 'EMAIL_HOST', 'smtp.gmail.com')
            port = int(getattr(settings, 'EMAIL_PORT', 587))

            with smtplib.SMTP(host, port, timeout=20) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(smtp_user, smtp_password)
                server.sendmail(smtp_user, [registration.email], msg_mixed.as_string())

        elif resend_key:
            # ── Resend API (fallback — use when domain is verified on resend.com) ──
            import resend
            resend.api_key = resend_key

            params = {
                'from': settings.DEFAULT_FROM_EMAIL,
                'to': [registration.email],
                'subject': subject,
                'html': html_content,
                'text': text_content,
            }
            if qr_bytes:
                params['attachments'] = [{
                    'filename': f'qr_{registration.registration_code}.png',
                    'content': list(qr_bytes),
                }]
            resend.Emails.send(params)

        else:
            logger.warning(
                f'No email credentials configured — skipping email for '
                f'{registration.registration_code}. '
                f'Set EMAIL_HOST_USER + EMAIL_HOST_PASSWORD (Gmail) or RESEND_API_KEY.'
            )
            return

        registration.email_sent = True
        registration.save(update_fields=['email_sent'])
        logger.info(f'Confirmation email sent to {registration.email} for {registration.event.title}')

    except Exception as e:
        logger.error(
            f'Failed to send confirmation email to {registration.email} '
            f'for {registration.registration_code}: {type(e).__name__}: {e}'
        )
        import traceback
        traceback.print_exc()
