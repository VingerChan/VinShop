from django_redis import get_redis_connection

# 数量
def _key(user_id):
    return f"cart_{user_id}"

#勾选
def _selected_key(user_id):
    return f"cart_selected_{user_id}"

# 获取购物车
def get_all(user_id):
    redis_conn = get_redis_connection('carts')
    data = redis_conn.hgetall(_key(user_id))
    # {b'1':b'2',b'4':b'1'}
    return {int(sku_id):int(count) for sku_id,count in data.items()}

# 添加购物车
def add(user_id,sku_id,count):
    redis_conn = get_redis_connection('carts')
    pipeline = redis_conn.pipeline()
    # hincrby: 对Hash中指定字段做 原子自增，字段不存在则自动创建并从0开始加
    pipeline.hincrby(_key(user_id),sku_id,count)
    # 新加入的商品默认置为勾选状态 redis_conn.sadd(key, value)
    pipeline.sadd(_selected_key(user_id),sku_id)
    pipeline.execute()

# 购物车中 SKU总数
def total_count(user_id):
    redis_conn = get_redis_connection('carts')
    # redis_conn.hvals(key) 返回某个 Hash 中所有的 value，不包含 field 名
    # 对hvals(key)返回的value进行累加 得出总数
    return sum(int(value) for value in redis_conn.hvals(_key(user_id)))

# 获取购物车中的勾选SKU
def get_selected(user_id):
    redis_conn = get_redis_connection('carts')
    # Set : {1,2,3,4,5}
    return {int(sku_id) for sku_id in redis_conn.smembers(_selected_key(user_id))}

def select_all(user_id,selected):
    redis_conn = get_redis_connection('carts')
    selected_key = _selected_key(user_id)
    # 如果全选 selected=True
    if selected:
        # 取出Redis Hash的key，不包括field 和 value
        sku_ids = redis_conn.hkeys(_key(user_id))
        # 先清空 再 批量加入
        redis_conn.delete(selected_key)
        if sku_ids:
            redis_conn.sadd(selected_key,*sku_ids)

    else:
        redis_conn.delete(selected_key)