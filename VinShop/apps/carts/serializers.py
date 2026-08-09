from rest_framework import serializers
from apps.goods.models import SKU
from utils import carts
class CartSerializer(serializers.Serializer):
    sku_id = serializers.IntegerField()
    # min_value: DRF内建校验，count<1时自动报错，不用手写validate_count
    count = serializers.IntegerField(min_value=1)
    def validate_sku_id(self,value):
        try:
            sku = SKU.objects.get(id=value,is_launched=True)
        except SKU.DoesNotExist:
            raise serializers.ValidationError('商品不存在或已下架')
        # 把查询到的 sku 暂存进context ，供下面的validate()复用，避免二次查库
        self.context['sku'] = sku
        return value
    def validate(self,attrs):
        # 校验库存：购物车已有数量 + 本次新增count <= 库存
        sku = self.context['sku']
        cart = carts.get_all(self.context['request'].user.id)
        if cart.get(sku.id,0)+attrs['count'] > sku.stock:
            raise serializers.ValidationError('商品库存不足')
        return attrs

class CartItemSerializer(serializers.Serializer):
    sku_id = serializers.IntegerField()
    name = serializers.CharField()
    price = serializers.DecimalField(max_digits=10,decimal_places=2)
    default_image = serializers.CharField()
    stock = serializers.IntegerField()
    count = serializers.IntegerField()
    selected = serializers.BooleanField()
    amount = serializers.DecimalField(max_digits=10,decimal_places=2)