from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_redis import get_redis_connection
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from django.conf import settings
from fdfs_client.client import Fdfs_client
import logging
from apps.comments.serializers import CommentCreateSerializer,CommentSerializer
from apps.orders.models import OrderInfo,OrderGoods
from apps.comments.models import Comment
from apps.goods.models import SKU
from django.db.models import F,Count,Q

logger = logging.getLogger(__name__)

class CommentUploadView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self,request):
        file = request.FILES.get('file')
        if not file:
            return Response({'message':'请选择要上传的文件'},status=status.HTTP_400_BAD_REQUEST)
        content_type = file.content_type    # 获取文件类型
        # 校验文件类型是否合格
        if content_type not in settings.ALLOWED_IMAGE_TYPES and content_type not in settings.ALLOWED_VIDEO_TYPES:
            return Response({'message': '仅支持图片(jpeg/png/webp)或视频(mp4)'},status=status.HTTP_400_BAD_REQUEST)
        if content_type in settings.ALLOWED_IMAGE_TYPES and file.size > settings.COMMENT_IMAGE_MAX_SIZE:
            return Response({'message':'图片大小不能超过5MB'},status=status.HTTP_400_BAD_REQUEST)
        if content_type in settings.ALLOWED_VIDEO_TYPES and file.size > settings.COMMENT_VIDEO_MAX_SIZE:
            return Response({'message':'视频大小不能超过100MB'},status=status.HTTP_400_BAD_REQUEST)
        try:
            client = Fdfs_client(settings.FDFS_CLIENT_CONF)
            result = client.upload_by_buffer(file.read())
        except Exception as e:
            logger.warning('评价文件上传失败：%s',e,exc_info=True)
            return Response({'message':'文件上传失败'},status=status.HTTP_400_BAD_REQUEST)
        if result.get('Status') != 'Upload successed.':
            return Response({'message':'文件上传失败'},status=status.HTTP_400_BAD_REQUEST)
        file_id = result['Remote file_id'].decode()    # 获取相对路径
        expire_ts = timezone.now().timestamp() + settings.FILE_TIMEOUT
        try:
            redis_conn = get_redis_connection('file')
            redis_conn.zadd(settings.FILE_KEY, {file_id: expire_ts})
        except Exception as e:
            logger.warning("文件上传成功但写入Redis失败 file_id: %s,score: %s",file_id,expire_ts,exc_info=True)
            client.delete_file(file_id.encode())
            return Response({'message':'系统出错，请重新上传'},status=status.HTTP_503_SERVICE_UNAVAILABLE)
        # file_id存库    url展示
        return Response({'file_id': file_id, 'url': settings.FDFS_BASE_URL + file_id})

