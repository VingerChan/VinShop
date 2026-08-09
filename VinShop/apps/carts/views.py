from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.carts.serializers import CartSerializer
from utils import carts
from django_redis import get_redis_connection

class CartView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self,request):             # 添加商品到购物车
        serializer = CartSerializer(data=request.data,context={'request': request})
        serializer.is_valid(raise_exception=True)
        # 校验 sku合法性 和 sku库存成功后，添加购物车
        carts.add(request.user.id,serializer.validated_data['sku_id'],serializer.validated_data['count'])
        # 返回购物车中最新总件数
        cart_count = carts.total_count(request.user.id)
        return Response({'cart_count':cart_count},status=status.HTTP_201_CREATED)

