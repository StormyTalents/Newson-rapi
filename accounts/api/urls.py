from django.urls import path
from .views import UserInfoAPIView, UserRegisterCreateAPIView, ConnectYourLinkedinAccountAPIView, GoogleAccountListAPIView, SmtpAccountListCreateAPIView, GoogleEmailCodeAPIView, UserProfileRetrieveUpdateAPIView, LinkedinAccountListAPIView, AppSumoPartnerNotification, LicenseRetrieveAPIView, UsersListAPIView, UserRetrieveUpdateDestroyAPIView, LoginAsAPIView, MyTokenObtainPairView, DisconnectAPIView, BulkImportLinkedinAccountsAPIView, LinkedinAccountRetriveUpdateAPIView
from rest_framework_simplejwt import views as jwt_views


urlpatterns = [
    path('', UserInfoAPIView.as_view(), name='userinfo'),
    path('license/<uuid:id>/', LicenseRetrieveAPIView.as_view(), name='app_sumo_license'),
    path('sumo-notification/', AppSumoPartnerNotification.as_view(), name='app_sumo_notification'),
    path('profile/', UserProfileRetrieveUpdateAPIView.as_view(), name='userprofile'),
    path('linkedin-accounts/', LinkedinAccountListAPIView.as_view(), name='linkedin_accounts'),
    path('linkedin-accounts/<int:id>/', LinkedinAccountRetriveUpdateAPIView.as_view(), name='linkedin_accounts_detail'),
    path('smtp-accounts/', SmtpAccountListCreateAPIView.as_view(), name='smtp_accounts'),
    path('google-accounts/', GoogleAccountListAPIView.as_view(), name='google_accounts'),
    path('register/', UserRegisterCreateAPIView.as_view(), name='user_register'),
    path('users/', UsersListAPIView.as_view(), name='users'),
    path('users/<int:id>/', UserRetrieveUpdateDestroyAPIView.as_view(), name='user_detail'),
    path('loginas/<int:id>/', LoginAsAPIView.as_view(), name='login_as'),
    path('connect/', ConnectYourLinkedinAccountAPIView.as_view(),
         name='connect_your_linkedin_account'),
    path('disconnect/<int:linkedin_account_id>/', DisconnectAPIView.as_view(), name='disconnect_your_linkedin_account'),
    path('import-bulk-linkedin-accounts/', BulkImportLinkedinAccountsAPIView.as_view(), name='bulk_linkedin_account_connect'),
    path('token/', MyTokenObtainPairView.as_view(),
         name='token_obtain_pair'),
    path('connect-google/',
         GoogleEmailCodeAPIView.as_view(), name='connect_google'),
    path('token/refresh/', jwt_views.TokenRefreshView.as_view(), name='token_refresh'),
]
