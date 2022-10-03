from unicodedata import category
from rest_framework import serializers
from django.contrib.auth.models import User
from accounts.api.serializers import LinkedinAccountSerializer
from main.models import Campaign, Prospect, ProspectLabel, SearchParameter, CampaignSequence, Message, Room, CampaignLinkedinAccount, Label
from django.utils.timesince import timesince


class CampaignSerializer(serializers.ModelSerializer):

    total_prospects_crawled = serializers.SerializerMethodField()
    total_prospects_lead = serializers.SerializerMethodField()
    total_prospects_customer = serializers.SerializerMethodField()
    total_prospects_fully_crawled = serializers.SerializerMethodField()
    total_connection_request_sent = serializers.SerializerMethodField()
    total_connection_request_accepted = serializers.SerializerMethodField()
    message_sent = serializers.SerializerMethodField()
    inmail_sent = serializers.SerializerMethodField()
    email_sent = serializers.SerializerMethodField()
    liked_posts = serializers.SerializerMethodField()
    followed = serializers.SerializerMethodField()
    endorsed = serializers.SerializerMethodField()
    connected_prospect_avatars = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    assigned = serializers.SerializerMethodField()
    total_steps_count = serializers.SerializerMethodField()

    class Meta:
        model = Campaign
        fields = "__all__"
        read_only_fields = ("created_at", "updated_at",
                            "user", "status", "pages_crawled")
        
    def get_total_steps_count(self, instance):
        return instance.campaignsequence_set.count()

    def get_category(self, instance):
        if instance.search_url and "/sales/" in instance.search_url:
            return "Linkedin Sales"

        return "Linkedin"
    
    def get_connected_prospect_avatars(self, instance):
        return [{"avatar" : prospect.linkedin_avatar.url, "name" : prospect.name} for prospect in Prospect.objects.filter(campaign_linkedin_account__campaign=instance, fully_crawled=True, connected = True, linkedin_avatar__isnull=False).exclude(linkedin_avatar__exact='')[:4]]

    def get_progress(self, instance):
        return int((Prospect.objects.filter(campaign_linkedin_account__campaign=instance, fully_crawled=True).count() / instance.crawl_total_prospects) * 100)

    def get_total_prospects_fully_crawled(self, instance):
        return Prospect.objects.filter(campaign_linkedin_account__campaign=instance, fully_crawled=True).count()

    def get_assigned(self, instance):
        return CampaignLinkedinAccount.objects.filter(campaign = instance, linkedin_account__avatar__isnull=False).distinct().values("linkedin_account__name", "linkedin_account__avatar")[:7]

    def get_total_prospects_crawled(self, instance):
        return Prospect.objects.filter(campaign_linkedin_account__campaign=instance).count()
    
    def get_total_prospects_lead(self, instance):
        return ProspectLabel.objects.filter(prospect__campaign_linkedin_account__campaign=instance, label__name="Lead").count()
    
    def get_total_prospects_customer(self, instance):
        return ProspectLabel.objects.filter(prospect__campaign_linkedin_account__campaign=instance, label__name="Customer").count()

    def get_total_connection_request_sent(self, instance):
        return Prospect.objects.filter(campaign_linkedin_account__campaign=instance, connection_request_sent=True).count()

    def get_total_connection_request_accepted(self, instance):
        return Prospect.objects.filter(campaign_linkedin_account__campaign=instance, connection_request_sent=True, connected=True).count()

    def get_message_sent(self, instance):
        message_sent = 0

        for prospect in Prospect.objects.filter(campaign_linkedin_account__campaign=instance, connection_request_sent=True, connected=True, state__isnull=False).all().distinct():

            for campaign_sequence in CampaignSequence.objects.filter(campaign=instance, order__lt=prospect.state.order):

                if campaign_sequence.step == "send_message":
                    message_sent += 1

            if prospect.state.step == "send_message" and prospect.state_status and prospect.state_status == "Finished":
                    message_sent += 1

        return message_sent
    
    def get_inmail_sent(self, instance):
        inmail_sent = 0

        for prospect in Prospect.objects.filter(campaign_linkedin_account__campaign=instance, fully_crawled=True, state__isnull=False).all().distinct():

            for campaign_sequence in CampaignSequence.objects.filter(campaign=instance, order__lt=prospect.state.order):

                if campaign_sequence.step == "send_inmail":
                    inmail_sent += 1

            if prospect.state.step == "send_inmail" and prospect.state_status and prospect.state_status == "Finished":
                    inmail_sent += 1

        return inmail_sent

    def get_email_sent(self, instance):
        email_sent = 0

        for prospect in Prospect.objects.filter(campaign_linkedin_account__campaign=instance, fully_crawled=True, email__isnull=False, state__isnull=False).all().distinct():

            for campaign_sequence in CampaignSequence.objects.filter(campaign=instance, order__lt=prospect.state.order):

                if campaign_sequence.step == "send_email":
                    email_sent += 1

            if prospect.state.step == "send_email" and prospect.state_status and prospect.state_status == "Finished":
                    email_sent += 1

        return email_sent

    def get_liked_posts(self, instance):
        liked_posts = 0

        for prospect in Prospect.objects.filter(campaign_linkedin_account__campaign=instance, fully_crawled=True, state__isnull=False).all().distinct():

            for campaign_sequence in CampaignSequence.objects.filter(campaign=instance, order__lt=prospect.state.order):

                if campaign_sequence.step == "like_3_posts":
                    liked_posts += 1

            if prospect.state.step == "like_3_posts" and prospect.state_status and prospect.state_status == "Finished":
                    liked_posts += 1

        return liked_posts*3

    def get_followed(self, instance):
        followed = 0

        for prospect in Prospect.objects.filter(campaign_linkedin_account__campaign=instance, fully_crawled=True, state__isnull=False).all().distinct():

            for campaign_sequence in CampaignSequence.objects.filter(campaign=instance, order__lt=prospect.state.order):

                if campaign_sequence.step == "follow":
                    followed += 1

            if prospect.state.step == "follow" and prospect.state_status and prospect.state_status == "Finished":
                    followed += 1

        return followed
    
    def get_endorsed(self, instance):
        endorsed = 0

        for prospect in Prospect.objects.filter(campaign_linkedin_account__campaign=instance, fully_crawled=True, state__isnull=False).all().distinct():

            for campaign_sequence in CampaignSequence.objects.filter(campaign=instance, order__lt=prospect.state.order):

                if campaign_sequence.step == "endorse_top_5_skills":
                    endorsed += 1

            if prospect.state.step == "endorse_top_5_skills" and prospect.state_status and prospect.state_status == "Finished":
                    endorsed += 1

        return endorsed*5


