from django.db import models
from utils.models import BaseModel
from utils.storage import FastDFSStorage
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
    sequence = models.IntegerField(default=0,verbose_name='组内顺序')
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

# SPU的品牌
class Brand(BaseModel):
    name = models.CharField(max_length=20,verbose_name='品牌名')
    # upload_to决定 文件上传后的相对路径 storage决定存储系统
    logo = models.ImageField(upload_to='',storage=FastDFSStorage(),max_length=200,verbose_name='Logo图片')
    class Meta:
        db_table = 'tb_brand'
        verbose_name = '品牌'
        verbose_name_plural = verbose_name
    def __str__(self):
        return self.name

# 商品主体
class SPU(BaseModel):
    name = models.CharField(max_length=20,verbose_name='SPU名称')
    brand = models.ForeignKey(Brand,on_delete=models.PROTECT,verbose_name='品牌')
    category = models.ForeignKey(GoodsCategory,on_delete=models.CASCADE,verbose_name='分类')
    desc = models.TextField(verbose_name='商品介绍',default='')
    # 等所有模型都加载完了，再去找真正的 SKU 表
    default_sku = models.ForeignKey('SKU',on_delete=models.SET_NULL,null=True,blank=True,verbose_name='默认SKU',related_name='+')
    class Meta:
        db_table = 'tb_spu'
        verbose_name = 'SPU'
        verbose_name_plural = verbose_name
    def __str__(self):
        return self.name

class SKU(BaseModel):
    name = models.CharField(max_length=100,verbose_name='SKU名称')
    spu = models.ForeignKey(SPU,on_delete=models.CASCADE,related_name='skus',verbose_name='所属SPU')
    price = models.DecimalField(max_digits=10,decimal_places=2,verbose_name='售价')
    stock = models.IntegerField(default=0,verbose_name='库存')
    # 商品展示的图片
    default_image = models.ImageField(upload_to='',storage=FastDFSStorage(),max_length=200,null=True,blank=False,verbose_name='默认展示图')
    sales = models.IntegerField(default=0,verbose_name='销量')
    comments = models.IntegerField(default=0,verbose_name='评论数')
    is_launched = models.BooleanField(default=True,verbose_name='是否上架销售')
    class Meta:
        db_table = 'tb_sku'
        verbose_name = 'SKU'
        verbose_name_plural = verbose_name
    def __str__(self):
        return self.name

# SKU商品 图片
class SKUImage(BaseModel):
    sku = models.ForeignKey(SKU,on_delete=models.CASCADE,verbose_name='所属SKU',related_name='images')
    img = models.ImageField(upload_to='',storage=FastDFSStorage(),max_length=200,verbose_name='图片')
    sequence = models.IntegerField(default=0,verbose_name='图片顺序')
    class Meta:
        db_table = 'tb_sku_image'
        verbose_name = 'SKU图片'
        verbose_name_plural = verbose_name
        ordering = ['sequence']
        constraints = [
            models.UniqueConstraint(
                fields = ['sku','sequence'],
                name = 'unique_sku_image',
            )
        ]
    def __str__(self):
        return f"{self.sku.name} - {self.sku.id}"

# SPU规格，每个SPU具有哪种规格
class SPUSpec(BaseModel):
    name = models.CharField(max_length=20,verbose_name='规格名')
    spu = models.ForeignKey(SPU,on_delete=models.CASCADE,related_name='specs',verbose_name='所属SPU')
    class Meta:
        db_table = 'tb_spu_spec'
        verbose_name = 'SPU规格'
        verbose_name_plural = verbose_name
    def __str__(self):
        return f'{self.spu.name} - {self.name}'

# SPU规格选项
class SpecOption(BaseModel):
    value = models.CharField(max_length=30,verbose_name='规格值')
    sequence = models.IntegerField(default=0,verbose_name='顺序')
    spec = models.ForeignKey(SPUSpec,on_delete=models.CASCADE,related_name='options',verbose_name='所属规格')
    class Meta:
        db_table = 'tb_spec_option'
        verbose_name = '规格选项'
        verbose_name_plural = verbose_name
        # 从小到大
        ordering = ['sequence']
        constraints = [
            models.UniqueConstraint(
                fields = ['spec','sequence'],
                name = 'unique_spec_option',
            )
        ]
    def __str__(self):
        return f"{self.spec.spu.name} - {self.spec.name} - {self.value}"

# SKU规格
class SKUSpec(BaseModel):
    option = models.ForeignKey(SpecOption,on_delete=models.PROTECT,verbose_name='规格选项')
    sku = models.ForeignKey(SKU,on_delete=models.CASCADE,related_name='specs',verbose_name='SKU')
    class Meta:
        db_table = 'tb_sku_spec'
        verbose_name = 'SKU规格'
        verbose_name_plural = verbose_name
        constraints = [
            models.UniqueConstraint(
                fields = ['option','sku'],
                name = 'unique_sku_spec',
            )
        ]
    def __str__(self):
        return f'{self.sku.name} - {self.option.value}'

# 广告位分类
class ContentCategory(BaseModel):
    name = models.CharField(max_length=20,verbose_name='广告位名称')
    key = models.CharField(max_length=50,verbose_name='唯一标识')
    class Meta:
        db_table = 'tb_content_category'
        verbose_name = '广告位'
        verbose_name_plural = verbose_name
    def __str__(self):
        return self.name

# 具体广告内容
class Content(BaseModel):
    category = models.ForeignKey(ContentCategory,on_delete=models.CASCADE,related_name='contents',verbose_name='所属广告位')
    title = models.CharField(max_length=50,verbose_name='广告标题')
    image = models.ImageField(upload_to='',storage=FastDFSStorage(),max_length=200,verbose_name='图片')
    link = models.CharField(max_length=200,verbose_name='跳转链接')
    sequence = models.IntegerField(default=0,verbose_name='排序')
    is_active = models.BooleanField(default=True,verbose_name='是否启用')
    class Meta:
        db_table = 'tb_content'
        verbose_name = '广告内容'
        verbose_name_plural = verbose_name
        ordering = ['sequence']
        constraints = [
            models.UniqueConstraint(
                fields = ['category','sequence'],
                name = 'unique_category_content',
            )
        ]
    def __str__(self):
        return self.title