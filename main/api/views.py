from platform import platform
from django.shortcuts import get_object_or_404
from django.db import IntegrityError
from django.db.models import Count, F
from rest_framework.generics import ListCreateAPIView, ListAPIView, RetrieveUpdateDestroyAPIView, CreateAPIView
from .serializers import CampaignSerializer, CampaignRetrieveSerializer, ProspectSerializer, SearchParameterSerializer, MessageSerializer, RoomSerializer, CampaignLinkedinAccountSerializer, LabelSerializer, CampaignSequenceSerializer, AssignLabelsSerializer
from main.models import Campaign, EmailWebHook, Prospect, SearchParameter, CeleryJob, CampaignSequence, Message, Room, Label, ProspectLabel
from accounts.models import LinkedinAccount
from django.contrib.auth.models import User
from rest_framework.views import Response, status, APIView
from rest_framework import serializers
from .tasks import perform_campaign_actions, run_outreach_campaign, check_user_connections, run_check_reply_and_get_conversations, send_message, run_auto_accept_connection_requests, run_post_campaign, crawl_post_campaign_prospects, check_user_groups
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from celery.task.control import revoke
from django.db.models import Q
from rest_framework.permissions import AllowAny
from django.db.models import Sum


class CampaignListCreateAPIView(ListCreateAPIView):
    serializer_class = CampaignSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['name']

    def perform_create(self, serializer):
        return serializer.save(user=self.request.user)

    def get_queryset(self):
        return Campaign.objects.filter(user=self.request.user)


class CampaignLinkedinAccountCreateAPIView(CreateAPIView):
    serializer_class = CampaignLinkedinAccountSerializer
    filter_backends = [DjangoFilterBackend,]
    filterset_fields = ['campaign', 'linkedin_account',]

    def get_serializer_context(self):

        context = super(CampaignLinkedinAccountCreateAPIView, self).get_serializer_context()

        context["campaigns"] = Campaign.objects.filter(user = self.request.user)
        context["linkedin_accounts"] = LinkedinAccount.objects.filter(profile = self.request.user.userprofile)

        return context


class CampaignRetrieveUpdateDestroyAPIView(RetrieveUpdateDestroyAPIView):
    serializer_class = CampaignRetrieveSerializer
    queryset = Campaign.objects.all()

    def perform_destroy(self, instance):
        for job in CeleryJob.objects.filter(campaign=instance):
            print(job)
            revoke(job.task_id, terminate=True)

        return instance.delete()

    def get_object(self):
        return get_object_or_404(Campaign, id=self.kwargs.get("id"), user=self.request.user)


class CampaignSequenceListCreateAPIView(ListCreateAPIView):
    serializer_class = CampaignSequenceSerializer
    # filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    # search_fields = ['name']

    def get_queryset(self):
        return CampaignSequence.objects.filter(campaign__user=self.request.user)


class ProspectListAPIView(ListAPIView):
    serializer_class = ProspectSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['name', "headline", "location",
                     "email", "phone", "campaign_linkedin_account__campaign__name"]
    filterset_fields = ['campaign_linkedin_account__campaign', 'name', 'show_inside_inbox', "prospect_labels__label"]

    def get_queryset(self):
        return Prospect.objects.filter(campaign_linkedin_account__campaign__user=self.request.user).order_by("-updated_at").distinct()


class RoomListAPIView(ListAPIView):
    serializer_class = RoomSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ["prospect__name",]
    filterset_fields = ['platform', "linkedin_account", ]

    def get_queryset(self):
        
        include_campaigns = self.request.GET.get("include_campaigns", "").split(",")
        include_labels = self.request.GET.get("include_labels", "").split(",")
        include_platforms = self.request.GET.get("include_platforms", "").split(",")
        include_message_types = self.request.GET.get("include_message_types", "").split(",")
        include_without_labels = self.request.GET.get("include_without_labels", "")
    
        campaign_filters = Q()
        label_filters = Q()
        platform_filters = Q()
        
        for campaign in include_campaigns:    
            if not campaign: continue
            campaign_filters.add(Q(prospect__campaign_linkedin_account__campaign_id=campaign), Q.OR)
            
        for label in include_labels:
            if not label: continue
            label_filters.add(Q(prospect__prospect_labels__label=label), Q.OR)
            
        for platform in include_platforms:
            if not platform: continue
            platform_filters.add(Q(platform=platform), Q.OR)
       
        if include_without_labels == "true":
            queryset = label_filters.add(Q(prospect__prospect_labels__isnull=True), Q.OR)
       
        queryset = Room.objects.filter(linkedin_account__profile__user=self.request.user).filter(campaign_filters & label_filters & platform_filters).distinct()
        
        if "Readed" in include_message_types:
            queryset = queryset.filter(messages__message_from="Prospect").annotate(diff = Count("messages") - F("customer_message_readed")).filter(diff__lte=0)
            
        if "Unreaded" in include_message_types:
            queryset = queryset.filter(messages__message_from="Prospect").annotate(diff = Count("messages") - F("customer_message_readed")).filter(diff__gt=0)

        return queryset.order_by("-created_at")
    

class RoomReadAPIView(APIView):
    def get(self, request, room_id, format=None):
        return Response({}, status=status.HTTP_200_OK)
        
    def post(self, request, room_id, format=None):
        room = get_object_or_404(Room, id = room_id, linkedin_account__profile__user=self.request.user)
        
        room.customer_message_readed = room.messages.filter(message_from="Prospect").count()
        room.save()
            
        return Response({}, status=status.HTTP_200_OK)