class CampaignRetrieveSerializer(serializers.ModelSerializer):

    class Meta:
        model = Campaign
        fields = ["status"]


class CampaignSequenceSerializer(serializers.ModelSerializer):

    class Meta:
        model = CampaignSequence
        fields = "__all__"
        read_only_fields = ("created_at", "updated_at",)


class CampaignLinkedinAccountSerializer(serializers.ModelSerializer):

    class Meta:
        model = CampaignLinkedinAccount
        fields = "__all__"
        read_only_fields = ("created_at", "updated_at",)

    def __init__(self, *args, **kwargs):

        super(CampaignLinkedinAccountSerializer, self).__init__(*args, **kwargs)

        self.fields["campaign"].queryset = self.context["campaigns"]
        self.fields["linkedin_account"].queryset = self.context["linkedin_accounts"]


class ProspectSerializer(serializers.ModelSerializer):
    statuses = serializers.SerializerMethodField()
    labels = serializers.SerializerMethodField()

    class Meta:
        model = Prospect
        fields = "__all__"
        read_only_fields = ("created_at", "updated_at",)
        
    def get_labels(self, instance):
        return ProspectLabel.objects.filter(prospect = instance).values("id", "label_id", "label__name")

    def get_statuses(self, instance):

        statuses = []
        
        if not instance.state:
            return [
                {"status": "Pending", "color": "#FFB020"}
            ]
        
        for campaign_sequence in CampaignSequence.objects.filter(campaign=instance.campaign_linkedin_account.campaign, order__lt = instance.state.order).order_by("order"):

            if campaign_sequence.step == "send_connection_request":
                statuses.append(
                    {"status": "Connection Request Sent" if not instance.connected else "Connected", "color": "rgb(16, 185, 129)"})
                    
            elif campaign_sequence.step == "send_message":
                statuses.append(
                    {"status": "Message Sent", "color": "rgb(16, 185, 129)"})

            elif campaign_sequence.step == "send_inmail":
                statuses.append(
                    {"status": "InMail Sent", "color": "rgb(16, 185, 129)"})

            elif campaign_sequence.step == "like_3_posts":
                statuses.append(
                    {"status": "Liked 3 Posts", "color": "rgb(16, 185, 129)"})

            elif campaign_sequence.step == "follow":
                statuses.append(
                    {"status": "Followed", "color": "rgb(16, 185, 129)"})

            elif campaign_sequence.step == "endorse_top_5_skills":
                statuses.append(
                    {"status": "Endorsed", "color": "rgb(16, 185, 129)"})

            elif campaign_sequence.step == "send_email":
                statuses.append(
                    {"status": "Email Sent", "color": "rgb(16, 185, 129)"})
                
        if instance.state.step == "send_connection_request":
            
            if instance.state_status == "Performing" or not instance.state_status:
                statuses.append(
                    {"status": "Sending Connection Request", "color": "#5048E5"})

            elif instance.state_status == "Finished":
                statuses.append({"status": "Connection Request Sent" if not instance.connected else "Connected", "color": "rgb(16, 185, 129)"})

            elif instance.state_status == "Failed":
                statuses.append(
                    {"status": "Connection Request Failed", "color": "#D14343"})
                
        elif instance.state.step == "send_message":
            
            if instance.state_status == "Performing" or not instance.state_status:
                statuses.append(
                    {"status": "Sending Message", "color": "#5048E5"})

            elif instance.state_status == "Finished":
                statuses.append(
                    {"status": "Message Sent", "color": "rgb(16, 185, 129)"})

            elif instance.state_status == "Failed":
                statuses.append(
                    {"status": "Sending Message Failed", "color": "#D14343"})

        elif instance.state.step == "send_inmail":
            
            if instance.state_status == "Performing" or not instance.state_status:
                statuses.append(
                    {"status": "Sending Inmail", "color": "#5048E5"})

            elif instance.state_status == "Finished":
                statuses.append(
                    {"status": "Inmail Sent", "color": "rgb(16, 185, 129)"})

            elif instance.state_status == "Failed":
                statuses.append(
                    {"status": "Sending Inmail Failed", "color": "#D14343"})

        elif instance.state.step == "like_3_posts":
            
            if instance.state_status == "Performing" or not instance.state_status:
                statuses.append(
                    {"status": "Liking Posts", "color": "#5048E5"})

            elif instance.state_status == "Finished":
                statuses.append(
                    {"status": "Liked 3 Posts", "color": "rgb(16, 185, 129)"})

            elif instance.state_status == "Failed":
                statuses.append(
                    {"status": "Liking Post Failed", "color": "#D14343"})

        elif instance.state.step == "follow":
            if instance.state_status == "Performing" or not instance.state_status:
                statuses.append(
                    {"status": "Following Prospect", "color": "#5048E5"})

            elif instance.state_status == "Finished":
                statuses.append(
                    {"status": "Followed", "color": "rgb(16, 185, 129)"})

            elif instance.state_status == "Failed":
                statuses.append(
                    {"status": "Following Prospect Failed", "color": "#D14343"})

        elif instance.state.step == "endorse_top_5_skills":
            if instance.state_status == "Performing" or not instance.state_status:
                statuses.append(
                    {"status": "Endorsing Prospect", "color": "#5048E5"})

            elif instance.state_status == "Finished":
                statuses.append(
                    {"status": "Endorsed", "color": "rgb(16, 185, 129)"})

            elif instance.state_status == "Failed":
                statuses.append(
                    {"status": "Endorsing Failed", "color": "#D14343"})

        elif instance.state.step == "send_email":
            if instance.state_status == "Performing" or not instance.state_status:
                statuses.append(
                    {"status": "Sending Email", "color": "#5048E5"})

            elif instance.state_status == "Finished":
                statuses.append(
                    {"status": "Email Sent", "color": "rgb(16, 185, 129)"})

            elif instance.state_status == "Failed":
                statuses.append(
                    {"status": "Sending Email Failed", "color": "#D14343"})

        return statuses


