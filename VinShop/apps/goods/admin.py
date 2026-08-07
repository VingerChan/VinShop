from django.contrib import admin
from apps.goods.models import GoodsCategory,GoodsChannelGroup,GoodsChannel,Brand,SPU,SKU,SPUSpec,SpecOption,SKUSpec,ContentCategory,Content,SKUImage

# SPU.default_sku只能选择当前SPU下的SKU
class SPUAdmin(admin.ModelAdmin):
    # 触发时机：Admin为模型的每一个ForeignKey/OneToOneField生成表单字段时调用
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # db_filed:当前正在处理的外键字段对象
        # 只对目标字段生效，其余外键不受影响，直接走super()的默认逻辑
        if db_field.name == 'default_sku':
            spu_id = request.resolver_match.kwargs.get('object_id')
            if spu_id:
                # 默认就是这个外键的全表查询集
                kwargs['queryset'] = SKU.objects.filter(spu_id=spu_id)
        if db_field.name == 'category':
            kwargs['queryset'] = GoodsCategory.objects.filter(subs__isnull=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

class SKUAdmin(admin.ModelAdmin):
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'default_image':
            sku_id = request.resolver_match.kwargs.get('object_id')
            if sku_id:
                kwargs['queryset'] = SKUImage.objects.filter(sku_id=sku_id)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

admin.site.register(GoodsCategory)
admin.site.register(GoodsChannelGroup)
admin.site.register(GoodsChannel)
admin.site.register(Brand)
admin.site.register(SPU,SPUAdmin)
admin.site.register(SKU,SKUAdmin)
admin.site.register(SPUSpec)
admin.site.register(SpecOption)
admin.site.register(SKUSpec)
admin.site.register(ContentCategory)
admin.site.register(Content)
admin.site.register(SKUImage)