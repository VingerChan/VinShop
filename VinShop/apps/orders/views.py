from decimal import Decimal
from django.conf import settings
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.orders.models import OrderInfo
from apps.goods.models import SKU
from apps.users.serializers import AddressSerializer
from utils import carts
from apps.orders.serializers import OrderSettlementSKUSerializer


# 获取订单结算页面
# 收获地址、商品清单、金额汇总、支付方式
class OrderSettlementView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self,request):
        user = request.user
        # 获取购物车商品 以及 选中的sku_id
        cart = carts.get_all(user.id)
        selected_ids = carts.get_selected(user.id)
        # 每个地址各查 province / city / district
        # 使用select_related变成1次JOIN查完
        addresses = user.address.all().select_related('province','city','district')
        result = {
            'default_address' : user.default_address.id if user.default_address else None,
            'addresses' : AddressSerializer(addresses,many=True).data,
            'skus' : [],
            'freight' : Decimal('0.00'),
            'total_count' : 0,
            'total_amount' : Decimal('0.00'),
            'final_amount' : Decimal('0.00'),
            'pay_methods' : [{'id':value,'name':name} for value,name in OrderInfo.PAY_METHODS_CHOICES],
        }
        # 如果
        if not selected_ids:
            return Response(result)
        # 提前触发查询，避免重复查数据库
        skus = list(SKU.objects.filter(id__in=selected_ids,is_launched=True))
        total_count = 0
        total_amount = Decimal('0.00')
        for sku in skus:
            count = cart[sku.id]
            if count > sku.stock:
                return Response({'message':f"商品 [{sku.name}] 库存不足，请调整数量"},status=status.HTTP_400_BAD_REQUEST)
            total_count += count
            total_amount += sku.price * count
        # 计算运费
        freight = Decimal('0.00') if total_amount >= settings.FREE_FREIGHT_LIMIT else settings.FREIGHT
        result.update({
            'skus' : OrderSettlementSKUSerializer(skus,many=True,context={'counts':cart}).data,
            'freight' : freight,
            'total_count' : total_count,
            'total_amount' : total_amount,
            'final_amount' : total_amount + freight,
        })
        return Response(result)