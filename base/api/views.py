from django.shortcuts import get_object_or_404
from .serializers import CountrySerializer, WhiteLabelSerializer, PublicWhiteLabelSerializer
from rest_framework import filters
from base.models import Country, WhiteLabel
from rest_framework.generics import ListAPIView, ListCreateAPIView, RetrieveUpdateAPIView, RetrieveAPIView, RetrieveDestroyAPIView
from rest_framework.views import APIView, Response, status
from rest_framework.permissions import IsAuthenticatedOrReadOnly, AllowAny
import subprocess


class CountryListAPIView(ListAPIView):
    serializer_class = CountrySerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name',]

    def get_queryset(self):
        
        if not self.request.GET.get("custom_proxy"):
            return Country.objects.filter(proxy__isnull = False, proxy__linkedin_proxy__isnull=True).distinct()
        else:
            return Country.objects.all()


class WhiteLabelListCreateAPIView(ListCreateAPIView):
    serializer_class = WhiteLabelSerializer

    def perform_create(self, serializer):
        serializer.save(admin = self.request.user)

    def get_queryset(self):
        if self.request.user.is_superuser:
            return WhiteLabel.objects.all()
        return WhiteLabel.objects.filter(admin = self.request.user)


class ClientWhiteLabelRetrieveAPIView(RetrieveAPIView):
    serializer_class = PublicWhiteLabelSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        return get_object_or_404(WhiteLabel, domain = self.kwargs["domain"])


class WhiteLabelRetrieveUpdateAPIView(RetrieveDestroyAPIView):
    serializer_class = WhiteLabelSerializer

    def get_object(self):
        return get_object_or_404(WhiteLabel, id = self.kwargs["id"], admin = self.request.user) if not self.request.user.is_superuser else get_object_or_404(WhiteLabel, id = self.kwargs["id"])


class GenerateSSL(APIView):
    
    def get(self, request, whitelabel_id, format=None):
        return Response({})
    
    def post(self, request, whitelabel_id, format=None):
        whitelabel = get_object_or_404(WhiteLabel, id = whitelabel_id, admin = self.request.user) if not self.request.user.is_superuser else get_object_or_404(WhiteLabel, id = whitelabel_id)
        
        try:    
            result = subprocess.run(["sudo", "certbot", "--nginx", "-d", f"{whitelabel.domain}", "-n", "--redirect"], capture_output=True, text=True)
            returncode = result.returncode
        except FileNotFoundError as e:
            print(e)
            returncode = 127

        if returncode == 0:
            whitelabel.ssl_generated = True
            whitelabel.save()
            return Response({
                "ssl_generated": True
            }, status=status.HTTP_200_OK)
            
        else:
            return Response({
                "ssl_generated": False
            }, status=status.HTTP_400_BAD_REQUEST)
        