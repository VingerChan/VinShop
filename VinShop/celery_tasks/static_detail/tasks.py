from celery_tasks.main import app
from utils.generate_static_detail import static_sku_detail

# 生成单个商品详情页静态化文件
@app.task
def generate_static_sku_detail(sku_id):
    static_sku_detail(sku_id)
