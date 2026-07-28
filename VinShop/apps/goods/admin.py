from django.contrib import admin
from apps.goods.models import GoodsCategory,GoodsChannelGroup,GoodsChannel


admin.site.register(GoodsCategory)
admin.site.register(GoodsChannelGroup)
admin.site.register(GoodsChannel)