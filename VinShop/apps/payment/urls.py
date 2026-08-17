from django.urls import path
from apps.payment.views import AlipayURLView
urlpatterns = [
    path('payment/alipay/',AlipayURLView.as_view()),
]