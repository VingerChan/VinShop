from django.shortcuts import render
from django.utils import timezone
from django_redis import get_redis_connection
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.conf import settings
from fdfs_client.client import Fdfs_client
import logging

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