class SearchParameterSerializer(serializers.ModelSerializer):

    class Meta:
        model = SearchParameter
        fields = "__all__"
        read_only_fields = ("created_at", "updated_at",)


class MessageSerializer(serializers.ModelSerializer):

    class Meta:
        model = Message
        fields = "__all__"
        read_only_fields = ("created_at", "updated_at", "message_from",)


class RoomSerializer(serializers.ModelSerializer):
    last_message = serializers.SerializerMethodField()
    linkedin_account_name = serializers.SerializerMethodField()
    total_customer_messages = serializers.SerializerMethodField()
    prospect_details = serializers.SerializerMethodField()
    prospect_labels = serializers.SerializerMethodField()
    campaign_details = serializers.SerializerMethodField()
    linkedin_account = LinkedinAccountSerializer(read_only=True)

    class Meta:
        model = Room
        fields = "__all__"
        
    def get_prospect_labels(self, instance):
        return ProspectLabel.objects.filter(prospect = instance.prospect).values("id", "label_id", "label__name") if instance.prospect else []

    def get_last_message(self, instance):
        messages = instance.messages.all().order_by("-created_at")

        message_count = 0

        for message in messages:

            if message.message_from == "User":
                break

            message_count += 1

        if messages.first():
            return {"message": messages.first().message, "time": messages.first().time, "message_count": message_count}

        return {"message": "", "time": "", "message_count": 0}


    def get_linkedin_account_name(self, instance):
        return instance.linkedin_account.name
    
    def get_prospect_details(self, instance):
        return Prospect.objects.filter(id = instance.prospect.id).values()[0] if instance.prospect else {}
   
    def get_campaign_details(self, instance):
        return Campaign.objects.filter(id = instance.prospect.campaign_linkedin_account.campaign.id).values()[0] if instance.prospect and instance.prospect.campaign_linkedin_account and instance.prospect.campaign_linkedin_account.campaign else {}
    
    def get_total_customer_messages(self, instance):
        return instance.messages.filter(message_from="Prospect").count()
    

class LabelSerializer(serializers.ModelSerializer):

    class Meta:
        model = Label
        fields = "__all__"
        read_only_fields = ("created_at", "updated_at", "user", "default_label")
        

class AssignLabelsSerializer(serializers.Serializer):
    labels = serializers.ListField(allow_empty=True)