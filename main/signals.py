from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Campaign, CeleryJob
from celery.task.control import revoke


@receiver(post_save, sender=Campaign)
def stop_campaign(sender, instance, created, *args, **kwargs):
    
    if instance.status == "Stopped":
        print("Stopping Campaign")
        for job in CeleryJob.objects.filter(campaign=instance):
            revoke(job.task_id, terminate=True)