from django.db import models
from utils.models import BaseModel
from apps.orders.models import OrderInfo
class Payment(BaseModel):
    order = models.ForeignKey(OrderInfo,on_delete=models.CASCADE,verbose_name='订单编号')
    amount = models.DecimalField(max_digits=10,decimal_places=2,verbose_name='实付金额')
    trade_no = models.CharField(max_length=100,null=True,blank=True,unique=True,verbose_name='支付编号')
    class Meta:
        db_table = 'tb_payment'
        verbose_name='支付信息'
        verbose_name_plural = verbose_name