from django.urls import path
from apps.payment.views import AlipayURLView, AlipayQueryView, AlipayNotifyView
urlpatterns = [
    path('payment/alipay/',AlipayURLView.as_view()),
    path('payment/alipay/status/',AlipayQueryView.as_view()),
    path('payment/alipay/notify/',AlipayNotifyView.as_view()),
]