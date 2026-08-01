from django.contrib import admin
from apps.goods.models import GoodsCategory,GoodsChannelGroup,GoodsChannel,Brand,SPU,SKU,SPUSpec,SpecOption,SKUSpec,ContentCategory,Content,SKUImage


admin.site.register(GoodsCategory)
admin.site.register(GoodsChannelGroup)
admin.site.register(GoodsChannel)
admin.site.register(Brand)
admin.site.register(SPU)
admin.site.register(SKU)
admin.site.register(SPUSpec)
admin.site.register(SpecOption)
admin.site.register(SKUSpec)
admin.site.register(ContentCategory)
admin.site.register(Content)
admin.site.register(SKUImage)