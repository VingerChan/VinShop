from django.contrib import admin
from apps.goods.models import GoodsCategory,GoodsChannelGroup,GoodsChannel,Brand,SPU,SKU,SPUSpec,SpecOption,SKUSpec


admin.site.register(GoodsCategory)
admin.site.register(GoodsChannelGroup)
admin.site.register(GoodsChannel)
admin.site.register(Brand)
admin.site.register(SPU)
admin.site.register(SKU)
admin.site.register(SPUSpec)
admin.site.register(SpecOption)
admin.site.register(SKUSpec)