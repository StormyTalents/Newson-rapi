from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView, status
from rest_framework.generics import (
    ListAPIView, ListCreateAPIView,GenericAPIView,
    RetrieveAPIView, RetrieveUpdateAPIView
)
from rest_framework.permissions import AllowAny
from rest_framework.generics import CreateAPIView, RetrieveUpdateAPIView, RetrieveUpdateDestroyAPIView
from accounts.models import UserProfile, GoogleAccount, SmtpAccount, LinkedinAccount, User, Plan, License, ImportLinkedinAccount
from base.models import WhiteLabel
from .serializers import (
    UserRegisterSerializer, ConnectLinkedinAccountSerializer,
    ConnectLinkedinAccountVerificationCodeSerializer, GoogleEmailCodeSerializer,
    UserProfileSerializer, LinkedinAccountSerializer, SmtpAccountSerializer,
    GoogleAccountSerializer, AppSumoNotificationSerializer, LicenseSerializer,
    UserSerializer, MyTokenObtainPairSerializer, BulkImportLinkedinAccountsSerializer,
    ReConnectLinkedinAccountSerializer, LinkedinAccountRetrieveSerializer
)
from .utils import connect_your_linkedin, connect_your_linkedin_with_verification_code, test_smtp_server, get_tokens_for_user, check_if_proxy_works
from django.conf import settings
import requests
from rest_framework import serializers
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .permissions import MustBeAppSumoUserPermission
from .tasks import import_linkedin_accounts
from rest_framework_simplejwt.views import TokenViewBase, TokenError, InvalidToken
import pandas as pd
import numpy as np


class MyTokenObtainPairView(TokenViewBase):
    serializer_class = MyTokenObtainPairSerializer
    
    def post(self, request, *args, **kwargs):
        whitelabel = get_object_or_404(WhiteLabel, id = request.GET.get("whitelabel"))
        serializer = self.get_serializer(data=request.data, context={"whitelabel" : whitelabel})

        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0])

        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class AppSumoPartnerNotification(GenericAPIView):
    serializer_class = AppSumoNotificationSerializer
    permission_classes = [IsAuthenticated, MustBeAppSumoUserPermission]

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)

        serializer.is_valid(raise_exception=True)

        action = serializer.validated_data["action"]
        plan_id = serializer.validated_data["plan_id"]
        uuid = serializer.validated_data["uuid"]
        activation_email = serializer.validated_data["activation_email"]
        invoice_item_uuid = serializer.validated_data.get("invoice_item_uuid", None)

        if (action == "activate" or action == "refund") and not invoice_item_uuid:
            raise serializers.ValidationError({ "invoice_item_uuid" : "This Field Is Required!" })

        plan = get_object_or_404(Plan, code = plan_id)
        license = License.objects.create(plan = plan, license_product_key = uuid, activation_email = activation_email, invoice_item_uuid = invoice_item_uuid)

        return Response({
            "message": "product activated",
            "redirect_url": f"{settings.FE_HOST}/app-sumo-signup?l={license.id}&source=appsumo"
        }, status=status.HTTP_201_CREATED)


class LicenseRetrieveAPIView(RetrieveAPIView):
    permission_classes = [AllowAny]
    serializer_class = LicenseSerializer

    def get_object(self):
        return get_object_or_404(License, id = self.kwargs.get("id"), userprofile__isnull = True)


