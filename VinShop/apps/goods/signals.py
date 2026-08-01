from django.db.models.signals import post_delete
from django.dispatch import receiver
from apps.goods.models import Brand,SKUImage,Content
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