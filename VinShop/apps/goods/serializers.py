from rest_framework import serializers
from apps.goods.models import GoodsCategory,GoodsChannel,Content,GoodsChannelGroup,SKU,SPU,SKUSpec
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
    # 因为ModelSerializer，DRF在序列化GoodsChannel的query/instance时，会自动把对应的model instance作为obj传入
    def get_sub_category(self, obj):
        children = obj.category.subs.all()
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
        return obj.image.url if obj.image else ''

class HomePageSerializer(serializers.Serializer):
    groups = GoodsChannelGroupSerializer(many=True)
    contents = serializers.SerializerMethodField()
    # 普通的Serializer，没有绑定的model，所以obj完全由调用方决定，传dict，就是dict
    def get_contents(self, obj):
        categories = obj['content_categories']
        result = {}
        for cat in categories:
            active_content = cat.contents.filter(is_active=True)
            result[cat.key] = ContentSerializer(active_content, many=True).data
        return result

class SKUSerializer(serializers.ModelSerializer):
    default_img_url = serializers.SerializerMethodField()
    class Meta:
        model = SKU
        fields = ['id','name','price','comments','default_img_url','sales']
    def get_default_img_url(self, obj):
        if obj.default_image:
            return obj.default_image.url
        return ''

class SPUDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = SPU
        fields = ['id','name','desc']

class SKUDetailSerializer(serializers.ModelSerializer):
    default_image = serializers.SerializerMethodField()     # 默认展示图片
    images = serializers.SerializerMethodField()            # SKU图片
    spu = SPUDetailSerializer()
    specs = serializers.SerializerMethodField()
    class Meta:
        model = SKU
        fields = ['id','name','price','stock','sales','comments','default_image','images','spu','specs']
    def get_default_image(self, obj):
        if obj.default_image:
            return obj.default_image.url
        return ''
    def get_images(self, obj):
        return [image.img.url for image in obj.images.all()]
    def get_specs(self, obj):
        spu = obj.spu
        # 获取该SPU的所有SKU
        skus = spu.skus.filter(is_launched=True)
        # 查SPU所有规格选项
        spec_skus = SKUSpec.objects.filter(sku__in=skus)
        spec_skus_dict = {}
        for spec_sku in spec_skus:
            # 以 option_id 为 key，把对应的 sku_id 收集到一个列表中
            # 如果key不存在，则先创建一个空列表[]
            # 最终得出 option_id : [sku1,sku2]
            spec_skus_dict.setdefault(spec_sku.option_id,[]).append(spec_sku.sku_id)
        # SPU.specs.options.all()
        # 获取该SPU的所有规格
        specs = spu.specs.prefetch_related('options')
        spec_data = []
        # 假设该SPU有3个规格，一个一个遍历
        for spec in specs:
            options = []
            # 读某规格SPUSpec的所有规格选项option
            for option in spec.options.all():   # 读prefetch缓存
                options.append({
                    'option_id' : option.id,
                    'value' : option.value,
                    'skus' : spec_skus_dict.get(option.id,[])
                })
            spec_data.append({'name':spec.name,'options':options})
        return spec_data