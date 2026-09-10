from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from apps.human_agent.serializers import TransferCreateSerializer
from apps.human_agent.models import HumanAgentSession
from rest_framework.response import Response
from rest_framework import status
import uuid
from django.db import transaction
from apps.human_agent.queue_manager import WaitingQueue, assign_agent


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