from django.urls import path
from apps.verifications.views import CaptchaView,SMSCodeView


urlpatterns = [
    path('image_code/',CaptchaView.as_view()),
    path('sms_code/',SMSCodeView.as_view()),
]