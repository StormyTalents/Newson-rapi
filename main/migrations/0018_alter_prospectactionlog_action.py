# Generated by Django 3.2 on 2022-07-18 18:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0017_prospectactionlog'),
    ]

    operations = [
        migrations.AlterField(
            model_name='prospectactionlog',
            name='action',
            field=models.CharField(blank=True, choices=[('send_connection_request', 'Send Connection Request'), ('send_message', 'Send Message'), ('send_inmail', 'Send InMail'), ('like_3_posts', 'Like 3 Posts'), ('follow', 'Follow'), ('endorse_top_5_skills', 'Endorse Top 5 Skills'), ('send_email', 'Send Email')], max_length=23, null=True),
        ),
    ]
