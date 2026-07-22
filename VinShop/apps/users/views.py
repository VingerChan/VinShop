from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.generics import CreateAPIView, GenericAPIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
from apps.users.serializers import UserRegisterSerializer,LoginSerializer
from apps.users.models import User
from VinShop.settings import FDFS_BASE_URL,FDFS_CLIENT_CONF
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
class ProfileView(GenericAPIView,):
    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileSerializer
    # 用户中心获取个人资料
    def get(self,request):
        serializer = self.get_serializer(request.user.profile)
        return Response(serializer.data)
    def post(self,request):
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