from enum import unique
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_save
from base.models import Country, WhiteLabel
from uuid import uuid4
from multiselectfield import MultiSelectField
from django.conf import settings
from datetime import time


week_days = (
    (0, 'Monday'),
    (1, 'Tuesday'),
    (2, 'Wednesday'),
    (3, 'Thursday'),
    (4, 'Friday'),
    (5, 'Saturday'),
    (6, 'Sunday')
)


class Plan(models.Model):
    name = models.CharField(max_length=500, unique=True)
    code = models.CharField(max_length=500, unique=True)
    linkedin_and_email_accounts = models.IntegerField()
    prospects_per_month = models.IntegerField()
    price = models.IntegerField()
    white_label = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f"{self.name}"


class License(models.Model):
    id = models.UUIDField(default=uuid4, primary_key=True, unique = True)
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)
    license_product_key = models.UUIDField()
    activation_email = models.EmailField()
    invoice_item_uuid = models.UUIDField()

    def __str__(self) -> str:
        return f"{self.activation_email} / {self.plan.name}"


class Proxy(models.Model):
    username = models.CharField(max_length=300)
    password = models.CharField(max_length=700)
    server = models.CharField(max_length=200)
    port = models.PositiveIntegerField()
    country = models.ForeignKey(Country, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"{self.country.name} / {self.username} / {self.server}"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    app_sumo_user = models.BooleanField(default=False)
    plan = models.OneToOneField(License, on_delete=models.CASCADE, blank = True, null = True)
    whitelabel = models.ForeignKey(WhiteLabel, on_delete=models.CASCADE, null = True)
    has_permission_to_change_linkedin_account_limits = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.user.username}"


class GoogleAccount(models.Model):
    profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    name = models.CharField(max_length=700)
    email = models.EmailField(max_length=700)
    refresh_token = models.CharField(max_length=777)
    id_token = models.CharField(max_length=777)
    access_token = models.CharField(max_length=777)
    connected = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f"{self.name} - {self.profile.user.username} - {self.connected}"

    class Meta:
        unique_together = ["email", "profile",]


class SmtpAccount(models.Model):
    profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    username = models.CharField(max_length=1200)
    password = models.CharField(max_length=1200)
    server = models.CharField(max_length=1200)
    port = models.SmallIntegerField()
    ssl = models.BooleanField(default=False)
    connected = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f"{self.server} - {self.profile.user.username} - {self.connected}"

    class Meta:
        unique_together = ["profile", "username", "server", "ssl"]


class LinkedinAccount(models.Model):
    profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    username = models.CharField(max_length=700)
    password = models.CharField(max_length=700)
    verification_code_url = models.URLField(blank=True, null=True)
    name = models.CharField(max_length=700, blank = True, null = True)
    headline = models.CharField(max_length=700, blank = True, null = True)
    avatar = models.ImageField(upload_to="linkedin-accounts/", blank = True, null = True)
    profile_url = models.URLField(blank = True, null = True)
    connection_requests_per_day_from = models.IntegerField(default=10)
    connection_requests_per_day_to = models.IntegerField(default=20)
    messages_per_day_from = models.IntegerField(default=5)
    messages_per_day_to = models.IntegerField(default=15)
    inmails_per_day_from = models.IntegerField(default=10)
    inmails_per_day_to = models.IntegerField(default=20)
    emails_per_day_from = models.IntegerField(default=5)
    emails_per_day_to = models.IntegerField(default=15)
    like_3_posts_per_day_from = models.IntegerField(default=10)
    like_3_posts_per_day_to = models.IntegerField(default=20)
    follow_per_day_from = models.IntegerField(default=10)
    follow_per_day_to = models.IntegerField(default=20)
    endorse_top_5_skills_per_day_from = models.IntegerField(default=10)
    endorse_top_5_skills_per_day_to = models.IntegerField(default=20)
    ready_for_use = models.BooleanField(default=False)
    connected = models.BooleanField(default=False)
    header_csrf_token = models.TextField()
    header_cookie = models.TextField()
    cookies_file_path = models.CharField(max_length=2000)
    auto_accept_connection_requests = models.BooleanField(default = False)
    auto_accept_connection_requests_last_ran = models.DateTimeField(blank = True, null = True)
    working_days = MultiSelectField(choices = week_days, default=[0,1,2,3,4])
    from_hour = models.TimeField(default=time(9, 0))
    to_hour = models.TimeField(default=time(18, 0))
    timezone = models.CharField(max_length=32, choices = settings.ALL_TIMEZONES, default="Europe/London")
    profile_urn = models.CharField(max_length=700, blank = True, null = True)
    blacklist = models.TextField(blank = True, null = True)
    
    use_custom_proxy = models.BooleanField(default=False)
    
    custom_proxy_username = models.CharField(max_length=700, blank = True, null = True)
    custom_proxy_password = models.CharField(max_length=700, blank = True, null = True)
    custom_proxy_server = models.CharField(max_length=700, blank = True, null = True)
    custom_proxy_port = models.PositiveIntegerField(blank = True, null = True)
    custom_proxy_country = models.ForeignKey(Country, on_delete=models.CASCADE, blank = True, null = True)
    
    proxy = models.OneToOneField(Proxy, on_delete=models.SET_NULL, related_name="linkedin_proxy", blank = True, null = True)

    def __str__(self) -> str:
        return f"{self.name} - {self.profile.user.username} - {self.connected}"
    
    @property
    def get_proxy(self):
        proxy = {}
        
        if self.use_custom_proxy:
            proxy["username"] = self.custom_proxy_username
            proxy["password"] = self.custom_proxy_password
            proxy["server"] = self.custom_proxy_server
            proxy["port"] = self.custom_proxy_port
            proxy["country"] = self.custom_proxy_country
        elif self.proxy:
            proxy["id"] = self.proxy.id
            proxy["username"] = self.proxy.username
            proxy["password"] = self.proxy.password
            proxy["server"] = self.proxy.server
            proxy["port"] = self.proxy.port
            proxy["country"] = self.proxy.country
        
        return proxy

    class Meta:
        unique_together = ["username", "profile",]
        
    @property
    def linkedin_profile_id(self):
        
        if self.profile_url:
            return self.profile_url.split("/in/")[-1].split("/")[0]
        else:
            return None


class ImportLinkedinAccount(models.Model):
    id = models.UUIDField(default=uuid4, primary_key=True, unique = True)
    profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    csv = models.FileField(upload_to="linkedin-account-imports/")
    csv_name = models.CharField(max_length=700)
    finished = models.BooleanField(default = False)
    total_rows = models.PositiveIntegerField(default=1)
    imported = models.PositiveIntegerField(default=0)
    failed = models.PositiveIntegerField(default=0)
    failed_rows = models.TextField(blank = True, null = True)
    finished_at = models.DateTimeField(blank = True, null = True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.csv_name}"