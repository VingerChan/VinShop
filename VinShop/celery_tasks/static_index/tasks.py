import logging
from celery_tasks.main import app
from apps.goods.models import GoodsChannelGroup,GoodsChannel,ContentCategory
from django.db.models import Prefetch
from django.template import loader
import os
from django.conf import settings

logger = logging.getLogger(__name__)

# 生成首页静态文件
@app.task
def generate_static_index():
    try:
        # 查询目录数据
        groups = GoodsChannelGroup.objects.prefetch_related(
            Prefetch(
                'goodschannel_set',
                queryset=GoodsChannel.objects.select_related('category').prefetch_related('category__subs__subs').all()
            )
        ).all()
        # 查询广告数据
        contents = ContentCategory.objects.prefetch_related('contents').all()
        # 组装分类数据
        categories = {'groups':[],'contents':{}}
        for group in groups:    # 目录内容
            group_data = {    # 频道组
                'id':group.id,
                'name':group.name,
                'channels':[]
            }
            # 遍历当前频道组的所有一级目录
            for channel in group.goodschannel_set.all().order_by('sequence'):
                channel_data = {
                    'id' : channel.id,
                    'category_name' : channel.category.name,
                    'sub_category' : []
                }
                for sub in channel.category.subs.all():    # 二级目录
                    sub_data = {
                        'id' : sub.id,
                        'name' : sub.name,
                        'subs' : [{'id' : grand.id,'name':grand.name} for grand in sub.subs.all()]
                    }
                    channel_data['sub_category'].append(sub_data)
                group_data['channels'].append(channel_data)
            categories['groups'].append(group_data)
        for content_cat in contents:    # 广告内容
            categories['contents'][content_cat.key] = [
                {'id' : t.id,'img_url' : t.image.url if t.image else '','link' : t.link} for t in content_cat.contents.filter(is_active=True).order_by('sequence')
            ]
        # 渲染模板
        template = loader.get_template('index.jinja2',using='django_jinja')
        html_content = template.render({'categories': categories})
        # 写入静态文件
        file_path = os.path.join(settings.BASE_DIR,'static','pages','index.html')
        """
            os.path.dirname(file_path)提取目录部分去掉文件名(index.html)
            os.makedirs(path,exist_ok=True)递归创建目录,父目录必须存在,所以先拿到目录路径
            如果没有exist_ok=True(默认False),目录存在时会抛出FileExistsError
        """
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path,'w',encoding='utf-8') as f:
            f.write(html_content)
        logger.info(f"首页静态文件已生成: {file_path}")
        return f"首页静态文件已生成: {file_path}"
    except Exception as e:
        logger.error(f"生成首页静态文件失败: {str(e)}",exc_info=True)
        raise


