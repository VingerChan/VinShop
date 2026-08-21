from rest_framework import serializers
from apps.comments.models import Comment

class CommentCreateSerializer(serializers.Serializer):
    order_goods_id = serializers.IntegerField()
    score = serializers.ChoiceField(choices=Comment.SCORE_CHOICES)
    content = serializers.CharField(required=False,allow_blank=True,max_length=2000,default='')
    images = serializers.ListSerializer(child=serializers.CharField(max_length=200),required=False,default=list,max_length=6)
    video = serializers.CharField(required=False,allow_blank=True,default='',max_length=200)
    is_anonymous = serializers.BooleanField(required=False,default=False)