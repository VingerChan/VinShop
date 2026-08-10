from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.carts.serializers import CartSerializer,CartItemSerializer,SelectAllSerializer,CartItemSelectSerializer,CartCountSerializer
from apps.goods.models import SKU
from utils import carts
from decimal import Decimal
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
    def get(self,request):          # 获取购物车
        # 一次性读出{sku_id:count}
        cart = carts.get_all(request.user.id)
        # 如果购物车为空
        if not cart:
            return Response({'cart_count':0,'total_selected':0,'total_amount':Decimal('0.00'),'cart':[]})
        # 查询出购物车的 SKU
        skus = SKU.objects.filter(id__in=cart.keys(),is_launched=True)
        # 读出勾选集合    {sku1,sku2,sku3,sku4}
        selected_ids = carts.get_selected(request.user.id)
        cart_count=0
        total_selected=0
        total_amount=Decimal('0.00')
        for sku in skus:
            sku_count = cart[sku.id]
            cart_count += sku_count
            # # 判断sku.id是否在selected_ids中，存在返回True
            if sku.id in selected_ids:
                total_selected += sku_count
                total_amount += sku.price * sku_count
        serializer = CartItemSerializer(skus,many=True,context={'counts':cart,'selected':selected_ids})
        return Response({'cart_count':cart_count,'total_selected':total_selected,'total_amount':total_amount,'cart':serializer.data})

# 全选 / 取消全选
class CartSelectAllView(APIView):
    permission_classes = [IsAuthenticated]
    def put(self,request):
        serializer = SelectAllSerializer(data=request.data,context={'request': request})
        # 校验是否传了selected 以及 selected是否为True/False
        serializer.is_valid(raise_exception=True)
        # 接收前端发送的 是否全选(True/False)来判断
        carts.select_all(request.user.id,serializer.validated_data['selected'])
        return Response(status=status.HTTP_204_NO_CONTENT)

# 单个商品 勾选 / 取消勾选
class CartItemSelectView(APIView):
    permission_classes = [IsAuthenticated]
    def put(self,request,sku_id):
        serializer = CartItemSelectSerializer(data=request.data,context={'sku_id':sku_id,'request':request})
        serializer.is_valid(raise_exception=True)
        carts.select(request.user.id,sku_id,serializer.validated_data['selected'])
        return Response(status=status.HTTP_204_NO_CONTENT)

class CartItemView(APIView):
    permission_classes = [IsAuthenticated]
    # 修改商品count
    def put(self,request,sku_id):
        if not carts.exists(request.user.id,sku_id):
            return Response({'message':'商品不在购物车中'},status=status.HTTP_404_NOT_FOUND)
        serializer = CartCountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            sku = SKU.objects.get(id=sku_id,is_launched=True)
        except SKU.DoesNotExist:
            return Response({'message':'商品不存在或已下架'},status=status.HTTP_404_NOT_FOUND)
        #
        if serializer.validated_data['count'] > sku.stock:
            return Response({'message':'商品库存不足'},status=status.HTTP_400_BAD_REQUEST)
        carts.update_count(request.user.id,sku_id,serializer.validated_data['count'])
        return Response({'cart_count':carts.total_count(request.user.id)})
    def delete(self,request,sku_id):
        if not carts.exists(request.user.id,sku_id):
            return Response({'message':'商品不在购物车中'},status=status.HTTP_404_NOT_FOUND)
        carts.remove(request.user.id,sku_id)
        return Response(status=status.HTTP_204_NO_CONTENT)