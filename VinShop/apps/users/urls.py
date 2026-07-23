from django.urls import path
from apps.users.views import RegisterView,LoginView,ProfileView,SendSmsEmailView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('register/',RegisterView.as_view()),
    path('login/',LoginView.as_view()),
    path('profile/',ProfileView.as_view()),
    path('token/refresh/',TokenRefreshView.as_view()),
    path('email/sms/',SendSmsEmailView.as_view()),
]