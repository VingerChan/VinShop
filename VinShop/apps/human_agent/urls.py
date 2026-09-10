from django.urls import path
from apps.human_agent.views import TransferCreateView, QueuePositionView, SendMessageView, EndSessionView
urlpatterns = [
    path('transfer/create/', TransferCreateView.as_view()),
    path('transfer/queue-position/<str:session_id>/', QueuePositionView.as_view()),
    path('transfer/message/', SendMessageView.as_view()),
    path('transfer/end/', EndSessionView.as_view()),
]