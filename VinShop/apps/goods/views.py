from django.db.models import Prefetch
from django.shortcuts import render,get_object_or_404
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from apps.goods.serializers import HomePageSerializer,SKUSerializer,SKUDetailSerializer
from apps.goods.models import GoodsChannelGroup,GoodsChannel,ContentCategory,SKU
from utils.recommend import get_popular_skus
from apps.goods.documents import sku_query
from django.conf import settings
from utils.es_util import get_client

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

class SKUDetailView(APIView):
    def get(self,request,sku_id):
        # 先join把SKU和SPU放在同一张表，再反向查询SKU的所有image
        # sku = get_object_or_404(SKU,id=sku_id)
        sku = get_object_or_404(SKU.objects.select_related('spu').prefetch_related('images').filter(is_launched=True), id=sku_id)
        serializer = SKUDetailSerializer(sku)
        return Response(serializer.data)

class SearchView(APIView):

    def get(self,request):
        # 获取搜索关键字 并清除前后空格
        keyword = (request.query_params.get('keyword') or '').strip()
        if not keyword:
            return Response({'detail':'请输入关键字'},status=status.HTTP_400_BAD_REQUEST)
        # 获取指定页 和 页码大小
        try:
            page = int(request.query_params.get('page',1))
            page_size = int(request.query_params.get('page_size',20))
        except ValueError:
            return Response({'detail':'page/page_size 必须是整数'},status=status.HTTP_400_BAD_REQUEST)
        # 根据sales 或 -sales   lstrip为清除最左边的 -
        ordering = request.query_params.get('ordering','')
        if ordering and ordering.lstrip('-')  not in ('sales','comments','price'):
            return Response({'detail':'不支持的排序字段'},status=status.HTTP_400_BAD_REQUEST)
        # 获取价格区间参数
        try:
            min_price = request.query_params.get('min_price')
            max_price = request.query_params.get('max_price')
            min_price = float(min_price) if min_price else None
            max_price = float(max_price) if max_price else None
        except ValueError:
            return Response({'detail':'min_price/max_price 必须是数字(单位：元)'},status=status.HTTP_400_BAD_REQUEST)
        body = sku_query(keyword,page,page_size,ordering,min_price,max_price)
        result = get_client().search(index=settings.ES_SKU_INDEX,body=body)
        # 命中总数
        total = result['hits']['total']['value']
        # result['hits']['hits']是列表 存放SKU 数据
        es_ids = [hit['_id'] for hit in result['hits']['hits']]
        highlights = {}
        for hit in result['hits']['hits']:
            sku_id = int(hit['_id'])
            # 如果有高亮就提取高亮文本，否则返回None
            hl = hit.get('highlight',{}).get('name',[None])[0]
            highlights[sku_id] = hl
        # 在数据库返回的顺序是不确定的 要重新按照sku_ids进行排序
        skus = list(SKU.objects.filter(id__in=es_ids))
        sku_dict = {sku.id:sku for sku in skus}
        es_sku = [sku_dict[int(i)] for i in es_ids if int(i) in sku_dict]
        serializer = SKUSerializer(es_sku,many=True)
        return Response({
            'total':total,
            'page':page,
            'page_size':page_size,
            'skus':serializer.data,
            'highlights':highlights,
        })