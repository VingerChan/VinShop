from django.urls import path
from apps.orders.views import OrderSettlementView,OrderCommitView,OrderCenterView
urlpatterns = [
    path('order/settlement/', OrderSettlementView.as_view()),
    path('order/commit/', OrderCommitView.as_view()),
    path('orders/',OrderCenterView.as_view()),
]