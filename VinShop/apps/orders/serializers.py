from rest_framework import serializers
from apps.goods.models import SKU
from apps.orders.models import OrderInfo,OrderGoods
from django.conf import settings
from datetime import timedelta
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

class OrderGoodsSerializer(serializers.ModelSerializer):
    sku_id = serializers.IntegerField(source='sku.id')
    sku_name = serializers.CharField(source='sku.name')
    default_image_url = serializers.SerializerMethodField()
    class Meta:
        model = OrderGoods
        fields = ['sku_id','sku_name','default_image_url','count','price','note']
    def get_default_image_url(self,obj):
        return obj.sku.default_image.url if obj.sku.default_image else ''

class OrderInfoSerializer(serializers.ModelSerializer):
    status_text = serializers.SerializerMethodField()
    pay_method_text = serializers.SerializerMethodField()
    final_amount = serializers.SerializerMethodField()
    skus = OrderGoodsSerializer(many=True,read_only=True)   # 只允许序列化输出
    expire_ts = serializers.SerializerMethodField()
    class Meta:
        model = OrderInfo
        fields = ['order_id','create_time','expire_ts','status','status_text','pay_method','pay_method_text','receiver_name','receiver_mobile','receiver_address','total_count','total_amount','freight','final_amount','skus']
    def get_status_text(self,obj):
        # 用 Django 自带的方法：get_字段名_display()可以得到展示文本
        return obj.get_status_display()
    def get_pay_method_text(self,obj):
        return obj.get_pay_method_display()
    def get_final_amount(self,obj):
        return obj.total_amount + obj.freight
    def get_expire_ts(self,obj):
        if obj.status != obj.STATUS_ENUM['UNPAID']:
            return None
        expire_at = obj.create_time + timedelta(seconds=settings.ORDER_PAY_TIMEOUT)
        return int(expire_at.timestamp())