class UserRegisterCreateAPIView(CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = UserRegisterSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"]  = self.request
        context["whitelabel"]  = self.request.GET.get("whitelabel")
        return context


class UserProfileRetrieveUpdateAPIView(RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer

    def get_object(self):
        return UserProfile.objects.get(user=self.request.user)


class UserInfoAPIView(APIView):

    def get(self, request, format=None):
        return Response({
            "id": request.user.id,
            "username": request.user.username,
            "email": request.user.email,
            "is_superuser": request.user.is_superuser,
            "linkedin_connected_account" : LinkedinAccount.objects.filter(profile = request.user.userprofile, connected=True).count(),
            "linkedin_connected_accounts" : LinkedinAccount.objects.filter(profile = request.user.userprofile, connected=True).values("id", "username", "name", "avatar", "profile_url", "ready_for_use", "connected"),
            "google_connected_accounts": GoogleAccount.objects.filter(profile = request.user.userprofile, connected=True).values("id", "profile_id", "name", "email", "connected"),
            "smtp_connected_accounts": SmtpAccount.objects.filter(profile = request.user.userprofile, connected=True).values("id", "profile_id", "username", "server", "port", "ssl", "connected"),
            "google_accounts": GoogleAccount.objects.filter(profile = request.user.userprofile).values(),
            "smtp_accounts": SmtpAccount.objects.filter(profile = request.user.userprofile).values(),
            "linkedin_accounts": LinkedinAccount.objects.filter(profile = request.user.userprofile).values("id", "username", "name", "avatar", "profile_url", "ready_for_use", "connected"),
            "plan":  License.objects.filter(id = request.user.userprofile.plan.id).values("plan__name", "plan__linkedin_and_email_accounts", "plan__prospects_per_month", "plan__white_label")[0] if request.user.userprofile.plan else {},
        })


class LinkedinAccountListAPIView(ListAPIView):
    serializer_class = LinkedinAccountSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['username', "name",]
    filterset_fields = ['proxy', 'connected', 'ready_for_use', ]

    def get_queryset(self):
        return LinkedinAccount.objects.filter(profile = self.request.user.userprofile)
    

class LinkedinAccountRetriveUpdateAPIView(RetrieveUpdateAPIView):
    serializer_class = LinkedinAccountRetrieveSerializer
    
    def perform_update(self, serializer):
        instance = self.get_object()
        
        country = serializer.validated_data.get("country", None)
        
        if country:
            serializer.validated_data["proxy"] = country.proxy_set.filter(linkedin_proxy__isnull=True).first()            
            
        return serializer.save()

    def get_object(self):
        return get_object_or_404(LinkedinAccount, profile = self.request.user.userprofile, id = self.kwargs.get("id"))


class UsersListAPIView(ListAPIView):
    serializer_class = UserSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['username', "email",]
    permission_classes = [IsAdminUser]
    # filterset_fields = ['proxy', 'connected', 'ready_for_use', ]

    def get_queryset(self):
        return User.objects.all()


class UserRetrieveUpdateDestroyAPIView(RetrieveUpdateDestroyAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]
    lookup_field = "id"
    queryset = User.objects.all()


class LoginAsAPIView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, id, format=None):
        user = get_object_or_404(User, id = id)
        return Response(get_tokens_for_user(user), status=status.HTTP_200_OK)


class ConnectYourLinkedinAccountAPIView(APIView):
    serializer_class = ConnectLinkedinAccountSerializer
    verification_lookup = "verification_code"
    reconnect_lookup = "reconnect"

    def get_serializer_class(self):
        if self.request.GET.get(self.verification_lookup):
            return ConnectLinkedinAccountVerificationCodeSerializer
        elif self.request.GET.get(self.reconnect_lookup):
            return ReConnectLinkedinAccountSerializer
        else:
            return self.serializer_class

    def get(self, request, format=None):
        return Response({}, status=status.HTTP_200_OK)

    def post(self, request, format=None):
        serializer = self.get_serializer_class()(data=request.data)

        if serializer.is_valid():
            username = serializer.validated_data.get("username")
            password = serializer.validated_data.get("password")
            reconnect = request.GET.get(self.reconnect_lookup)
            country = serializer.validated_data.get("country")
            timezone = serializer.validated_data.get("timezone")
            from_hour = serializer.validated_data.get("from_hour")
            to_hour = serializer.validated_data.get("to_hour")
            code = serializer.validated_data.get("code")
            
            use_custom_proxy = serializer.validated_data.get("use_custom_proxy")
            custom_proxy_username = serializer.validated_data.get("custom_proxy_username")
            custom_proxy_password = serializer.validated_data.get("custom_proxy_password")
            custom_proxy_server = serializer.validated_data.get("custom_proxy_server")
            custom_proxy_port = serializer.validated_data.get("custom_proxy_port")
            proxy = {}
            
            if use_custom_proxy:
                proxy["username"] = custom_proxy_username
                proxy["password"] = custom_proxy_password
                proxy["server"] = custom_proxy_server
                proxy["port"] = custom_proxy_port
                proxy["country"] = country
                
                if not check_if_proxy_works(proxy):
                    raise serializers.ValidationError({ "proxy" : "Invalid Proxy Please Check Your Proxy Settings!" })
            
            elif country:
                newProxy = country.proxy_set.filter(linkedin_proxy__isnull=True).first()
                proxy["id"] = newProxy.id
                proxy["username"] = newProxy.username
                proxy["password"] = newProxy.password
                proxy["server"] = newProxy.server
                proxy["port"] = newProxy.port
                proxy["country"] = newProxy.country
                
                
            
            linkedin_account = serializer.validated_data.get("linkedin_account")
            email_verification = request.GET.get(self.verification_lookup)
            
            if username and not reconnect:
                linkedin_account_exist = LinkedinAccount.objects.filter(username = username, profile=request.user.userprofile).first()

                if linkedin_account_exist:
                    raise serializers.ValidationError({ "msg" : "This Linkedin Account Is Already Added!" })
            
            if reconnect and linkedin_account:
                linkedin_account = get_object_or_404(LinkedinAccount, id = linkedin_account, profile = request.user.userprofile)
                
                if username and password:
                    connected, msg, linkedin_account = connect_your_linkedin(
                        request, username, password,
                        linkedin_account.timezone, linkedin_account.from_hour, linkedin_account.to_hour,
                        linkedin_account.get_proxy, linkedin_account
                    )
                else:
                    connected, msg, linkedin_account = connect_your_linkedin(
                        request, linkedin_account.username, linkedin_account.password,
                        linkedin_account.timezone, linkedin_account.from_hour, linkedin_account.to_hour,
                        linkedin_account.get_proxy, linkedin_account
                    )
                
            elif email_verification and code and linkedin_account:
                linkedin_account = get_object_or_404(LinkedinAccount, id = linkedin_account, profile = request.user.userprofile)
                connected, msg = connect_your_linkedin_with_verification_code(request, code, linkedin_account)
                
            else:
                connected, msg, linkedin_account = connect_your_linkedin(
                    request, username, password,
                    timezone, from_hour, to_hour,
                    proxy,
                )

            return Response({
                "connected": connected,
                "linkedin_account": LinkedinAccount.objects.filter(id=linkedin_account.id).values()[0] if linkedin_account else {},
                "msg": msg,
                "error": True if msg else False
            }, status=status.HTTP_200_OK if connected else status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SmtpAccountListCreateAPIView(ListCreateAPIView):
    serializer_class = SmtpAccountSerializer

    def perform_create(self, serializer):
        try:
            test_smtp_server(
                serializer.validated_data["server"],
                serializer.validated_data["port"],
                serializer.validated_data["username"],
                serializer.validated_data["password"],
                serializer.validated_data["ssl"],
            )
            serializer.save(profile = self.request.user.userprofile, connected = True)
        except Exception as e:
            raise serializers.ValidationError({"smtp": "No Connection Could Be Made Please Check Your Smtp Settings."})

    def get_queryset(self):
        return SmtpAccount.objects.filter(profile = self.request.user.userprofile)


class GoogleAccountListAPIView(ListAPIView):
    serializer_class = GoogleAccountSerializer

    def get_queryset(self):
        return GoogleAccount.objects.filter(profile = self.request.user.userprofile)


class GoogleEmailCodeAPIView(APIView):
    serializer_class = GoogleEmailCodeSerializer

    def google_get_access_token(self, code: str, redirect_uri: str) -> str:

        data = {
            'code': code,
            'client_id': settings.GOOGLE_OAUTH2_CLIENT_ID,
            'client_secret': settings.GOOGLE_OAUTH2_CLIENT_SECRET,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code'
        }

        response = requests.post(
            "https://oauth2.googleapis.com/token", data=data)

        if not response.ok:
            return False

        print(response.json())

        access_token = response.json()['access_token']
        refresh_token = response.json()['refresh_token']
        id_token = response.json()['id_token']

        return (access_token, refresh_token, id_token)

    def get_google_account_info(self, access_token: str) -> dict:

        response = requests.get(
            "https://www.googleapis.com/oauth2/v1/userinfo", params={
                "access_token": access_token
            })

        if not response.ok:
            return {}

        return response.json()

    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            code = serializer.validated_data.get("code")
            redirect_uri = serializer.validated_data.get("redirect_uri")
            tokens = self.google_get_access_token(code, redirect_uri)

            if tokens:
                user_info = self.get_google_account_info(tokens[0]) # access token
                google_account, created = GoogleAccount.objects.get_or_create(name = user_info["name"], email = user_info["email"], profile = self.request.user.userprofile)
                google_account.access_token = tokens[0] # access token
                google_account.refresh_token = tokens[1] # refresh token
                google_account.id_token = tokens[2] # id token
                google_account.connected = True
                google_account.save()

            return Response({"connected": True if tokens else False}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DisconnectAPIView(APIView):

    def post(self, request, linkedin_account_id, format=None):
        linkedin_account = get_object_or_404(LinkedinAccount, id = linkedin_account_id, profile = request.user.userprofile)
        linkedin_account.ready_for_use = False
        linkedin_account.connected = False
        linkedin_account.save()

        return Response({}, status=status.HTTP_200_OK)
    
    

class BulkImportLinkedinAccountsAPIView(APIView):
    serializer_class = BulkImportLinkedinAccountsSerializer
    
    def get(self, request, format=None):
        return Response({}, status=status.HTTP_200_OK)

    def post(self, request, format=None):
        serializer = self.serializer_class(data = request.data or request.POST)
        serializer.is_valid(raise_exception=True)
        
        df = pd.read_csv(serializer.validated_data["csv_file"])
        df = df.replace(' ', np.nan) # to get rid of empty values

        columns = [
            {
                "name": "Linkedin Email *",
                "no_empty_values": True,
            },
            { 
                "name" : "Linkedin Password *",
                "no_empty_values": True,
            },
            {
                "name" : "Linkedin Email Password *",
                "no_empty_values": True,
            },
            {
                "name" : "Linkedin Email Recovery Email *",
                "no_empty_values": True,
            },
            {
                "name" : "Country *",
                "no_empty_values": True,
            },
            {
                "name" : "IMAP Host"
            },
            {
                "name" : "IMAP Port"
            }
        ]
        
        for column in columns:
            
            if not column["name"] in df.columns:
                raise serializers.ValidationError({ "column": f'Please make sure csv file has "{column["name"]}" column!' })

            if pd.isna(df[column["name"]]).any() and column.get("no_empty_values", False):
                raise serializers.ValidationError({ "column": f'Please make sure "{column["name"]}" column has no empty values!' })
        
        df["IMAP Host"] = df["IMAP Host"].fillna('')
        df["IMAP Port"] = df["IMAP Port"].fillna(993)
        import_linkeidn_account = ImportLinkedinAccount.objects.create(
            profile = request.user.userprofile,
            csv = serializer.validated_data["csv_file"],
            csv_name = serializer.validated_data["csv_file"].name,
            total_rows = len(df.index),
        )
        
        import_linkedin_accounts.delay(f"{request.user.userprofile.id}", f"{import_linkeidn_account.id}", df.to_dict('records'))

        return Response({}, status=status.HTTP_200_OK)