class CommentCreateView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self,request):
        # 校验数据
        serializer = CommentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # 获取校验好的数据
        data = serializer.validated_data
        user = request.user
        with transaction.atomic():
            try:    # 校验该订单是否存在 属于当前用户
                order_good = OrderGoods.objects.select_related('order').get(pk=data['order_goods_id'],order__user=user)
            except OrderGoods.DoesNotExist:
                return Response({'message':'订单商品不存在'},status=status.HTTP_400_BAD_REQUEST)
            # 防止同一订单并发评价 导致最终订单状态判断错误
            order = OrderInfo.objects.select_for_update().get(pk=order_good.order_id)
            # 拿到OrderGoods的最新is_commented信息 并加锁
            order_good = OrderGoods.objects.select_for_update().select_related('sku','sku__spu').get(pk=order_good.pk)
            if order.status != OrderInfo.STATUS_ENUM['UNCOMMENT']:
                return Response({'message':'订单当前状态不可评价'},status=status.HTTP_400_BAD_REQUEST)
            if order_good.is_commented:
                return Response({'message':'该商品已评价'},status=status.HTTP_400_BAD_REQUEST)
            # 校验图片 / 视频数据一致性
            redis_conn = get_redis_connection('file')
            for file_id in data['images']:
                if not redis_conn.zscore(settings.FILE_KEY, file_id):
                    return Response({'message': '文件不存在或已过期'}, status=status.HTTP_400_BAD_REQUEST)
            if data['video']:
                if not redis_conn.zscore(settings.FILE_KEY, data['video']):
                    return Response({'message':'文件不存在或已过期'},
                                    status=status.HTTP_400_BAD_REQUEST)
            Comment.objects.create(
                user=user,
                spu=order_good.sku.spu,
                sku=order_good.sku,
                order=order,
                order_goods=order_good,
                score=data['score'],
                content=data['content'],
                images=data['images'],
                video=data['video'],
                is_anonymous=data['is_anonymous'],
            )
            # 创建评价成功后 更新OrderGoods评价状态
            order_good.is_commented = True
            order_good.save(update_fields=['is_commented'])
            # 更新SKU的comments评论数
            SKU.objects.filter(pk=order_good.sku_id).update(comments=F('comments') + 1)
            # 根据OrderInfo判断子OrderGoods是否都已经评价完成 并根据情况更新状态
            if not order.skus.filter(is_commented=False).exists():
                order.status = OrderInfo.STATUS_ENUM['FINISHED']
                order.save(update_fields=['status'])
        # 评价成功后 清理Redis对应标记的孤儿文件
        try:    # 避免Redis故障返回500给用户
            redis_conn = get_redis_connection('file')
            for file_id in data['images']:
                redis_conn.zrem(settings.FILE_KEY, file_id)
            if data['video']:
                redis_conn.zrem(settings.FILE_KEY, data['video'])
        except Exception as e:
            logger.warning('评价成功但清理文件标记失败: %s',e,exc_info=True)
        return Response({'message':'评价成功'},status=status.HTTP_201_CREATED)

# 商品详情页的评价展示
class CommentListView(APIView):
    def get(self,request,sku_id):
        sku = get_object_or_404(SKU,pk=sku_id)
        # 获取SPU所有评价
        queryset = Comment.objects.filter(spu_id=sku.spu_id).select_related('user__profile').prefetch_related('sku__specs__option')
        comment_status = queryset.aggregate(
            all_count=Count('id'),
            good=Count('id',filter=Q(score__gte=4)),    # 好评4～5个数
            mid=Count('id',filter=Q(score=3)),    # 中评3星个数
            bad=Count('id',filter=Q(score__lte=2)),    # 差评1～2星个数
            media=Count('id',filter=~Q(images=[])|~Q(video=''))

        )
        # 根据好评 中评 差评筛选评论
        score_type = request.query_params.get('score_type')
        if score_type == 'good':
            queryset = queryset.filter(score__gte=4)
        elif score_type == 'mid':
            queryset = queryset.filter(score=3)
        elif score_type == 'bad':
            queryset = queryset.filter(score__lte=2)
        elif score_type is not None:
            return Response({'message':'score_type仅支持good/mid/bad'},status=status.HTTP_400_BAD_REQUEST)
        # 筛选晒图
        has_media = request.GET.get('has_media')
        if has_media == 'true':
            # 图片URL不为空 或 videos不为空 即为晒图
            queryset = queryset.filter(~Q(images=[])|~Q(video=''))
        # 款式筛选
        raw_sku_id = request.query_params.get('sku_id')
        if raw_sku_id is not None:
            try:
                queryset = queryset.filter(sku_id=int(raw_sku_id))
            except ValueError:
                return Response({'message':'sku_id必须是整数'},status=status.HTTP_400_BAD_REQUEST)
        # 分页
        paginator = PageNumberPagination()
        paginator.page_size_query_param = 'page_size'    # 前端不传默认settings
        page = paginator.paginate_queryset(queryset, request)
        serializer = CommentSerializer(page,many=True)
        # get_paginated_response返回DRF标准分页格式: {count,next,previous,results}
        response = paginator.get_paginated_response(serializer.data)
        # 追加自定义字段
        all_count = comment_status['all_count']
        # 好评率
        good_rate = round(comment_status['good']*100/all_count) if all_count else 0
        response.data['good_rate'] = good_rate
        response.data['counts'] = {
            'all' : comment_status['all_count'],
            'good' : comment_status['good'],
            'mid' : comment_status['mid'],
            'bad' : comment_status['bad'],
            'media' : comment_status['media'],
        }
        return response