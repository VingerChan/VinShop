from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    mobile = models.CharField(max_length=11, unique=True)

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