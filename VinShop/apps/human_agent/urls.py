from django.urls import path
from apps.human_agent.views import TransferCreateView
urlpatterns = [
    path('transfer/create/', TransferCreateView.as_view()),
]