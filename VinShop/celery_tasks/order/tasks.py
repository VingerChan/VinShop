from celery_tasks.main import app
from django.utils import timezone
from utils.order import cancel_unpaid_order,get_expired_order_ids
@app.task
def cancel_timeout_order(order_id,expire_ts):
    return cancel_unpaid_order(order_id,expire_ts)

@app.task
def check_expired_orders():
    # 将当前时间转换成时间戳
    now_ts = int(timezone.now().timestamp())
    # 获取超时未支付的订单id
    expired_ids = get_expired_order_ids(now_ts)
    for order_id,expire_ts in expired_ids:
        # 异步投递
        cancel_timeout_order.delay(order_id,expire_ts)
    return len(expired_ids)