# Generated by Django 3.2 on 2022-08-15 20:18

from django.db import migrations, models
import django.db.models.deletion
import multiselectfield.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0028_alter_postsequence_company'),
    ]

    operations = [
        migrations.AddField(
            model_name='prospect',
            name='engagement',
            field=multiselectfield.db.fields.MultiSelectField(blank=True, choices=[('Liked Posts', 'Liked Posts'), ('Commented Posts', 'Commented Posts'), ('Shared Posts', 'Shared Posts')], max_length=40, null=True),
        ),
        migrations.CreateModel(
            name='PostCampaignPost',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('post_link', models.URLField()),
                ('state_status', models.CharField(blank=True, choices=[('Performing', 'Performing'), ('Failed', 'Failed'), ('Finished', 'Finished')], max_length=40, null=True)),
                ('state_action_start_time', models.DateTimeField(blank=True, null=True)),
                ('state_action_finish_time', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('campaign_linkedin_account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.campaignlinkedinaccount')),
                ('state', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='main.postsequence')),
            ],
        ),
    ]
