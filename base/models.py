from django.db import models
from uuid import uuid4
from django.contrib.auth.models import User


class Country(models.Model):
    name = models.CharField(max_length=600, unique=True)

    class Meta:
        verbose_name_plural = "Countries"

    def __str__(self) -> str:
        return f"{self.name}"


class WhiteLabel(models.Model):
    id = models.UUIDField(default=uuid4, primary_key=True, unique = True)
    admin = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=600, unique=True)
    domain = models.CharField(max_length=500, unique=True)
    ssl_generated = models.BooleanField(default=False)
    primary_color = models.CharField(max_length=7)
    primary_dark_color = models.CharField(max_length=7)
    theme_color = models.CharField(max_length=7)
    logo = models.ImageField(upload_to = "whitelabels/logos/")
    favicon = models.ImageField(upload_to = "whitelabels/favicons/")

    def __str__(self) -> str:
        return f"{self.name}"