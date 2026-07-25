from django.shortcuts import render
from rest_framework.generics import ListAPIView, RetrieveAPIView
from apps.areas.serializers import AreaSerializer
from apps.areas.models import Area
from django.core.cache import caches
class AreaListView(ListAPIView):
    serializer_class = AreaSerializer
    def get_queryset(self):
        # 查看省数据是否在Redis中缓存
        cache = caches['default']
        provinces = cache.get('provinces')
        # 如果不存在，就存进去
        if provinces is None:
            # Redis不支持QuerySet，所以需要将QuerySet转成list
            provinces = list(Area.objects.filter(parent__isnull=True))
            cache.set('provinces', provinces,60*60*24)
        return provinces

class SubAreaView(ListAPIView):
    serializer_class = AreaSerializer
    def get_queryset(self):
        pk = self.kwargs['pk']
        key = f"parent_{pk}"
        cache = caches['default']
        subs = cache.get(key)
        if subs is None:
            subs = list(Area.objects.filter(parent=pk))
            # 如果能获取得到市、区数据则缓存
            if subs:
                cache.set(key,subs, 60*60*24)
        return subs