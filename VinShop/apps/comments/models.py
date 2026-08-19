from django.db import models
from utils.models import BaseModel
from apps.users.models import User
from apps.goods.models import SPU,SKU
from apps.orders.models import OrderInfo,OrderGoods
from utils.storage import FastDFSStorage
class Comment(BaseModel):
    SCORE_CHOICES = (
        (1,'1星'),
        (2,'2星'),
        (3,'3星'),
        (4,'4星'),
        (5,'5星'),
    )

    user = models.ForeignKey(User,on_delete=models.PROTECT,verbose_name='评价人')
    spu = models.ForeignKey(SPU,on_delete=models.CASCADE,related_name='comments',verbose_name='所属SPU')
    sku = models.ForeignKey(SKU, on_delete=models.PROTECT,related_name='sku_comments',verbose_name='实际购买SKU')
    order = models.ForeignKey(OrderInfo, on_delete=models.CASCADE, related_name='comments', verbose_name='所属订单')
    order_goods = models.ForeignKey(OrderGoods,on_delete=models.CASCADE,related_name='comments',verbose_name='订单商品')
    score = models.SmallIntegerField(choices=SCORE_CHOICES,verbose_name='评价(1~5星)')
    content = models.TextField(blank=True,default='',verbose_name='评价内容')
    images = models.JSONField(default=list,verbose_name='评价图片(最多6张)')
    video = models.FileField(upload_to='',storage=FastDFSStorage(),max_length=200,blank=True,default='',verbose_name='评价视频(最多一个)')
    is_anonymous = models.BooleanField(default=False,verbose_name='是否匿名评价')
    class Meta:
        db_table = 'tb_comment'
        verbose_name = '商品评价'
        verbose_name_plural = verbose_name
        ordering = ['-create_time']
        constraints = [
            models.UniqueConstraint(
                fields=['order_goods'],
                name='unique_comment_order_goods',
            )
        ]
    def __str__(self):
        return f"{self.user.username} - {self.sku.name}"
