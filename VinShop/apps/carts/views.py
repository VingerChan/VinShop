from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.carts.serializers import CartSerializer,CartItemSerializer
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
            return Response({'cart_count':0,'total_selected':0,'total_amount':0.00,'cart':[]})
        # 查询出购物车的 SKU
        skus = SKU.objects.filter(id__in=cart.keys(),is_launched=True)
        # 读出勾选集合    {sku1,sku2,sku3,sku4}
        selected_ids = carts.get_selected(request.user.id)
        cart_count=0
        total_selected=0
        total_amount=Decimal('0.00')
        cart_list = []      # 购物车列表
        for sku in skus:
            sku_count = cart[sku.id]
            # 判断sku.id是否在selected_ids中，存在返回True
            selected = sku.id in selected_ids
            amount = sku.price * sku_count
            cart_count += sku_count
            # 如果当前SKU被勾选
            if selected:
                total_selected += sku_count
                total_amount +=amount
            cart_list.append({
                'sku_id':sku.id,
                'name':sku.name,
                'price':sku.price,
                'default_image':sku.default_image.url if sku.default_image else '',
                'stock':sku.stock,
                'count':sku_count,
                'selected':selected,
                'amount':amount,
            })
        serializer = CartItemSerializer(cart_list,many=True)
        return Response({'cart_count':cart_count,'total_selected':total_selected,'total_amount':total_amount,'cart':cart_list})