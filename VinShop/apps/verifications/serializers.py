from rest_framework import serializers
from django.core.cache import caches
import re
class SMSCodeSerializer(serializers.Serializer):
    # 前端返回mobile uuid code(图片验证码)
    mobile = serializers.CharField()
    uuid = serializers.CharField()
    frontend_code = serializers.CharField()
    def validate_mobile(self, value):
        if not re.match(r'1[345789]\d{9}',value):
            raise serializers.ValidationError('手机号规格不符合要求')
        return value
    def validate(self,attrs):
        cache = caches['code']
        # 从 Redis 取出code
        code = cache.get(attrs['uuid'])
        # 校验图片验证码有没有过期
        if not code:
            raise serializers.ValidationError('图形验证码已过期')
        # 校验frontend_code与Redis的code是否一致
        if attrs.get('frontend_code') != code.lower():
            raise serializers.ValidationError('图形验证码错误')
        # 如果没有错误，删除Redis中的code
        cache.delete(attrs['uuid'])
        return attrs