# Generated by Django 3.2 on 2022-05-10 19:50

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0014_label_description'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='room',
            name='headline',
        ),
        migrations.RemoveField(
            model_name='room',
            name='linkedin_avatar',
        ),
        migrations.RemoveField(
            model_name='room',
            name='linkedin_profile_url',
        ),
        migrations.RemoveField(
            model_name='room',
            name='location',
        ),
        migrations.RemoveField(
            model_name='room',
            name='name',
        ),
    ]
