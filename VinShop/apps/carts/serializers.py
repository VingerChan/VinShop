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

class CartItemSerializer(serializers.ModelSerializer):
    default_image_url = serializers.SerializerMethodField()
    count = serializers.SerializerMethodField()
    selected = serializers.SerializerMethodField()
    amount = serializers.SerializerMethodField()
    class Meta:
        model = SKU
        fields=['id','name','price','default_image_url','stock','count','selected','amount']
    def get_default_image_url(self,obj):
        return obj.default_image.url if obj.default_image else ''
    def get_count(self,obj):
        return self.context['counts'].get(obj.id,0)
    def get_selected(self,obj):
        return obj.id in self.context['selected']
    def get_amount(self,obj):
        return obj.price * self.context['counts'].get(obj.id,0)

class SelectAllSerializer(serializers.Serializer):
    selected = serializers.BooleanField()

class CartItemSelectSerializer(serializers.Serializer):
    selected = serializers.BooleanField()
    def validate(self,attrs):
        sku_id = self.context['sku_id']
        user_id = self.context['request'].user.id
        if not carts.exists(user_id,sku_id):
            raise serializers.ValidationError('商品不在购物车中')
        return attrs