from django.db.models.signals import post_delete,post_save
from django.dispatch import receiver
from apps.goods.models import Brand,SKUImage,Content,SKU,SPU
from celery_tasks.search.tasks import update_sku_index,delete_sku_index
import logging

logger = logging.getLogger(__name__)

# 第一个参数监听哪个信号,sender指定只监听哪个模型的该信号,如果省略sender=SKU,那么所有模型的post_save都会触发这个函数,会严重影响性能
@receiver(post_delete,sender=Brand)
def delete_brand_logo(sender,instance,**kwargs):
    if instance.logo:
        try:
            instance.logo.delete(save=False)
        except Exception as e:
            logger.warning("删除 Brand %s 的 logo 失败：%s",instance.pk,e)

@receiver(post_delete,sender=SKUImage)
def delete_sku_image(sender,instance,**kwargs):
    if instance.img:
        try:
            instance.img.delete(save=False)
        except Exception as e:
            logger.warning("删除 SKUImage %s 的 img 失败：%s",instance.pk,e)

@receiver(post_delete,sender=Content)
def delete_content_image(sender,instance,**kwargs):
    if instance.image:
        try:
            instance.image.delete(save=False)
        except Exception as e:
            logger.warning("删除 Content %s 的 image 失败：%s",instance.pk,e)
"""
@receiver是一个装饰器,作用是把下面的函数注册到指定的信号上,相当于手动手写post_save.connect(sku_save,sender=SKU)

写完signals之后，需要去子应用的apps.py中，通过ready()来执行注册逻辑
"""

@receiver(post_save,sender=SKU)
# SKU 保存/修改后 -> 异步更新 ES 索引
def update_sku_es(sender,instance,**kwargs):
    update_sku_index.delay(instance.id)

@receiver(post_delete,sender=SKU)
# SKU 删除后 -> 异步删除 ES 索引
def delete_sku_es(sender,instance,**kwargs):
    delete_sku_index.delay(instance.id)

@receiver(post_save,sender=SPU)
# SPU 的 name/brand/category 被改时，其下所有 SKU 索引都要刷新
def refresh_spu_skus(sender,instance,**kwargs):
    # values_list是Django ORM的QuerySet方法，即对SPU的所有SKU只取id这一列
    # flat=True让返回的id不带元组壳[(1,),(2,)]，而是一维值列表[1,2]
    for sku_id in instance.skus.values_list('id',flat=True):
        update_sku_index.delay(sku_id)