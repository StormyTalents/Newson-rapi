from django.urls import path
from .views import (
    CampaignListCreateAPIView, CampaignSequenceListCreateAPIView,
    ProspectListAPIView, SearchParameterListCreateAPIView, MessageListAPIView,
    RunCampaignAPIView, CampaignRetrieveUpdateDestroyAPIView,
    RoomListAPIView, CampaignLinkedinAccountCreateAPIView, EmailWebHookAPIView,
    RoomReadAPIView, LabelListCreateAPIView, LabelRetrieveUpdateDestroyAPIView,
    AssignLabelAPIView, AssignLabelsAPIView, FullInboxCountAPIView,
)


urlpatterns = [
    path('campaigns/', CampaignListCreateAPIView.as_view(),
         name='campaigns_list_create_api_view'),
    path('rooms/', RoomListAPIView.as_view(),
         name='rooms_list_api_view'),
    path('room-readed/<int:room_id>/', RoomReadAPIView.as_view(),
         name='room_readed_api_view'),
    path('campaign-sequences/', CampaignSequenceListCreateAPIView.as_view(),
         name='campaign_sequence_list_create_api_view'),
    path('campaign-linkedin-accounts/', CampaignLinkedinAccountCreateAPIView.as_view(),
         name='campaign_linkedin_account_create_api_view'),
    path('campaigns/<int:id>/', CampaignRetrieveUpdateDestroyAPIView.as_view(),
         name='campaigns_detail_api_view'),
    path('search-parameters/', SearchParameterListCreateAPIView.as_view(),
         name='search_parameter_list_create_api_view'),
    path('prospects/', ProspectListAPIView.as_view(),
         name='prospect_list_api_view'),
    path('messages/', MessageListAPIView.as_view(),
         name='messages_list_api_view'),
    path('labels/', LabelListCreateAPIView.as_view(),
         name='labels_list_api_view'),
    path('labels/<int:id>/', LabelRetrieveUpdateDestroyAPIView.as_view(),
         name='labels_detail'),
    path('assign-label/<str:action>/<int:prospect_id>/<str:label>/', AssignLabelAPIView.as_view(),
         name='labels_list_api_view'),
    path('assign-labels/<int:prospect_id>/', AssignLabelsAPIView.as_view(),
         name='labels_list_api_view'),
    path('trigger/<int:id>/', RunCampaignAPIView.as_view(),
         name='RunCampaignAPIView'),
    path('email-webhook/<uuid:id>/', EmailWebHookAPIView.as_view(),
         name='email_webhook'),
    path('inbox-count/', FullInboxCountAPIView.as_view(),
         name='inbox_count'),
]
