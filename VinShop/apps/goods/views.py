from django.db.models import Prefetch
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from apps.goods.serializers import HomePageSerializer,SKUSerializer
from apps.goods.models import GoodsChannelGroup,GoodsChannel,ContentCategory
from utils.recommend import get_popular_skus

class HomePageView(APIView):
    def get(self,request):
        # 一个频道组有多个频道
        # 查所有频道组，并提前把它们的 channels 批量查好
        # 只填充一个“缓存”，让后续访问关系时不用再查库
        groups = GoodsChannelGroup.objects.prefetch_related(
            Prefetch(
                'goodschannel_set',     # 关联名
                queryset = GoodsChannel.objects.select_related('category').prefetch_related('category__subs__subs').all()
            )
        ).all()
        # 返回一个QuerySet，对象是ContentCategory
        contents = ContentCategory.objects.prefetch_related('contents').all()
        serializer = HomePageSerializer(instance={
            'groups' : groups,
            'content_categories' : contents,
        })
        return Response(serializer.data)

class RecommendView(APIView):
    def get(self,request):
        skus = get_popular_skus()
        serializer = SKUSerializer(skus, many=True)
        return Response(serializer.data)