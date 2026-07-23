from rest_framework import serializers
from apps.users.models import User,UserProfile
import re
from django.core.cache import caches
from utils.default_nickname import generate_default_nickname
from django.db import transaction
from VinShop.settings import FDFS_BASE_URL
# 用到模型创建，所以用ModelSerializer(包含默认的create和update实现)
class UserRegisterSerializer(serializers.ModelSerializer):
    # 只允许反序列化
    password2 = serializers.CharField(write_only=True)
    allow = serializers.BooleanField(write_only=True)
    sms_code = serializers.CharField(write_only=True)
    class Meta:
        model = User
        # 不在fields里的字段，DRF会直接忽略
        fields = ['id','username','password','password2','mobile','allow','sms_code']
        extra_kwargs = {
            'password' : {'write_only' : True},
            # 去掉默认的验证器，使用自己的validate
            'username' : {'validators' : []}
        }
    def validate_username(self,value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('用户名已存在，请勿重复注册')
        # 必须返回验证后的值，否则username不会传进create_user
        return value
    def validate_mobile(self,value):
        if not re.match(r'1[345789]\d{9}',value):
            raise serializers.ValidationError('手机号规格不符合要求')
        return value
    def validate_allow(self,value):
        if not value:
            raise serializers.ValidationError('请先同意用户协议')
        return value
    def validate(self,attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError('两次密码不一致')
        cache = caches['code']
        redis_sms = cache.get(attrs['mobile'])
        if not redis_sms:
            raise serializers.ValidationError('短信验证码已过期')
        if redis_sms != attrs['sms_code']:
            raise serializers.ValidationError('短信验证码错误')
        return attrs
    def create(self,validated_data):
        # 直接移除password2，不赋值
        validated_data.pop('password2')
        validated_data.pop("allow")
        validated_data.pop('sms_code')
        # create_user自动对密码进行哈希加密,和create不同
        with transaction.atomic():
            user = User.objects.create_user(**validated_data)
            UserProfile.objects.create(
                user=user,
                user_img='group1/M00/00/00/wKjpgGpgibGAGEWyAAgMd8DMqI0553',
                nickname=generate_default_nickname(),
                gender=0,
                birthday=None
            )
            cache = caches['code']
            cache.delete(validated_data['mobile'])
        return user

from django.contrib.auth import authenticate
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    def validate(self,attrs):
        username = attrs['username']
        password = attrs['password']
        # 如果输入是手机号 --> 查出对应的username
        if re.match(r'1[345789]\d{9}',username):
            try:
                user = User.objects.get(mobile=username)
                username = user.username
            except User.DoesNotExist:
                pass
        # 用户验证(验证成功返回user模型实例 失败返回None)
        user = authenticate(username=username, password=password)
        if not user:
            raise serializers.ValidationError('用户名或密码错误')
        attrs['user'] = user
        return attrs

# ModelSerializer包含默认的create()和update()的实现
class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['user_img','nickname','gender','birthday']
    # to_representation() 是 DRF 中，把「模型对象 → Python 字典 → JSON」的核心转换函数
    def to_representation(self,instance):   # 重写
        # 输出时将user_img拼成完整URL
        # 重写父类方法，拦截序列化流程
        data = super().to_representation(instance)
        if data.get('user_img'):    # 如果data存在user_img
            data['user_img'] = FDFS_BASE_URL + data['user_img']
        data['email'] = instance.user.email
        return data

class SendSmsEmailSerializer(serializers.Serializer):
    sms_code = serializers.CharField()
    def validate_sms_code(self,value):
        cache = caches['code']
        user = self.context.get('request').user
        redis_email_sms = cache.get(f"email_sms_{user.id}")
        if not value:
            raise serializers.ValidationError("短信验证码已过期")
        if redis_email_sms != value:
            raise serializers.ValidationError('短信验证码错误')
        cache.set(f"email_sms_passed_{user.id}",'1',600)
        cache.delete(f"email_sms_{user.id}")
        return value

from apps.users.models import User
class SendEmailCodeSerializer(serializers.Serializer):
    email = serializers.EmailField()
    def validate_email(self,value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("该邮箱已经被其他用户绑定")
        if not re.match(r'[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}', value):
            raise serializers.ValidationError("邮箱不符合规格")
        return value
    def validate(self,attrs):
        cache = caches['code']
        if not cache.get(f"email_sms_passed_{self.context.get('request').user.id}"):
            raise serializers.ValidationError("请先完成身份验证")
        return attrs

class VerifyEmailCodeSerializer(serializers.Serializer):
    email = serializers.EmailField()
    email_code = serializers.CharField()
    def validate(self,attrs):
        cache = caches['code']
        user = self.context.get('request').user
        cache_code = cache.get(f"email_{attrs['email']}")
        if not cache.get(f"email_sms_passed_{user.id}"):
            raise serializers.ValidationError("请先完成身份验证")
        if not cache_code:
            raise serializers.ValidationError("邮箱验证码已过期，请重新发送")
        if attrs['email_code']!=cache_code:
            raise serializers.ValidationError("邮箱验证码错误")
        # 如果没有错误，删掉Redis中的验证码
        cache.delete(f"email_{attrs['email']}")
        cache.delete(f"email_sms_passed_{user.id}")
        return attrs
    def update(self,instance,validated_data):
        instance.email = validated_data['email']
        instance.save()
        return instance