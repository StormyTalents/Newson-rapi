import imp
from django.contrib import admin
from .models import Campaign, CampaignSequence, CampaignLinkedinAccount, Prospect, SearchParameter, CampaignFailedReason, UserLinkedinConnection, CeleryJob, Message, Room, Label, ProspectLabel, ProspectActionLog, CeleryJobsLog, PostSequence, EngagementCampaignPost, UserLinkedinGroup, Label

# Register your models here.


class LabelAdmin(admin.ModelAdmin):
    list_filter = ("user",)
    search_fields = ("name",)


class ProspectLabelAdmin(admin.ModelAdmin):
    list_filter = ("label",)
    search_fields = ("prospect__name",)


class CampaignAdmin(admin.ModelAdmin):
    list_filter = ("user", "status")
    search_fields = ("name",)


class CampaignSequenceAdmin(admin.ModelAdmin):
    list_filter = ("campaign", "step")
    search_fields = ("step", "note", "message", "inmail_subject",
                     "inmail_message", "email_subject", "email_message")


class CampaignLinkedinAccountAdmin(admin.ModelAdmin):
    list_filter = ("campaign", "linkedin_account")


class SearchParameterAdmin(admin.ModelAdmin):
    list_filter = ("campaign", "parameter")
    search_fields = ("parameter", "value")


class ProspectAdmin(admin.ModelAdmin):
    list_filter = ("campaign_linkedin_account", )  # "state")
    search_fields = ("name", "headline", "location", "email", "phone",
                     "linkedin_profile_url", "linkedin_sales_navigator_profile_url",)  # "state")


class CampaignFailedReasonAdmin(admin.ModelAdmin):
    list_filter = ("campaign",)
    search_fields = ("reason",)


class UserLinkedinConnectionAdmin(admin.ModelAdmin):
    list_filter = ("campaign", "linkedin_account",)
    search_fields = ("linkedin_profile_url",)


class CeleryJobAdmin(admin.ModelAdmin):
    list_filter = ("campaign", "status")
    search_fields = ("task_id",)


class RoomAdmin(admin.ModelAdmin):
    list_filter = ("platform",)
    search_fields = ("message_thread", "prospect__name", "message_thread",)


class MessageAdmin(admin.ModelAdmin):
    list_filter = ("room", "message_from",)
    search_fields = ("message", "room__prospect__name",
                     "room__message_thread",)


class ProspectActionLogAdmin(admin.ModelAdmin):
    list_filter = ("prospect__campaign_linkedin_account__campaign__user", "created_at",)
    search_fields = ("prospect__name",)
    list_display = ("prospect", "action", "created_at",)


admin.site.register(Campaign, CampaignAdmin)
admin.site.register(CampaignLinkedinAccount, CampaignLinkedinAccountAdmin)
admin.site.register(CampaignSequence, CampaignSequenceAdmin)
admin.site.register(SearchParameter, SearchParameterAdmin)
admin.site.register(Prospect, ProspectAdmin)
admin.site.register(CampaignFailedReason, CampaignFailedReasonAdmin)
admin.site.register(UserLinkedinConnection, UserLinkedinConnectionAdmin)
admin.site.register(CeleryJob, CeleryJobAdmin)
admin.site.register(Room, RoomAdmin)
admin.site.register(Message, MessageAdmin)
admin.site.register(ProspectActionLog, ProspectActionLogAdmin)
admin.site.register(CeleryJobsLog)
admin.site.register(PostSequence)
admin.site.register(EngagementCampaignPost)
admin.site.register(UserLinkedinGroup)
admin.site.register(Label)