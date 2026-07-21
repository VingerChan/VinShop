from rest_framework import serializers
from apps.users.models import User
import re

class UserRegisterSerializer(serializers.ModelSerializer):
    # 只允许反序列化
    password2 = serializers.CharField(write_only=True)
    allow = serializers.BooleanField(write_only=True)
    class Meta:
        model = User
        fields = ['id','username','password','password2','mobile','allow']
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
        return attrs
    def create(self,validated_data):
        # 直接移除password2，不赋值
        validated_data.pop('password2')
        validated_data.pop("allow")
        # create_user自动对密码进行哈希加密,和create不同
        return User.objects.create_user(**validated_data)
