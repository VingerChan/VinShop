from channels.generic.websocket import WebsocketConsumer
import json
from apps.human_agent.models import HumanAgent, HumanAgentSession, HumanAgentMessage
from django.utils import timezone
from apps.human_agent.queue_manager import try_assign_from_queue, WaitingQueue
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

class AgentConsumer(WebsocketConsumer):
    def connect(self):
        # 从ws://host/agent/?token=abc123&user_id=42获取原始查询字符串
        params = dict(p.split('=') for p in self.scope['query_string'].decode().split('&') if '=' in p)
        self.agent_id = params.get('agent_id')    # 后续其他方法还需要用
        agent_name = params.get('agent_name', '')    # 只在本方法用
        max_capacity = int(params.get('max_capacity', 5))
        if not self.agent_id:
            self.send(text_data=json.dumps({
                'code': 4001,
                'reason': '缺少agent_id参数'
            }))
            self.close()
            return
        agent, created = HumanAgent.objects.update_or_create(
            agent_id=self.agent_id,
            defaults={
                'agent_name': agent_name,
                'max_capacity': max_capacity,
                'status': 'online',
                'last_active_at': timezone.now()
            }
        )
        self.agent_name = agent.agent_name
        self.max_capacity = agent.max_capacity
        self.channel_layer.group_add(f"agent_{self.agent_id}", self.channel_name)
        self.accept()
        self.send(text_data=json.dumps({
            'type': 'login_success',
            'agent_id': self.agent_id,
            'max_capacity': self.max_capacity,
        }))
        try_assign_from_queue()

    def disconnect(self, close_code):
        if hasattr(self, 'agent_id') and self.agent_id:
            self.channel_layer.group_discard(
                f"agent_{self.agent_id}", self.channel_name
            )
            try:
                agent = HumanAgent.objects.get(agent_id=self.agent_id)
                agent.status = 'offline'
                agent.save(update_fields=['status'])
            except HumanAgent.DoesNotExist:
                pass
            active_sessions = HumanAgentSession.objects.filter(agent_id=self.agent_id, status='human_active')
            queue = WaitingQueue()
            for session in active_sessions:
                session.status = 'in_queue'
                session.agent = None
                session.save(update_fields=['agent', 'status'])
                queue.enqueue(session.session_id)    # 加入队列
            try_assign_from_queue()

    def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        msg_type = data.get('type')
        if msg_type == 'agent_message':
            self.handle_agent_message(data)
        elif msg_type == 'end_session':
            self.handle_end_session(data)

    # 客服发送消息给用户
    def handle_agent_message(self, data):
        session_id = data.get('session_id')
        content = data.get('content', '')
        message_type = data.get('message_type', 'text')
        metadata = data.get('metadata')
        # 根据session_id查询会话记录
        try:
            session = HumanAgentSession.objects.get(session_id=session_id)
        except HumanAgentSession.DoesNotExist:
            self.send(text_data=json.dumps({
                'type': 'error',
                'code': 4004,
                'reason': '会话不存在'
            }))
            return
        # 校验session是否属于当前客服
        if not session.agent or session.agent.agent_id != self.agent_id:
            self.send(text_data=json.dumps({
                'type': 'error',
                'code': 4005,
                'reason': '无权操作此会话',
            }))
            return
        # 将客服消息持久化到数据库
        HumanAgentMessage.objects.create(
            session=session,
            sender_type='agent',
            sender_id=self.agent_id,
            content=content,
            message_type=message_type,
            metadata=metadata,
        )
        # 更新session的update_time
        session.save(update_fields=['update_time'])
        # 通过Channel Layer向用户端WebSocket推送消息
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"user_{session.user_id}",
            {
                'type': 'user_message',
                'session_id': session_id,
                'content': content,
                'metadata': metadata,
            }
        )

    # 客服结束会话
    def handle_end_session(self, data):
        """客服结束会话"""
        session_id = data.get('session_id')
        reason = data.get('reason', '问题已解决')
        summary = data.get('summary', '')
        # 更新会话状态为已完成
        try:
            session = HumanAgentSession.objects.get(session_id=session_id)
        except HumanAgentSession.DoesNotExist:
            self.send(text_data=json.dumps({
                'type': 'error',
                'code': 4004,
                'reason': '会话不存在'
            }))
            return
        # 校验session是否属于当前客服
        if not session.agent or session.agent.agent_id != self.agent_id:
            self.send(text_data=json.dumps({
                'type': 'error',
                'code': 4005,
                'reason': '无权操作此会话',
            }))
            return
        session.status = 'session_completed'
        session.ended_at = timezone.now()
        session.end_reason = reason
        session.summary = summary
        session.save(update_fields=['status', 'ended_at', 'end_reason', 'summary'])
        # 释放客服容量
        if session.agent:
            agent = session.agent
            agent.current_sessions = max(0, agent.current_sessions - 1)
            if agent.current_sessions < agent.max_capacity:
                agent.status = 'online'
            agent.save(update_fields=['current_sessions', 'status'])
        # 通知用户会话已结束
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"user_{session.user_id}",
            {
                'type': 'session_ended',
                'session_id': session_id,
                'reason': reason,
            }
        )
        # 尝试从排队队列中为其他用户分配客服
        try_assign_from_queue()

    """
            Channel Layer 消息处理器
        当其他代码调用group_send 向 "agent_{agent_id}" 组发消息时，
        Channels 会根据message['type] 找到同名方法并调用
    """
    # 接收新会话分配通知(由assign_agent函数触发)
    def new_assignment(self, event):
        self.send(text_data=json.dumps({
            'type': 'new_assignment',
            'session_id': event['session_id'],
            'user_id': event['user_id'],
            'history': event['history'],
        }))

    # 接收用户发来的消息(由SendMessageView触发)
    def user_message(self, event):
        self.send(text_data=json.dumps({
            'type': 'user_message',
            'session_id': event['session_id'],
            'content': event['content'],
            'metadata': event.get('metadata'),
        }))

    # 接收会话结束通知(由EndSessionView触发)
    def session_ended(self, event):
        self.send(text_data=json.dumps({
            'type': 'session_ended',
            'session_id': event['session_id'],
            'reason': event['reason'],
        }))