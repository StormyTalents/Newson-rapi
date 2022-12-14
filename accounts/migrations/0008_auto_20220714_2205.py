# Generated by Django 3.2 on 2022-07-14 17:05

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0007_linkedinaccount_headline'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProxyCredential',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(max_length=300)),
                ('password', models.CharField(max_length=700)),
                ('provider', models.URLField(blank=True, null=True)),
            ],
        ),
        migrations.AddField(
            model_name='proxy',
            name='credential',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='accounts.proxycredential'),
        ),
    ]
