from django.shortcuts import render
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.generics import CreateAPIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
from apps.users.serializers import UserRegisterSerializer
from apps.users.models import User
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
            'access' : str(refresh.access_token),
            'refresh' : str(refresh),

        }
        return Response(data,status=status.HTTP_201_CREATED)