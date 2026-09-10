from django.urls import path
from apps.human_agent.views import TransferCreateView, QueuePositionView, SendMessageView, EndSessionView, AgentStatusView
urlpatterns = [
    path('transfer/create/', TransferCreateView.as_view()),
    path('transfer/queue-position/<str:session_id>/', QueuePositionView.as_view()),
    path('transfer/message/', SendMessageView.as_view()),
    path('transfer/end/', EndSessionView.as_view()),
    path('transfer/agent/status/', AgentStatusView.as_view()),
]