from django.urls import path
from apps.users.views import RegisterView,LoginView,ProfileView,SendSmsEmailView,VerifySmsEmailView,SendEmailCodeView,VerifyEmailCodeView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('register/',RegisterView.as_view()),
    path('login/',LoginView.as_view()),
    path('profile/',ProfileView.as_view()),
    path('token/refresh/',TokenRefreshView.as_view()),
    path('email/sms/',SendSmsEmailView.as_view()),
    path('email/sms/verify/',VerifySmsEmailView.as_view()),
    path('email/',SendEmailCodeView.as_view()),
    path('email/verify/',VerifyEmailCodeView.as_view()),
]