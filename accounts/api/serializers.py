from django.shortcuts import get_object_or_404
from base.models import Country, WhiteLabel
from rest_framework import serializers, fields
from django.contrib.auth.models import User
from accounts.models import LinkedinAccount, UserProfile, SmtpAccount, GoogleAccount, License, week_days
from main.models import Campaign
from rest_framework_simplejwt.serializers import get_user_model, PasswordField, authenticate, api_settings, exceptions, RefreshToken, update_last_login
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from datetime import time


class MyTokenObtainPairSerializer(serializers.Serializer):
    token_class = RefreshToken
    username_field = get_user_model().USERNAME_FIELD

    default_error_messages = {
        "no_active_account": _("No active account found with the given credentials")
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields[self.username_field] = serializers.CharField()
        self.fields["password"] = PasswordField()

    def validate(self, attrs):
        authenticate_kwargs = {
            self.username_field: attrs[self.username_field],
            "password": attrs["password"],
            "password": attrs["password"],
        } 
        try:
            authenticate_kwargs["request"] = self.context["request"]
        except KeyError:
            pass
        
        self.user = authenticate(**authenticate_kwargs)

        if not api_settings.USER_AUTHENTICATION_RULE(self.user):
            raise exceptions.AuthenticationFailed(
                self.error_messages["no_active_account"],
                "no_active_account",
            )

#         if not self.user.userprofile.whitelabel == self.context["whitelabel"]:
#             print("here whitelabel")
#             raise exceptions.AuthenticationFailed(
#                 self.error_messages["no_active_account"],
#                 "no_active_account",
#             ) 
            
        data = {}

        refresh = self.get_token(self.user)

        data["refresh"] = str(refresh)
        data["access"] = str(refresh.access_token)

        if api_settings.UPDATE_LAST_LOGIN:
            update_last_login(None, self.user)
        
        return data
    
    @classmethod
    def get_token(cls, user):
        return cls.token_class.for_user(user)


class AppSumoNotificationSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices = ["activate", "enhance_tier", "reduce_tier", "refund"])
    plan_id = serializers.CharField()
    uuid = serializers.UUIDField() # license product key
    activation_email = serializers.EmailField()
    invoice_item_uuid = serializers.UUIDField(required=False)


class UserProfileSerializer(serializers.ModelSerializer):
    smtp_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password', 'placeholder': 'Smtp Password'}
    )

    class Meta:
        model = UserProfile
        fields = (
            "id",
            "user",
            "linkedin_username",
            "linkedin_account_connected",
            "google_name",
            "google_email",
            "google_account_connected",
            "smtp_username",
            "smtp_password",
            "smtp_server",
            "smtp_port",
            "smtp_ssl",
            "smtp_account_connected",
        )
        read_only_fields = (
            "id",
            "user",
            "linkedin_username",
            "google_name",
            "google_email",
        )


class UserRegisterSerializer(serializers.ModelSerializer):

    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        write_only=True, style={'input_type': 'password', })

    def create(self, validated_data):
        license = None
        whitelabel = get_object_or_404(WhiteLabel, id = self.context.get("whitelabel"))

        if self.context["request"].GET.get("license_id"):
            license = get_object_or_404(License, id = self.context["request"].GET["license_id"], userprofile__isnull = True)

        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
        )

        if license:
            user.userprofile.plan = license
            user.userprofile.save() 
    
        user.userprofile.whitelabel = whitelabel
        user.userprofile.save()

        return user
    
    def validate(self, attrs):
        
        if not self.context.get("whitelabel") or not WhiteLabel.objects.filter(id = self.context.get("whitelabel")).exists():
            raise serializers.ValidationError({ "whitelabel": "Whitelabel Doesn't Exist!" })    
        
        return super().validate(attrs)

    class Meta:
        model = User
        fields = ("id", "username", "email", "password",)


class ConnectLinkedinAccountSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=700,)
    password = serializers.CharField(max_length=700, write_only=True, style={'input_type': 'password', },)
    timezone = serializers.ChoiceField(choices=settings.ALL_TIMEZONES, default="Europe/London")
    from_hour = serializers.TimeField(default=time(9, 0))
    to_hour = serializers.TimeField(default=time(18, 0))
    
    use_custom_proxy = serializers.BooleanField(default=False)
    custom_proxy_username = serializers.CharField(max_length=700, required=False, allow_blank=True)
    custom_proxy_password = serializers.CharField(max_length=700, required=False, allow_blank=True)
    custom_proxy_server = serializers.CharField(max_length=700, required=False, allow_blank=True)
    custom_proxy_port = serializers.IntegerField(required=False, allow_null = True)
    
    country = serializers.PrimaryKeyRelatedField(queryset=Country.objects.all(), allow_null=False, required=True)

    
class ReConnectLinkedinAccountSerializer(serializers.Serializer):
    username = serializers.CharField(
        max_length=700, required=False, allow_blank = True)
    password = serializers.CharField(max_length=700, write_only=True, style={
                                     'input_type': 'password', }, required=False, allow_blank = True)
    linkedin_account = serializers.IntegerField()


class ConnectLinkedinAccountVerificationCodeSerializer(serializers.Serializer):
    code = serializers.IntegerField()
    linkedin_account = serializers.IntegerField()


class GoogleEmailCodeSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=256)
    redirect_uri = serializers.URLField()


class LinkedinAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = LinkedinAccount
        exclude = (
            "password",
            "verification_code_url",
            "cookies_file_path",
            "header_csrf_token",
            "proxy",
        )
        

class LinkedinAccountRetrieveSerializer(serializers.ModelSerializer):
    working_days = fields.MultipleChoiceField(choices=week_days)
    country = serializers.PrimaryKeyRelatedField(queryset=Country.objects.all(), allow_null=True, required=False, write_only = True)

    class Meta:
        model = LinkedinAccount
        exclude = (
            "password",
            "verification_code_url",
            "cookies_file_path",
            "header_csrf_token",
            "header_cookie",
            "proxy",
        )
        read_only_fields = (
            "profile",
            "username",
            "password",
            "verification_code_url",
            "name",
            "headline",
            "avatar",
            "profile_url",
            "connected",
            "auto_accept_connection_requests_last_ran",
            "profile_urn",
            "proxy",
        )


class SmtpAccountSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, style={'input_type': 'password', })
    class Meta:
        model = SmtpAccount
        fields = "__all__"
        read_only_fields = ("profile", "connected",)


class GoogleAccountSerializer(serializers.ModelSerializer):
    access_token = serializers.CharField(max_length=777, write_only=True, style={'input_type': 'password', })

    class Meta:
        model = GoogleAccount
        fields = "__all__"
        read_only_fields = ("profile", "connected",)


class LicenseSerializer(serializers.ModelSerializer):

    class Meta:
        model = License
        fields = "__all__"


class UserSerializer(serializers.ModelSerializer):
    linkedin_accounts = serializers.SerializerMethodField()
    campaigns = serializers.SerializerMethodField()
    plan = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "username", "email", "linkedin_accounts", "campaigns", "plan",)


    def get_plan(self, instance):
        return instance.userprofile.plan.plan.name if instance.userprofile.plan else None
    
    def get_linkedin_accounts(self, instance):
        return LinkedinAccount.objects.filter(profile__user=instance).count()

    def get_campaigns(self, instance):
        return Campaign.objects.filter(user=instance).count()


class BulkImportLinkedinAccountsSerializer(serializers.Serializer):
    csv_file = serializers.FileField(required=True)
