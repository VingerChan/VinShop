from rest_framework import serializers
from apps.goods.models import SKU
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