from celery_tasks.main import app
from django_redis import get_redis_connection
from django.conf import settings
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

@app.task
def clean_comment_file():
    redis_conn = get_redis_connection('file')
    # 获取当前时间戳
    now_ts = timezone.now().timestamp()
    orphan_file = redis_conn.zrangebyscore(settings.FILE_KEY,min='-inf',max=now_ts)
    removed = 0    # 已删除孤儿文件的个数
    from fdfs_client.client import Fdfs_client
    fdfs = Fdfs_client(settings.FDFS_CLIENT_CONF)
    for file_id in orphan_file:
        file_id = file_id.decode()
        try:
            fdfs.delete_file(file_id.encode())
            removed += 1
        except Exception as e:
            logger.warning('清理孤儿文件失败 %s: %s',file_id,e)
    if orphan_file:
        redis_conn.zrem(settings.FILE_KEY, *[file.decode() for file in orphan_file])
    return removed

