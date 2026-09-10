"""
ASGI config for VinShop project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VinShop.settings')

django_asgi_app = get_asgi_application()

from apps.human_agent.routing import websocket_urlpatterns

# 所有WebSocket请求先经过AuthMiddlewareStack处理认证；再经过URLRouter匹配URL路径
# 最终到达AgentConsumer
# ProtocolTypeRouter根据连接协议类型做路由分发
application = ProtocolTypeRouter({
    'http': django_asgi_app,    # 所有HTTP请求走Django标准处理
    'websocket': AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})
