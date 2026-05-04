# Generated manually — updates help_text on assigned_events (cosmetic, no schema change)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_adminprofile_assigned_events'),
        ('events', '0003_event_checkin_open_event_registration_open'),
    ]

    operations = [
        migrations.AlterField(
            model_name='adminprofile',
            name='assigned_events',
            field=models.ManyToManyField(
                blank=True,
                help_text='Superadmins see all events automatically. Assign specific events for admin/moderator roles.',
                related_name='assigned_admins',
                to='events.event',
            ),
        ),
    ]
