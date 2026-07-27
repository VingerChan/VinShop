from django.urls import path,include
from apps.users.views import RegisterView,LoginView,ProfileView,CenterVerifySmsView,CenterEmailView,CenterChangeSmsView,CenterChangePswView,AddressViewSet
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

router = DefaultRouter()
# basename是DRF router用来生成URL名称前缀的参数
# 如果AddressViewSet没有设置queryset一开始，则无法自动生成URL名称前缀，所以需要basename
router.register('address',AddressViewSet,basename='address')
urlpatterns = [
    path('register/',RegisterView.as_view()),
    path('login/',LoginView.as_view()),
    path('profile/',ProfileView.as_view()),
    path('token/refresh/',TokenRefreshView.as_view()),
    path('center/sms/',CenterVerifySmsView.as_view()),
    path('center/sms/change/',CenterChangeSmsView.as_view()),
    path('center/email/',CenterEmailView.as_view()),
    path('center/psw/',CenterChangePswView.as_view()),
    path('',include(router.urls)),
]