# Generated by Django 3.2 on 2022-04-21 18:50

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0006_whitelabel_primary_dark_color'),
        ('accounts', '0005_userprofile_whitelabel'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='whitelabel',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='base.whitelabel'),
        ),
    ]
