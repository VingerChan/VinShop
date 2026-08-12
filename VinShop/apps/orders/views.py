from decimal import Decimal
from django.conf import settings
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.orders.models import OrderInfo
from apps.goods.models import SKU
from apps.users.serializers import AddressSerializer
from utils import carts
from apps.orders.serializers import SettlementQuerySerializer,OrderSettlementSKUSerializer


# 获取订单结算页面
# 收获地址、商品清单、金额汇总、支付方式
class OrderSettlementView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self,request):
        user = request.user
        qs = SettlementQuerySerializer(data=request.query_params)
        qs.is_valid(raise_exception=True)
        params = qs.validated_data
        if params:
            cart = {params['sku_id']:params['count']}
            selected_ids = {params['sku_id']}
        else:
            # 获取购物车商品 以及 选中的sku_id
            cart = carts.get_all(user.id)
            selected_ids = carts.get_selected(user.id)
        # 每个地址各查 province / city / district
        # 使用select_related变成1次JOIN查完
        addresses = user.address.all().select_related('province','city','district')
        result = {
            'default_address' : user.default_address_id,
            'addresses' : AddressSerializer(addresses,many=True).data,
            'skus' : [],
            'invalid_skus' : [],
            'freight' : Decimal('0.00'),
            'total_count' : 0,
            'total_amount' : Decimal('0.00'),
            'final_amount' : Decimal('0.00'),
            'pay_methods' : [{'id':value,'name':name} for value,name in OrderInfo.PAY_METHODS_CHOICES],
        }
        # 如果购物车中没有选取任何SKU
        if not selected_ids:
            return Response(result)

        # 提前触发查询，避免重复查数据库
        skus = list(SKU.objects.filter(id__in=selected_ids))
        valid_skus = []             # 上架并且在购物车中的商品
        invalid_skus = []           # 下架并且在购物车中的商品
        # 根据sku 分出需要展示的sku 和 因错误而软提示的sku
        for sku in skus:
            count = cart[sku.id]
            if not sku.is_launched:
                invalid_skus.append({'id':sku.id,'name':sku.name,'reason':'商品已下架'})
            elif count > sku.stock:
                invalid_skus.append({'id':sku.id,'name':sku.name,'reason':'库存不足，请调整数量'})
            else:
                valid_skus.append(sku)
        # 查找不存在的商品id  A - B 表示 集合差集
        not_found_ids = selected_ids - {sku.id for sku in skus}
        invalid_skus.extend({'id':sku_id,'name':'商品不存在','reason':'商品不存在'}for sku_id in sorted(not_found_ids))
        result['invalid_skus'] = invalid_skus

        # 如果没有有效商品，结算页照常打开
        if not valid_skus:
            return Response(result)
        total_count = 0
        total_amount = Decimal('0.00')
        for sku in valid_skus:
            count = cart[sku.id]
            total_count += count
            total_amount += sku.price * count
        # 计算运费
        freight = Decimal('0.00') if total_amount >= settings.FREE_FREIGHT_LIMIT else settings.FREIGHT
        result.update({
            'skus' : OrderSettlementSKUSerializer(valid_skus,many=True,context={'counts':cart}).data,
            'freight' : freight,
            'total_count' : total_count,
            'total_amount' : total_amount,
            'final_amount' : total_amount + freight,
        })
        return Response(result)