from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from apps.human_agent.serializers import TransferCreateSerializer, SendMessageSerializer, EndSessionSerializer
from apps.human_agent.models import HumanAgentSession, HumanAgentMessage, HumanAgent
from rest_framework.response import Response
from rest_framework import status
import uuid
from django.db import transaction
from apps.human_agent.queue_manager import WaitingQueue, assign_agent
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.utils import timezone
from apps.human_agent.queue_manager import try_assign_from_queue

# 创建转接会话
class TransferCreateView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        serializer = TransferCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        user = request.user
        # 检查用户是否已经在等待队列 或 已有活跃会话
        existing = HumanAgentSession.objects.filter(user=user, status__in=['transfer_requested', 'in_queue', 'human_active']).first()
        if existing:
            return Response({
                'error': 'already_in_queue',
                'message': '您已在等待队列中',
                'session_id' : existing.session_id
            }, status=status.HTTP_400_BAD_REQUEST)
        # 取UUID4的前16位进制字符(64位随机性)
        session_id = f"hs_{uuid.uuid4().hex[:16]}"
        with transaction.atomic():
            session = HumanAgentSession.objects.create(
                session_id=session_id,
                user=user,
                ai_chat_history=data.get('ai_chat_history', []),
                status='transfer_requested',
            )
            queue = WaitingQueue()
            queue.enqueue(session_id)    # 加入队列，返回是否成功
            session.status = 'in_queue'
            session.save(update_fields=['status'])
        # 尝试立即分配客服
        agent_id = assign_agent(session_id)
        if agent_id:
            queue_position = 0
            estimated_wait = 0
        else:
            queue = WaitingQueue()
            queue_position = queue.get_position(session_id) or 1
            estimated_wait = queue_position * 60    # 粗略估算每人等待60秒
        return Response({
            'session_id': session_id,
            'status': session.status,
            'queue_position': queue_position,
            'estimated_wait_seconds': estimated_wait,
            'message': (
                f"已为您转接人工客服，您当前排在第{queue_position}位，请稍后..."
                if queue_position > 0 else '已为您接通人工客服'
            )
        }, status=status.HTTP_201_CREATED)

# 查询当前排队位置
class QueuePositionView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, session_id):
        try:
            session = HumanAgentSession.objects.get(session_id=session_id, user=request.user)
        except HumanAgentSession.DoesNotExist:
            return Response({
                'error': 'session_not_found',
                'message': '会话不存在',
            },status=status.HTTP_404_NOT_FOUND)
        queue = WaitingQueue()
        position = queue.get_position(session_id)    # 当前排队位置
        queue_length = queue.get_queue_length()    # 当前队列总人数
        return Response({
            'session_id': session_id,
            'position': position or 0,
            'total_in_queue': queue_length,
            'estimated_wait_seconds': (position or 0) * 60,
            'status': session.status,
        })

# 发送信息(用户端)
class SendMessageView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        serializer = SendMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        # 查询会话记录，同时校验两个条件：session_id 存在 且 属于当前用户
        try:
            session = HumanAgentSession.objects.get(session_id=data['session_id'], user=request.user)
        except HumanAgentSession.DoesNotExist:
            return Response({
                'error': 'session_not_found',
                'message': '会话不存在'
            }, status=status.HTTP_404_NOT_FOUND)
        with transaction.atomic():
            message = HumanAgentMessage.objects.create(
                session=session,
                sender_type='user',
                sender_id=str(request.user.id),
                content=data['content'],
                message_type=data.get('message_type', 'text'),
                metadata=data.get('metadata'),
            )
            session.save(update_fields=['update_time'])
        channel_layer = get_channel_layer()    # 获取Redis-backed的Channel Layer实例
        # 如果该会话已分配客服，通过Channel Layer向客服的ws组推送消息
        if session.agent:
            async_to_sync(channel_layer.group_send)(
                f"agent_{session.agent.agent_id}",
                {
                    'type': 'user_message',
                    'session_id': session.session_id,
                    'content': data['content'],
                    'metadata': data.get('metadata'),
                }
            )
        return Response({
            'success': True,
            'message_id': str(message.id),
            'created_at': message.create_time.isoformat(),
        }, status=status.HTTP_201_CREATED)

# 结束会话(用户)
class EndSessionView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        serializer = EndSessionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        # 查询会话记录，同时校验两个条件：session_id 存在 且 属于当前用户
        try:
            session = HumanAgentSession.objects.get(session_id=data['session_id'], user=request.user)
        except HumanAgentSession.DoesNotExist:
            return Response({
                'error': 'session_not_found',
                'message': '会话不存在',
            }, status=status.HTTP_404_NOT_FOUND)
        with transaction.atomic():
            session.status = 'session_completed'
            session.ended_at = timezone.now()
            session.end_reason = data.get('reason', '问题已解决')
            session.summary = data.get('summary', '')
            session.save(update_fields=['status','ended_at', 'end_reason', 'summary'])
            if session.agent:    # 如果该会话已分配客服
                agent = session.agent
                # 当前客服 当前会话数 - 1
                agent.current_sessions = max(0, agent.current_sessions - 1)
                if agent.current_sessions < agent.max_capacity:
                    agent.status = 'online'
                agent.save(update_fields=['current_sessions', 'status'])
        # 通知客服 结束会话
        if session.agent:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"agent_{session.agent.agent_id}",
                {
                    'type': 'session_ended',
                    'session_id': session.session_id,
                    'reason': session.end_reason,
                }
            )
        # 场景"排队中，主动取消会话"兜底
        queue = WaitingQueue()
        queue.remove(data['session_id'])
        # 该会话结束后，为其他用户 分配客服
        try_assign_from_queue()
        return Response({
            'success': True,
            'status': session.status,
            'ended_at': session.ended_at.isoformat(),
        })

# 查询客服状态API
class AgentStatusView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        agents = HumanAgent.objects.all()
        online_agents = agents.filter(status='online')
        busy_agents = agents.filter(status='busy')
        agent_list = []
        for agent in agents:
            agent_list.append({
                'agent_id': agent.agent_id,
                'agent_name': agent.agent_name,
                'status': agent.status,
                'current_sessions': agent.current_sessions,
                'max_capacity': agent.max_capacity,
                'available_slots': max(0, agent.max_capacity - agent.current_sessions),    # 还能接多少用户
            })
        return Response({
            'total_agents': agents.count(),
            'online_agents': online_agents.count(),
            'busy_agents': busy_agents.count(),
            'agents': agent_list,
        })

# 查询历史消息
class HistoryView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, session_id):
        # 查询会话记录，同时校验两个条件：session_id 存在 且 属于当前用户
        try:
            session = HumanAgentSession.objects.get(session_id=session_id, user=request.user)
        except HumanAgentSession.DoesNotExist:
            return Response({
                'error': 'session_not_found',
                'message': '会话不存在',
            }, status=status.HTTP_404_NOT_FOUND)
        messages = HumanAgentMessage.objects.filter(session=session)
        message_list = []
        for message in messages:
            message_list.append({
                'message_id': str(message.id),
                'sender_type': message.sender_type,
                'sender_id': message.sender_id,
                'content': message.content,
                'message_type': message.message_type,
                'metadata': message.metadata,
                'created_at': message.create_time.isoformat(),
            })
        return Response({
            'session_id': session_id,
            'messages': message_list,
            'total_count': len(message_list),
        })
