# Generated by Django 3.2 on 2022-09-14 01:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0020_auto_20220907_0500'),
    ]

    operations = [
        migrations.AddField(
            model_name='linkedinaccount',
            name='blacklist',
            field=models.TextField(blank=True, null=True),
        ),
    ]
