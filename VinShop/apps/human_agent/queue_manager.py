from django_redis import get_redis_connection
from django.conf import settings

QUEUE_KEY = 'human_agent:waiting_queue'

# 基于Redis的等待队列
class WaitingQueue:
    def __init__(self):
        self.redis_conn = get_redis_connection('human_agent')
    def enqueue(self, session_id: str) -> bool:
        """
        加入队列，返回是否成功
        :param session_id: 会话id
        :return: True or False
        """
        # 获取列表当前长度
        queue_len = self.redis_conn.llen(QUEUE_KEY)
        #  从settings中获取队列最大容量
        max_size = getattr(settings, 'QUEUE_MAX_SIZE', 100)
        # 如果队列已满，拒绝入队
        if queue_len >= max_size:
            return False
        # 将元素添加到队列末尾
        self.redis_conn.rpush(QUEUE_KEY, session_id)
        return True
    def dequeue(self) -> str | None:
        """
        取出队首元素
        :return: session_id 或 None
        """
        result = self.redis_conn.lpop(QUEUE_KEY)
        if result is None:
            return None
        # 返回值如果是bytes类型，需要解码
        return result.decode() if isinstance(result, bytes) else result
    def peek(self) -> str | None:
        """
        查看队首元素但不移除（用于尝试过分配时的预览）
        :return: session_id 或 None
        """
        # lindex 获取指定索引的元素，index=0 即队首
        result = self.redis_conn.lindex(QUEUE_KEY, 0)
        if result is None:
            return None
        return result.decode() if isinstance(result, bytes) else result
    def get_position(self, session_id: str) -> int | None:
        """
        获取指定会话在队列中的位置
        :param session_id: 会话id
        :return: 位置(从1开始) 或 None(不在队列中)
        """
        # lrange 获取列表的指定范围， 0:-1 表示获取全部元素
        queue = self.redis_conn.lrange(QUEUE_KEY, 0, -1)
        try:
            return queue.index(session_id.encode()) + 1
        except ValueError:    # 元素不在队列中
            return None
    def get_queue_length(self) -> int:
        """
        :return: 当前队列长度
        """
        return self.redis_conn.llen(QUEUE_KEY)
    def remove(self, session_id: str) -> int:
        """
        从队列中移除指定会话
        :param session_id: 会话id
        :return: 移除的元素个数(0或1)
        """
        # count = 0表示移除所有匹配的元素
        return self.redis_conn.lrem(QUEUE_KEY, 0, session_id)

def assign_agent(session_id: str) -> str | None:
    """
    为会话分配客服
    :param session_id: 会话ID
    :return: agent_id 或 None
    """
    from apps.human_agent.models import HumanAgent, HumanAgentSession
    from asgiref.sync import async_to_sync
    from channels.layers import get_channel_layer
    # 查询所有在线客服
    online_agents = HumanAgent.objects.filter(status='online')
    # 筛选出当前会话数 < 最大容量的客服
    available_agents = [agent for agent in online_agents if agent.current_sessions < agent.max_capacity]
    # 优先分配负载较低的客服
    available_agents.sort(key=lambda agent: agent.max_capacity - agent.current_sessions, reverse=True)    # 降序排序
    # 没有可用客服
    if not available_agents:
        return None
    # 选择槽位最多的客服
    agent = available_agents[0]
    # 更新客服的会话计数
    agent.current_sessions += 1
    if agent.current_sessions >= agent.max_capacity:
        agent.status = 'busy'    # 达到上限，标记为忙碌
    agent.save(update_fields=['current_sessions', 'status'])
    # 更新会话状态：绑定客服，状态改为人工客服服务中
    session = HumanAgentSession.objects.get(session_id=session_id)
    session.agent = agent
    session.status = 'human_active'
    session.save(update_fields=['agent', 'status'])
    # 通过Channel Layer(消息中间件)向客服推送"新会话分配"通知
    channel_layer = get_channel_layer()
    history = session.ai_chat_history or []
    # group_send向指定组发送消息
    async_to_sync(channel_layer.group_send)(
        f"agent_{agent.agent_id}",    # 目标组：该客服的所有WebSocket连接
        {
            'type': 'new_assignment',
            'session_id': session.session_id,
            'user_id': session.user_id,
            'history': history,    # 附带AI聊天历史，方便客服了解上下文
        }
    )
    return agent.agent_id

# 尝试从队列中分配用户给空闲客服
def try_assign_from_queue():
    queue = WaitingQueue()
    while True:
        # 查看排队队列的队首
        session_id = queue.peek()
        if not session_id:
            # 队列为空，退出循环
            break
        session_id = session_id.decode() if isinstance(session_id, bytes) else session_id
        # 尝试为该用户分配客服
        agent_id = assign_agent(session_id)
        if agent_id is None:
            # 无可用客服，停止尝试
            break
        # 分配成功，从队列中移除该用户
        queue.dequeue()

# 异步版本 (供 AsyncWebsocketConsumer 使用)

from channels.db import database_sync_to_async
from channels.layers import get_channel_layer

async def assign_agent_async(session_id: str) -> str | None:
    """
    异步版本：为会话分配客服
    :param session_id: 会话ID
    :return: agent_id 或 None
    """
    from apps.human_agent.models import HumanAgent, HumanAgentSession

    # 查询所有在线客服
    online_agents = await database_sync_to_async(
        lambda: list(HumanAgent.objects.filter(status='online'))
    )()
    # 筛选出当前会话数 < 最大容量的客服
    available_agents = [agent for agent in online_agents if agent.current_sessions < agent.max_capacity]
    # 优先分配负载较低的客服
    available_agents.sort(key=lambda agent: agent.max_capacity - agent.current_sessions, reverse=True)
    # 没有可用客服
    if not available_agents:
        return None
    # 选择槽位最多的客服
    agent = available_agents[0]
    # 更新客服的会话计数
    agent.current_sessions += 1
    if agent.current_sessions >= agent.max_capacity:
        agent.status = 'busy'
    await database_sync_to_async(agent.save)(update_fields=['current_sessions', 'status'])
    # 更新会话状态：绑定客服，状态改为人工客服服务中
    session = await database_sync_to_async(HumanAgentSession.objects.get)(session_id=session_id)
    session.agent = agent
    session.status = 'human_active'
    await database_sync_to_async(session.save)(update_fields=['agent', 'status'])
    # 通过Channel Layer向客服推送"新会话分配"通知
    channel_layer = get_channel_layer()
    history = session.ai_chat_history or []
    await channel_layer.group_send(
        f"agent_{agent.agent_id}",
        {
            'type': 'new_assignment',
            'session_id': session.session_id,
            'user_id': session.user_id,
            'history': history,
        }
    )
    return agent.agent_id

async def try_assign_from_queue_async():
    """异步版本：尝试从队列中分配用户给空闲客服"""
    queue = WaitingQueue()
    while True:
        # WaitingQueue 的 Redis 调用是同步的，用 database_sync_to_async 包装
        session_id = await database_sync_to_async(queue.peek)()
        if not session_id:
            break
        session_id = session_id.decode() if isinstance(session_id, bytes) else session_id
        agent_id = await assign_agent_async(session_id)
        if agent_id is None:
            break
        await database_sync_to_async(queue.dequeue)()