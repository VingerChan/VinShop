from django.db import models
from utils.models import BaseModel
from apps.users.models import User

# 人工客服信息表
class HumanAgent(BaseModel):
    STATUS_CHOICES = (
        ('offline', '离线'),
        ('online', '在线'),
        ('busy', '忙碌'),
    )
    agent_id = models.CharField(max_length=64, unique=True, verbose_name='客服ID')
    agent_name = models.CharField(max_length=128, verbose_name='客服名称')
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default='offline', verbose_name='状态')
    max_capacity = models.IntegerField(default=5, verbose_name='最大并发数')
    current_sessions = models.IntegerField(default=0, verbose_name='当前会话数')
    last_active_at = models.DateTimeField(null=True, blank=True, verbose_name='最后活跃时间')

    class Meta:
        db_table = 'tb_human_agents'
        verbose_name = '人工客服'
        verbose_name_plural = verbose_name
        ordering = ['-create_time']

# 转接会话表
class HumanAgentSession(BaseModel):
    STATUS_CHOICES = (
        ('transfer_requested', '转接请求已提交'),
        ('in_queue', '排队中'),
        ('human_active', '人工客服服务中'),
        ('session_completed', '会话已完成'),
        ('session_timeout', '会话超时'),
    )
    session_id = models.CharField(max_length=64, primary_key=True, verbose_name='会话ID')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='human_agent_sessions',verbose_name='用户')
    agent = models.ForeignKey(HumanAgent, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='客服')
    status = models.CharField(max_length=32, choices=STATUS_CHOICES,default='transfer_requested', db_index=True, verbose_name='状态')
    ai_chat_history = models.JSONField(null=True, blank=True, verbose_name='AI聊天历史')
    ended_at = models.DateTimeField(null=True, blank=True)
    end_reason = models.CharField(max_length=32, null=True, blank=True)
    summary = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'tb_human_agent_sessions'
        verbose_name = '人工客服会话'
        verbose_name_plural = verbose_name
        ordering = ['-create_time']

# 人工客服消息表
class HumanAgentMessage(BaseModel):
    SENDER_TYPE_CHOICES = (
        ('user', '用户'),
        ('agent', '客服'),
        ('system', '系统'),
    )
    MESSAGE_TYPE_CHOICES = (
        ('text', '文本'),
        ('image', '图片'),
        ('file', '文件'),
    )
    session = models.ForeignKey(HumanAgentSession, on_delete=models.CASCADE, related_name='messages', verbose_name='会话')
    sender_type = models.CharField(max_length=16, choices=SENDER_TYPE_CHOICES, verbose_name='发送者类型')
    sender_id = models.CharField(max_length=64, verbose_name='发送者ID')
    content = models.TextField(verbose_name='消息内容')
    message_type = models.CharField(max_length=32, choices=MESSAGE_TYPE_CHOICES,default='text', verbose_name='消息类型')
    # 扩展字段，图片/文件的元数据
    metadata = models.JSONField(null=True, blank=True, verbose_name='元数据')

    class Meta:
        db_table = 'tb_human_agent_messages'
        verbose_name = '人工客服消息'
        verbose_name_plural = verbose_name
        ordering = ['-create_time']
