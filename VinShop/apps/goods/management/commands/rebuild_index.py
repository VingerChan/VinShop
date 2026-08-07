# django的命令发现机制要求目录结构必须是app/management/commands/
# 每层都必须有__init__.py
from django.core.management import BaseCommand
from apps.goods.documents import ensure_sku_index,sku_doc
from apps.goods.models import SKU
from utils.es_util import get_client
from elasticsearch.helpers import bulk
from django.conf import settings

class Command(BaseCommand):
    help = '全量重建商品(SKU)搜索索引'  # 运行python manage.py rebuild_index --help时显示的文字
    # 方法名必须是handle,Django在识别命令后会调用这个方法.options里放着add_arguments定义的参数值
    def handle(self, *args, **options):
        # 确保索引存在
        ensure_sku_index()
        client = get_client()
        # 只索引上架商品，一次性join出 spu/brand/category
        qs = SKU.objects.filter(is_launched=True).select_related('spu__brand','spu__category','spu__category__parent','spu__category__parent__parent').order_by('id')
        # 惰性生成批量写动作
        # 每个 action 只需 _index、_id（=sku.id）、_source（=构建好的文档），bulk 自己处理分批和错误重试。
        # 把结果集做成惰性迭代器，配合生成器 actions，全量数据也不会一次性全部加载进内存 —— 处理几万条 SKU 毫无压力
        actions = (
            {'_op_type':'index','_index':settings.ES_SKU_INDEX,'_id':sku.id,'_source':sku_doc(sku)}
            for sku in qs.iterator()    # 记录SQL查询条件 当前游标位置
        )
        # Bulk helper 批量处理工具/批量辅助程序
        # 自动把生成器按 500 条一批分块发送，比一条条 index 快一个数量级。返回值是 (成功条数, 失败条数)
        success,errors = bulk(client,actions,chunk_size=500,request_timeout=60)
        self.stdout.write(self.style.SUCCESS(f"成功 {success} 条，失败 {errors} 条 "))
