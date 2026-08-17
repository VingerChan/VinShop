from celery_tasks.main import app
from utils.order import cancel_unpaid_order
@app.task
def cancel_timeout_order(order_id,expire_ts):
    return cancel_unpaid_order(order_id,expire_ts)