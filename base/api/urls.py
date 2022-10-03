from django.urls import path
from .views import CountryListAPIView, WhiteLabelListCreateAPIView, ClientWhiteLabelRetrieveAPIView, WhiteLabelRetrieveUpdateAPIView, GenerateSSL


urlpatterns = [
    path('countries/', CountryListAPIView.as_view(), name='countries'),
    path('whitelabels/', WhiteLabelListCreateAPIView.as_view(), name='whitelabels'),
    path('whitelabels/<uuid:id>/', WhiteLabelRetrieveUpdateAPIView.as_view(), name='whitelabel_detail'),
    path('whitelabels/<str:domain>/', ClientWhiteLabelRetrieveAPIView.as_view(), name='client_whitelabel_detail'),
    path('whitelabels/<str:domain>/', ClientWhiteLabelRetrieveAPIView.as_view(), name='client_whitelabel_detail'),
    path('generate-ssl/<uuid:whitelabel_id>/', GenerateSSL.as_view(), name='generate_ssl'),
    
]
