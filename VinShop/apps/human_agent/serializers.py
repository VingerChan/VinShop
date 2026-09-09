from rest_framework import serializers
from apps.human_agent.models import HumanAgentMessage

# 创建转接会话的请求序列化器
class TransferCreateSerializer(serializers.Serializer):
    ai_chat_history = serializers.ListField(required=False, default=list, help_text='AI聊天历史记录')

# 发送消息的请求序列化器
class SendMessageSerializer(serializers.Serializer):
    session_id = serializers.CharField(max_length=64, help_text='会话ID')
    sender_type = serializers.ChoiceField(choices=HumanAgentMessage.SENDER_TYPE_CHOICES)
    sender_id = serializers.CharField(max_length=64, help_text='发送者ID')
    content = serializers.CharField(help_text='消息内容')
    message_type = serializers.ChoiceField(choices=HumanAgentMessage.MESSAGE_TYPE_CHOICES, default='text')
    # 元数据，图片/文件消息时使用
    metadata = serializers.JSONField(required=False, allow_null=True, default=None)

# 结束会话的请求序列化器
class EndSessionSerializer(serializers.Serializer):
    session_id = serializers.CharField(max_length=64, help_text='会话ID')
    reason = serializers.CharField(max_length=32, required=False, default='问题已解决', help_text='结束原因')
    summary = serializers.CharField(required=False, allow_blank=True, default='', help_text='会话摘要')