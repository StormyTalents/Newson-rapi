# Generated by Django 3.2 on 2022-04-15 19:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0004_alter_whitelabel_options'),
    ]

    operations = [
        migrations.AlterField(
            model_name='whitelabel',
            name='domain',
            field=models.CharField(max_length=500, unique=True),
        ),
    ]