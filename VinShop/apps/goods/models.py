from django.db import models
from utils.models import BaseModel
# 目录
class GoodsCategory(BaseModel):
    name = models.CharField(max_length=10,verbose_name='名称')
    parent = models.ForeignKey('self',on_delete=models.CASCADE,related_name='subs',null=True, blank=True,verbose_name='父目录')
    class Meta:
        db_table = 'tb_goods_category'
        verbose_name = '商品目录'
        verbose_name_plural = verbose_name
    def __str__(self):
        return self.name

# 频道组，一个频道组内有多个一级目录
class GoodsChannelGroup(BaseModel):
    name = models.CharField(max_length=10,verbose_name='频道组名')
    class Meta:
        db_table = 'tb_goods_channel_group'
        verbose_name = '频道组'
        verbose_name_plural = verbose_name
    def __str__(self):
        return self.name

class GoodsChannel(BaseModel):
    group = models.ForeignKey(GoodsChannelGroup,on_delete=models.CASCADE,verbose_name='频道组')
    category = models.ForeignKey(GoodsCategory,on_delete=models.CASCADE,verbose_name='一级目录商品类别')
    sequence = models.IntegerField(verbose_name='组内顺序')
    class Meta:
        db_table = 'tb_goods_channel'
        verbose_name = '商品频道'
        verbose_name_plural = verbose_name
        # 按照sequence升序，从小到大
        ordering = ['sequence']
        constraints = [
            models.UniqueConstraint(
                # 同组内顺序唯一
                fields = ['group','sequence'],
                # 给数据库约束一个可读名字，如果报错就能知道是这个问题
                name = 'unique_goods_channel',
            )
        ]
    def __str__(self):
        return self.category.name