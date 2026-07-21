from rest_framework import serializers
from apps.users.models import User
import re
from django.core.cache import caches
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
        # 通过验证 删除sms_code 并 返回所有数据attrs
        cache.delete(attrs['mobile'])
        return attrs
    def create(self,validated_data):
        # 直接移除password2，不赋值
        validated_data.pop('password2')
        validated_data.pop("allow")
        validated_data.pop('sms_code')
        # create_user自动对密码进行哈希加密,和create不同
        return User.objects.create_user(**validated_data)

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
