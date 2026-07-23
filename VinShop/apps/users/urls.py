from django.urls import path
from apps.users.views import RegisterView,LoginView,ProfileView,CenterSmsView,CenterEmailView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('register/',RegisterView.as_view()),
    path('login/',LoginView.as_view()),
    path('profile/',ProfileView.as_view()),
    path('token/refresh/',TokenRefreshView.as_view()),
    path('center/sms/',CenterSmsView.as_view()),
    path('center/email/',CenterEmailView.as_view()),
]