from rest_framework import serializers
from apps.goods.models import GoodsCategory,GoodsChannel,Content
from VinShop.settings import FDFS_BASE_URL


# 只返回id和name，用于嵌套在频道下的子分类列表
class SubCategorySerializer(serializers.ModelSerializer):
    # 它是 DRF 中的一个 只读字段(read-only)用于：序列化时使用，不负责反序列化（不能用于创建/更新），必须配合一个 get_{field_name} 方法使用
    subs = serializers.SerializerMethodField()
    class Meta:
        model = GoodsCategory
        fields = ['id', 'name','subs']
    # 递归获取子目录
    def get_subs(self, obj):
        # obj 是当前序列化的 Category 对象
        children = obj.subs.all()
        if children:
            return SubCategorySerializer(children, many=True).data
        return []

class GoodsChannelSerializer(serializers.ModelSerializer):
    category_id = serializers.IntegerField(source='category.id')
    category_name = serializers.CharField(source='category.name')
    sub_category = serializers.SerializerMethodField()
    class Meta:
        model = GoodsChannel
        fields = ['id','sequence','category_id','category_name','sub_category']
    def get_sub_category(self, obj):
        children = obj.subs.all()
        return SubCategorySerializer(children, many=True).data

class GoodsChannelGroupSerializer(serializers.ModelSerializer):
    # 通过 goodschannel_set 反向拿到该组下的所有 GoodsChannel,再交给GoodsChannelSerializer
    channels = GoodsChannelSerializer(source='goodschannel_set',many=True)
    class Meta:
        model = GoodsChannelGroup
        fields = ['id','name','channels']

class ContentSerializer(serializers.ModelSerializer):
    img_url = serializers.SerializerMethodField()
    class Meta:
        model = Content
        fields = ['id','title','img_url','link']
    def get_img_url(self, obj):
        return FDFS_BASE_URL + obj.img_url