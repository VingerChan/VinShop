from django.db import models

# Create your models here.
class Area(models.Model):
    name = models.CharField(max_length=20,verbose_name='名称')
    parent = models.ForeignKey('self',on_delete=models.PROTECT,null=True,related_name='subs',verbose_name='上级行政区划')
    class Meta:
        db_table = 'tb_areas'
        verbose_name = '省市区'
        verbose_name_plural = verbose_name
    def __str__(self):
        return self.name
    """
        · 'self'是Django中自关联外键的写法,表示该外键指向自己这个模型的同一张表
          而id是默认主键,所以ForeignKey默认关联主键
    """