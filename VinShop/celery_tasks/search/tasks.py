from celery_tasks.main import app
from apps.goods.models import SKU
from apps.goods.documents import sku_doc
from utils.es_util import get_client
from django.conf import settings
@app.task
# 把 SKU 的最新数据写入(覆盖) ES 索引
# 增 改: id索引存在则替换  id索引不存在则创建  (以sku_id为索引)
def update_sku_index(sku_id):
    try:
        sku = SKU.objects.select_related('spu__brand','spu__category','spu__category__parent','spu__category__parent__parent').get(id=sku_id)
    except SKU.DoesNotExist:
        return
    """
        client.index(index="my_index",id="my_document_id",document={
            "foo": "foo",
            "bar": "bar",
        }
    )
    """
    # 强制立刻 refresh,写完马上把这块数据变成可搜索的
    get_client().index(index=settings.ES_SKU_INDEX,id=sku_id,document=sku_doc(sku),refresh=True)

@app.task
def delete_sku_index(sku_id):
    # 对status404忽略，如果数据不存在也不会报错
    # client.index(index="my_index",id="my_document_id")
    get_client().delete(index=settings.ES_SKU_INDEX,id=sku_id,ignore_status=[404])

