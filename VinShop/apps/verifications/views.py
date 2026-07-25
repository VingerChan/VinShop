from uuid import uuid4
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from utils.captcha import generate_captcha,generate_captcha_base64
from django.core.cache import caches
import random
"""
    APIView继承自View，区别在于
    get是request.get_params() post是request.data
    在APIView中仍以常规的类视图定义方法来实现get()post()或者其他请求方式的方法。
"""
class CaptchaView(APIView):
    def post(self,request):
        # 获取图片验证码文本 以及 带base64编码的图片字符串
        code,b64_str = generate_captcha_base64()
        # 由后端生成是因为防止前端并发撞库
        captcha_key = str(uuid4())
        cache = caches['code']
        cache.set(captcha_key,code,300)
        return Response({'captcha_key':captcha_key,'b64_str':b64_str})

from apps.verifications.serializers import SMSCodeSerializer
from celery_tasks.sms.tasks import send_sms_code
class SMSCodeView(APIView):
    def post(self,request):
        # 定义序列化器，并进行反序列化
        serializer = SMSCodeSerializer(data=request.data)
        # 验证数据是否正确
        serializer.is_valid(raise_exception=True)
        # 校验通过后的“干净数据”,只有调用了 is_valid() 之后，validated_data 才会有值
        mobile = serializer.validated_data['mobile']
        # 验证短信是否一分钟内发过(防止频繁发送短信)
        cache = caches['code']
        if cache.get(f"sms_flag_{mobile}"):
            return Response({'message':'请不要频繁发送短信'},status=status.HTTP_429_TOO_MANY_REQUESTS)
        # 生成4位随机数字——>短信验证码
        sms_code = f"{random.randint(1000,9999)}"
        # 存进redis中
        cache.set(mobile,sms_code,300)
        # 如果第一次发送短信则设置flag，第二次发送短信的时候就会校验flag从而防止频繁发送短信
        cache.set(f"sms_flag_{mobile}",1,60)
        # 异步发送短信
        send_sms_code.delay(mobile,sms_code)
        return Response({'message':'短信验证码已发送'})


