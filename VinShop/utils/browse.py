from django.conf import settings
from django_redis import get_redis_connection
import time
# 添加浏览记录
def add(user_id,sku_id):
    # 连接redis 的history库
    redis_conn = get_redis_connection('history')
    key = f"history_{user_id}"
    # 从 1970-01-01 00:00:00 UTC 到现在已经过了 多少 s
    now:float = time.time()
    # 写入：score = 当前时间辍
    redis_conn.zadd(key,{sku_id:now})
    # 删除7天前的记录 redis_conn.zremrangebyscore(key, min_score, max_score)
    # 现在的score 和 7天前的score 相差7*86400 s，所以范围是0~7天前的score
    redis_conn.zremrangebyscore(key,0,now-settings.BROWSING_DAYS*86400)
    # 根据Redis ZSet排名限制200条数据zremrangebyscore(key,min,max)
    # 0表示最后一条数据 只有数据到达201位时才会删除(删除第0位和倒数201位)
    redis_conn.zremrangebyrank(key,0,-(settings.BROWSING_LIMIT+1))

# 获取浏览记录
def recent(user_id):
    redis_conn = get_redis_connection('history')
    key = f"history_{user_id}"
    # 读取前再兜底 清理时间超过7天以上的 数据
    redis_conn.zremrangebyscore(key,0,time.time()-settings.BROWSING_DAYS*86400)
    # zrange:score从低到高排序 zrevrange:score从高到低
    # 返回列表sku_id withscores=True则返回列表嵌套元组(sku_id,score)
    browse = redis_conn.zrevrange(key,0,-1,withscores=True)
    # redis里的sku_id是byte类型 需要转int
    return [(int(sku_id),int(timestamp)) for sku_id,timestamp in browse]
