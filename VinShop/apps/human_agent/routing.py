from django.urls import re_path
from apps.human_agent import consumers

websocket_urlpatterns = [
    # $表示字符串结尾，以ws/agent结尾
    re_path(r'ws/agent$', consumers.AgentConsumer.as_asgi()),
    re_path(r'ws/user$', consumers.UserConsumer.as_asgi()),
]