from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import CreateAPIView, GenericAPIView, RetrieveUpdateAPIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
from apps.users.serializers import UserRegisterSerializer,LoginSerializer
from apps.users.models import User
from VinShop.settings import FDFS_BASE_URL,FDFS_CLIENT_CONF
from django.core.cache import caches
import random
from celery_tasks.sms.tasks import send_sms_code
import re
from apps.users.serializers import CenterVerifySmsSerializer
from apps.users.serializers import CenterChangeMobileSerializer
from apps.users.serializers import CenterSendEmailSerializer
from apps.users.serializers import CenterVerifyEmailSerializer
class RegisterView(CreateAPIView):  #
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    def create(self,request):
        # 反序列化
        serializer = self.get_serializer(data=request.data)
        # 验证数据
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        """
            服务端生成access token和refresh token到前端存在localstorage/Cookie中
            前端通过拦截器或定时器主动检测access token的有效性
            一旦发现access token过期，就会发送api请求到服务端，通过合法的refresh token重新生成access token
        """
        data = {
            'user' : {
                'id' : user.id,
                'username' : user.username,
                'mobile' : user.mobile
            },
            'user_profile' : {
                'user_img' : FDFS_BASE_URL+user.profile.user_img,
                'nickname' : user.profile.nickname,
                'gender' : user.profile.gender,
                'birthday' : user.profile.birthday,
            },
            'access' : str(refresh.access_token),
            'refresh' : str(refresh),

        }
        return Response(data,status=status.HTTP_201_CREATED)

class LoginView(GenericAPIView):
    serializer_class = LoginSerializer
    def post(self,request):
        # 对前端发送的username,password进行反序列化
        serializer = self.get_serializer(data=request.data)
        # 验证数据(LoginSerialize里写的用户验证)
        serializer.is_valid(raise_exception=True)
        # 获取验证成功后的user模型实例
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        data = {
            'user' : {
                'id' : user.id,
                'username' : user.username,
                'mobile' : user.mobile
            },
            'access' : str(refresh.access_token),
            'refresh' : str(refresh),
        }
        # DRF的Response()默认status是200 OK，一般默认 200 不写
        return Response(data)

from apps.users.serializers import UserProfileSerializer
# 从左到右，从子类到父类
class ProfileView(RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileSerializer
    # 用户中心获取个人资料
    def get(self,request):
        serializer = self.get_serializer(request.user.profile)
        return Response(serializer.data)
    # 更新个人资料
    def patch(self,request):
        user_profile = request.user.profile
        data = request.data.copy()
        if 'user_img' in request.data:
            file = request.data['user_img']
            try:
                from fdfs_client.client import Fdfs_client
                client = Fdfs_client(FDFS_CLIENT_CONF)
                result = client.upload_by_buffer(file.read())
                data['user_img'] = result['Remote file_id']
            except Exception as e:
                return Response({'message':'头像上传失败'},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        # 告诉serializer：只校验请求中传来的字段，没传的字段跳过检验，保留数据库原值
        serializer = self.get_serializer(instance=user_profile,data=data,partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

# 用户中心[身份验证]
class CenterVerifySmsView(APIView):
    permission_classes = [IsAuthenticated]
    # 获取手机短信验证码
    def post(self,request):
        user = request.user
        # 查看是否频繁发送短信
        cache = caches['code']
        if cache.get(f'sms_flag_{user.id}'):
            return Response({'message': '请不要频繁发送短信'}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        # 发送短信
        sms_code = f"{random.randint(1000, 9999)}"
        cache.set(f"sms_{user.mobile}", sms_code, 300)
        cache.set(f"sms_flag_{user.id}", '1', timeout=60)
        send_sms_code.delay(user.mobile, sms_code)
        return Response({'message': '短信验证码已发送'})
    # 验证身份
    def patch(self,request):
        serializer = CenterVerifySmsSerializer(data=request.data,context={'request':request})
        # 校验数据
        serializer.is_valid(raise_exception=True)
        cache = caches['code']
        cache.set(f"sms_passed_{request.user.id}", '1', 600)
        cache.delete(f"sms_{request.user.mobile}")
        return Response({"message": '身份验证成功'})

# 用户中心[更改手机号]
class CenterChangeSmsView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CenterChangeMobileSerializer
    # 获取验证码
    def post(self,request):
        user = request.user
        cache = caches['code']
        mobile = request.query_params.get('mobile')
        # 防止前端传None，给None发送短信
        if not mobile or not re.match(r'^1[3-9]\d{9}$', mobile):
            return Response({'message':'请填写正确的手机号'},status=status.HTTP_400_BAD_REQUEST)
        # 检查是否频繁发送短信
        if cache.get(f'sms_flag_{mobile}'):
            return Response({'message':'请勿频繁发送短信'},status=status.HTTP_429_TOO_MANY_REQUESTS)
        sms_code = f"{random.randint(1000, 9999)}"
        cache.set(f"sms_{mobile}", sms_code, 300)
        cache.set(f"sms_flag_{mobile}", '1', timeout=60)
        send_sms_code.delay(mobile,sms_code)
        return Response({'message':'短信验证码已发送'})
    def patch(self,request):
        # 验证短信验证码并换绑
        user = request.user
        serializer = self.get_serializer(instance=user, data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

# 用户中心[绑定/换绑邮箱]
class CenterEmailView(APIView):
    permission_classes = [IsAuthenticated]
    # 获取邮箱验证码
    def post(self,request):
        serializer = CenterSendEmailSerializer(data=request.query_params,context={'request':request})
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        # 检测是否重复发送验证码
        cache = caches['code']
        if cache.get(f"email_flag_{request.user.id}"):
            return Response({'message': '请勿频繁发送'},status=status.HTTP_429_TOO_MANY_REQUESTS)
        # 生成邮箱验证码，并存进Redis
        email_code = f"{random.randint(100000, 999999)}"
        cache.set(f"email_{email}", email_code, 300)
        cache.set(f"email_flag_{request.user.id}", '1', timeout=60)
        from celery_tasks.email.tasks import send_email
        send_email.delay(email, email_code)
        return Response({"message": "邮箱验证码已发送"})
    # 绑定邮箱
    def patch(self,request):
        user = request.user
        serializer = CenterVerifyEmailSerializer(instance=user, data=request.data,context={'request':request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)