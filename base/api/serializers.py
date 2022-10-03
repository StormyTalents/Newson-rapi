from rest_framework import serializers
from base.models import Country, WhiteLabel
from django.conf import settings


class CountrySerializer(serializers.ModelSerializer):

    class Meta:
        model = Country
        fields = "__all__"
        read_only_fields = ("id",)


class WhiteLabelSerializer(serializers.ModelSerializer):

    class Meta:
        model = WhiteLabel
        fields = "__all__"
        read_only_fields = ("id", "admin",)


class PublicWhiteLabelSerializer(WhiteLabelSerializer):
    logo = serializers.SerializerMethodField()
    favicon = serializers.SerializerMethodField()

    class Meta:
        model = WhiteLabel
        fields = "__all__"
        read_only_fields = ("id", "admin",)

    
    def get_logo(self, instance):
        return F"{settings.BACKEND_HOST}media/{instance.logo.name}"
    
    def get_favicon(self, instance):
        return F"{settings.BACKEND_HOST}media/{instance.favicon.name}"