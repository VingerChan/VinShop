from django.urls import path
from apps.orders.views import OrderSettlementView,OrderCommitView
urlpatterns = [
    path('order/settlement/', OrderSettlementView.as_view()),
    path('order/commit/', OrderCommitView.as_view()),
]