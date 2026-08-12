from django.db import models
from utils.models import BaseModel
from apps.users.models import User,Address
from apps.goods.models import SKU
class OrderInfo(BaseModel):
    # ENUM Dict是给程序员看的，CHOICES只认元组
    # CHOICES 给Django校验/admin 用： 必须(存库值，中文显示名)
    # if order.status == OrderInfo.ORDER_STATUS_ENUM["UNPAID"]:
    PAY_METHODS_ENUM = {
        'CASH': 1,
        'ALIPAY': 2
    }
    PAY_METHODS_CHOICES = (
        (1,'货到付款'),
        (2,'支付宝'),
    )
    STATUS_ENUM = {
        'UNPAID': 1,  # 待支付
        'UNSEND': 2,  # 待发货
        'UNRECEIVED': 3,  # 待收货
        'UNCOMMENT': 4,  # 待评价
        'FINISHED': 5,  # 已完成
        'CANCELED': 6  # 已取消
    }
    STATUS_CHOICES = (
        (1,'待支付'),
        (2,'待发货'),
        (3,'待收货'),
        (4,'待评价'),
        (5,'已完成'),
        (6,'已取消'),
    )
    order_id = models.CharField(max_length=64,primary_key=True,verbose_name='订单号')
    user = models.ForeignKey(User,on_delete=models.PROTECT,related_name='orders',verbose_name='用户')
    address = models.ForeignKey(Address,on_delete=models.PROTECT,related_name='orders',verbose_name='收货地址')
    # 地址快照，用于后续用户可能因为填错地址信息 而修改
    receiver_name = models.CharField(max_length=20,verbose_name='收货人')
    receiver_mobile = models.CharField(max_length=11,verbose_name='收货手机号')
    receiver_address = models.CharField(max_length=255,verbose_name='收货地址')
    total_count = models.IntegerField(default=0,verbose_name='商品总件数')
    """
        max_digits:数字总位数（整数部分 + 小数部分）
        decimal_places:小数位数
    """
    total_amount = models.DecimalField(max_digits=10,decimal_places=2,verbose_name='商品总价')
    freight = models.DecimalField(max_digits=10,decimal_places=2,default=10,verbose_name='运费')
    pay_method = models.SmallIntegerField(default=PAY_METHODS_ENUM['CASH'],choices=PAY_METHODS_CHOICES,verbose_name='支付方式')
    status = models.SmallIntegerField(default=STATUS_ENUM['UNPAID'],choices=STATUS_CHOICES,verbose_name='订单状态')
    class Meta:
        db_table = 'tb_order_info'
        verbose_name = '订单信息'
        verbose_name_plural = verbose_name
    def __str__(self):
        return f"{self.user.username} - {self.order_id}"

class OrderGoods(BaseModel):
    order = models.ForeignKey(OrderInfo,on_delete=models.CASCADE,related_name='skus',verbose_name='订单')
    sku = models.ForeignKey(SKU,on_delete=models.PROTECT,verbose_name='SKU')
    count = models.IntegerField(verbose_name='数量')
    price = models.DecimalField(max_digits=10,decimal_places=2,verbose_name='下单时价格快照')
    note = models.CharField(max_length=200,default='',blank=True,verbose_name='下单备注')
    is_commented = models.BooleanField(default=False,verbose_name='是否已评价')
    class Meta:
        db_table = 'tb_order_goods'
        verbose_name = '订单商品'
        verbose_name_plural = verbose_name
    def __str__(self):
        return f"{self.order.order_id} - {self.sku.name}"