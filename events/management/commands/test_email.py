"""
Usage:
    python manage.py test_email your@email.com
"""
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings


class Command(BaseCommand):
    help = 'Send a test email to verify SMTP configuration'

    def add_arguments(self, parser):
        parser.add_argument('recipient', type=str, help='Email address to send test to')

    def handle(self, *args, **options):
        recipient = options['recipient']
        self.stdout.write(f'Sending test email to {recipient}...')
        self.stdout.write(f'  Backend:  {settings.EMAIL_BACKEND}')
        self.stdout.write(f'  Host:     {settings.EMAIL_HOST}:{settings.EMAIL_PORT}')
        self.stdout.write(f'  From:     {settings.DEFAULT_FROM_EMAIL}')
        try:
            send_mail(
                subject='WristbandsNG – Email Test ✓',
                message=(
                    'This is a test email from WristbandsNG.\n\n'
                    'If you received this, your email configuration is working correctly.\n\n'
                    '— WristbandsNG System'
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient],
                fail_silently=False,
            )
            self.stdout.write(self.style.SUCCESS(f'✓ Email sent successfully to {recipient}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Failed: {type(e).__name__}: {e}'))
            self.stdout.write(self.style.WARNING(
                '\nCommon fixes:\n'
                '  Gmail: Use an App Password (not your regular password)\n'
                '  Generate at: https://myaccount.google.com/apppasswords\n'
                '  Requires 2-Step Verification to be enabled first'
            ))
