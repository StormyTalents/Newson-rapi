# Generated by Django 3.2 on 2022-08-12 19:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0027_postsequence'),
    ]

    operations = [
        migrations.AlterField(
            model_name='postsequence',
            name='company',
            field=models.CharField(blank=True, help_text='For Posting A Job Post With A Job Company * (Required)', max_length=200, null=True),
        ),
    ]
