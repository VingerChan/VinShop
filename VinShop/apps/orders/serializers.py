from rest_framework import serializers
from apps.goods.models import SKU
from apps.orders.models import OrderInfo
class SettlementQuerySerializer(serializers.Serializer):
    sku_id = serializers.IntegerField(required=False)
    count = serializers.IntegerField(required=False,min_value=1)
    def validate(self,attrs):
        if ('sku_id' in attrs) != ('count' in attrs):
            raise serializers.ValidationError('缺失参数')
        return attrs
class OrderSettlementSKUSerializer(serializers.ModelSerializer):
    default_image_url = serializers.SerializerMethodField()
    count = serializers.SerializerMethodField()
    amount = serializers.SerializerMethodField()
    class Meta:
        model =SKU
        fields = ['id','name','price','stock','default_image_url','count','amount']
    def get_default_image_url(self,obj):
        return obj.default_image.url if obj.default_image else ''
    def get_count(self,obj):
        return self.context['counts'].get(obj.id,0)
    def get_amount(self,obj):
        return obj.price * self.context['counts'].get(obj.id,0)

class OrderCommitSKUSerializer(serializers.Serializer):
    sku_id = serializers.IntegerField(min_value=1)
    count = serializers.IntegerField(min_value=1)
    note = serializers.CharField(required=False,allow_blank=True,max_length=200,default='')

class OrderCommitSerializer(serializers.Serializer):
    address_id = serializers.IntegerField()
    pay_method = serializers.ChoiceField(choices=OrderInfo.PAY_METHODS_CHOICES)
    skus = OrderCommitSKUSerializer(many=True,required=False,allow_empty=False)
    # 幂等键，前端每次下单生成一次UUID
    client_token = serializers.CharField(max_length=64)
    # 单个SKU 立即购买结算 提交订单
    sku_id = serializers.IntegerField(required=False)
    count = serializers.IntegerField(required=False,min_value=1)
    note = serializers.CharField(required=False,allow_blank=True,max_length=200,default='')

    def validate(self,attrs):
        if ('count' in attrs) != ('sku_id' in attrs):
            raise serializers.ValidationError('缺失参数')
        if 'skus' in attrs and 'sku_id' in attrs:
            raise serializers.ValidationError('skus和sku_id不能同时传')
        if 'skus' not in attrs and 'sku_id' not in attrs:
            raise serializers.ValidationError('请提交要结算的商品')
        if 'skus' in attrs and len({item['sku_id'] for item in attrs['skus']}) != len(attrs['skus']):
            raise serializers.ValidationError('skus中sku_id不能重复')
        return attrs