class MessageListAPIView(ListCreateAPIView):
    serializer_class = MessageSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['room__name', "message"]
    filterset_fields = ["room", 'room__linkedin_account',
                        'message_from', 'room__platform']

    def perform_create(self, serializer):
        message = serializer.save(message_from="User")
        send_message.delay(f"{message.id}")

    def get_queryset(self):
        return Message.objects.filter(room__linkedin_account__profile__user=self.request.user).order_by("created_at")


class SearchParameterListCreateAPIView(ListCreateAPIView):
    serializer_class = SearchParameterSerializer
    filter_backends = [filters.SearchFilter]

    def get_queryset(self):
        return SearchParameter.objects.filter(campaign__user=self.request.user)


class RunCampaignAPIView(APIView):

    def get_object(self, id, request):
        return get_object_or_404(Campaign, id=id, user=request.user)

    def get(self, request, id, format=None):

        campaign = self.get_object(id, request)

        return Response({}, status=status.HTTP_200_OK)

    def post(self, request, id, format=None):

        campaign = self.get_object(id, request)

        # check_user_connections()  # run_outreach_campaign.delay(id, request.user.id) #run_outreach_campaign(id, request.user.id)
        # run_outreach_campaign(id, request.user.id)
        # run_check_reply_and_get_conversations()
        
        if campaign.type == "outreach":
            task = run_outreach_campaign.delay(id, request.user.id)
        else:
            task = run_post_campaign.delay(id, request.user.id)
        
        # check_user_groups()
        
        # crawl_post_campaign_prospects()
        
        # check_user_connections()
        
        # run_check_reply_and_get_conversations()
        
        CeleryJob.objects.create(task_id=f"{task.task_id}", campaign=campaign)

        return Response({}, status=status.HTTP_200_OK)


class EmailWebHookAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, id, format=None):
        webhook = get_object_or_404(EmailWebHook, id = id, prospect__email__isnull = True)

        data = request.data

        if data.get("status") == "email_found" and data.get("email"):

            webhook.prospect.email = data["email"]
            webhook.prospect.save()

        return Response({}, status=status.HTTP_200_OK)
    

class LabelListCreateAPIView(ListCreateAPIView):
    serializer_class = LabelSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['name']

    def perform_create(self, serializer):
        try:
            return serializer.save(user=self.request.user)
        except IntegrityError as e:
            raise serializers.ValidationError({ "name" : "Label Must Be Unique!" })

    def get_queryset(self):
        return Label.objects.filter(user=self.request.user)


class LabelRetrieveUpdateDestroyAPIView(RetrieveUpdateDestroyAPIView):
    serializer_class = LabelSerializer

    def get_object(self):
        return get_object_or_404(Label, id = self.kwargs.get("id"), default_label = False)


class AssignLabelAPIView(APIView):

    def post(self, request, action, prospect_id, label, format=None):
        prospect = get_object_or_404(Prospect, id=  prospect_id, campaign_linkedin_account__campaign__user=request.user)
        label, created = Label.objects.get_or_create(user_id = request.user.id, name = label)
        prospect_label = ProspectLabel.objects.filter(prospect = prospect, label = label)
        prospect_label_values = {}
        
        if action == "mark":

            if not prospect_label:
                prospect_label = ProspectLabel.objects.create(prospect = prospect, label = label)
                
            prospect_label_values = ProspectLabel.objects.filter(id = prospect_label.id).values("id", "label_id", "label__name")[0]
                
        if action == "unmark":
            
            prospect_label_values = ProspectLabel.objects.filter(id = prospect_label.first().id).values("id", "label_id", "label__name")[0]
            prospect_label.delete()
        
        return Response(prospect_label_values, status=status.HTTP_200_OK)


class AssignLabelsAPIView(APIView):
    serializer_class = AssignLabelsSerializer

    def put(self, request, prospect_id, format=None):
        prospect = get_object_or_404(Prospect, id=prospect_id, campaign_linkedin_account__campaign__user=request.user)
        serializer = AssignLabelsSerializer(data=request.data or request.POST)
        serializer.is_valid(raise_exception=True)
        
        labels_id = list(set(serializer.validated_data["labels"]))
        prospect_labels = ProspectLabel.objects.filter(prospect = prospect).exclude(label__name="Lead").exclude(label__name="Customer")
        prospect_labels.delete()
        
        for id in labels_id:
            label = Label.objects.filter(id = id, user = request.user).first()
            
            if label:
                ProspectLabel.objects.create(prospect = prospect, label = label)
            
        
        return Response(ProspectLabel.objects.filter(prospect = prospect).values("id", "label_id", "label__name"), status=status.HTTP_200_OK)


class FullInboxCountAPIView(APIView):

    def get(self, request, format=None):
        rooms = Room.objects.filter(linkedin_account__profile__user = request.user).annotate(
            total_customer_messages = Count('messages', filter=Q(messages__message_from="Prospect"))
        ).all()
        
        total_customer_messages = rooms.aggregate(Sum('total_customer_messages'))["total_customer_messages__sum"] or 0
        customer_message_readed = rooms.aggregate(Sum('customer_message_readed'))["customer_message_readed__sum"] or 0
        
        return Response({
            "count": (total_customer_messages - customer_message_readed) or 0
        }, status=status.HTTP_200_OK)
