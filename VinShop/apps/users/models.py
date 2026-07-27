from django.contrib.auth.models import AbstractUser
from django.db import models
from apps.areas.models import Area
from utils.models import BaseModel


class User(AbstractUser):
    mobile = models.CharField(max_length=11, unique=True)
    default_address = models.ForeignKey('Address',on_delete=models.SET_NULL,null=True,blank=True,verbose_name='默认地址',related_name='default_address')

    class Meta:
        db_table = 'tb_user'
        verbose_name = '用户管理'
        verbose_name_plural = verbose_name

class UserProfile(models.Model):
    GENDER_CHOICE = (
        (0,'未选择'),
        (1,'男'),
        (2,'女')
    )
    # 一个用户只能有一个UserProfile，所以用OnetoOneField
    user = models.OneToOneField(User,on_delete=models.CASCADE,related_name='profile')
    user_img = models.CharField(max_length=200,null=True,blank=True)
    nickname = models.CharField(max_length=20,null=True,blank=True)
    gender = models.SmallIntegerField(choices=GENDER_CHOICE,default=0)
    birthday = models.DateField(null=True,blank=True)
    """
        · auto_now_add:创建或添加对象时自动添加时间,修改或更新对象时,不会更改时间
        · auto_now:凡是对对象进行(创建/添加/修改/更新)时间都会随之改变
    """
    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = 'tb_user_profile'
        verbose_name='个人资料'
        verbose_name_plural = verbose_name

class Address(BaseModel):
    # on_delete=models.CASCADE:级联删除(User被删除,其的所有Address记录全部自动删除)
    user = models.ForeignKey(User,on_delete=models.CASCADE,related_name='address',verbose_name='用户')
    province = models.ForeignKey(Area,on_delete=models.PROTECT,related_name='province_addresses',verbose_name='省')
    city = models.ForeignKey(Area,on_delete=models.PROTECT,related_name='city_addresses',verbose_name='市')
    district = models.ForeignKey(Area,on_delete=models.PROTECT,related_name='district_addresses',verbose_name='区')
    place = models.CharField(max_length=50,verbose_name='详细地址')
    receiver_name = models.CharField(max_length=20,verbose_name='收货人姓名')
    mobile = models.CharField(max_length=11,verbose_name='手机号码')
    label = models.CharField(max_length=4,blank=True,null=True)
    class Meta:
        db_table = 'tb_address'
        verbose_name = '用户地址'
        verbose_name_plural = verbose_name
        ordering = ['-update_time']