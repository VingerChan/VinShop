from rest_framework import serializers
from apps.comments.models import Comment
from django.conf import settings

class CommentCreateSerializer(serializers.Serializer):
    order_goods_id = serializers.IntegerField()
    score = serializers.ChoiceField(choices=Comment.SCORE_CHOICES)
    content = serializers.CharField(required=False,allow_blank=True,max_length=2000,default='')
    images = serializers.ListField(child=serializers.CharField(max_length=200),required=False,default=list,max_length=6)
    video = serializers.CharField(required=False,allow_blank=True,default='',max_length=200)
    is_anonymous = serializers.BooleanField(required=False,default=False)

class CommentSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    sku = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
    video = serializers.SerializerMethodField()
    class Meta:
        model = Comment
        fields = ['id','create_time','user','is_anonymous','sku','score','content','images','video']
    def get_user(self,obj):
        if obj.is_anonymous:
            return {'nickname':'匿名用户','avatar':''}
        profile = getattr(obj.user,'profile',None)    # 获取用户资料
        nickname = profile.nickname if profile and profile.nickname else obj.user.username
        avatar=''
        if profile and profile.user_img:
            avatar = settings.FDFS_BASE_URL + profile.user_img if profile.user_img else ''
        return {'nickname':nickname,'avatar':avatar}

    def get_sku(self,obj):
        specs = [spec.option.value for spec in obj.sku.specs.all()]
        return {'id':obj.sku.id,'name':obj.sku.name,'specs':specs}

    def get_images(self,obj):
        return [settings.FDFS_BASE_URL + file_id for file_id in obj.images]

    def get_video(self,obj):
        return obj.video.url if obj.video else ''
