import logging
import os
from apps.goods.models import SKU,SKUSpec
from django.conf import settings
from django.template import loader

logger = logging.getLogger(__name__)

# 生成单个商品详情页静态化文件
def static_sku_detail(sku_id):
    try:
        sku = SKU.objects.select_related('spu').prefetch_related('images').get(pk=sku_id,is_launched=True)
    except SKU.DoesNotExist:
        logger.warning(f"SKU {sku_id} 不存在或已下架，跳过静态化")
        return
    # 构建SKUImage
    images = [sku_image.img.url for sku_image in sku.images.all()]
    """构建规格数据"""
    spu = sku.spu
    skus = spu.skus.filter(is_launched=True)    # 获取父spu的所有子sku
    spec_skus = SKUSpec.objects.filter(sku__in=skus)
    spec_skus_dict = {}
    for spec_sku in spec_skus:
        spec_skus_dict.setdefault(spec_sku.option.id,[]).append(spec_sku.sku_id)
    # 获取SPUSpec的规格名字
    specs = spu.specs.prefetch_related('options')    # 预加载SPUSpec 和 SpecOption
    spec_data = []
    for spec in specs:    # SPUSpec
        options = []
        for option in spec.options.all():    # SpecOption
            options.append({
                'option_id' : option.id,
                'value' : option.value,
                'skus' : spec_skus_dict.get(option.id,[]),    # 这个规格选项有什么sku_id
            })
        spec_data.append({'name':spec.name,'options':options})
    # 组装模板数据
    sku_data = {
        'id' : sku.id,
        'name' : sku.name,
        'price' : str(sku.price),
        'stock' : sku.stock,
        'sales' : sku.sales,
        'comments' : sku.comments,
        'default_image' : sku.default_image.url if sku.default_image else '',
        'images' : images,
        'spu' : {'id':spu.id,'name':spu.name,'desc':spu.desc},
        'specs' : spec_data
    }
    # 渲染模板
    template = loader.get_template('detail.jinja2',using='django_jinja')
    html_content = template.render({'sku':sku_data})
    # 写入静态文件
    file_path = os.path.join(settings.BASE_DIR,'static','pages','detail',f'{sku_id}.html')
    os.makedirs(os.path.dirname(file_path),exist_ok=True)
    with open(file_path,'w',encoding='utf-8') as f:
        f.write(html_content)
    logger.info(f"商品详情静态文件已生成: {file_path}")
    return f"商品详情静态文件已生成: {file_path}"

# 全量静态化所有已上架SKU
def static_all_sku_detail():
    # flat将元组(1,)(2,)变成列表[1,2]
    sku_ids = list(SKU.objects.filter(is_launched=True).values_list('id',flat=True))
    logger.info(f"开始全量静态化，共{len(sku_ids)}个SKU")
    for sku_id in sku_ids:
        static_sku_detail(sku_id)
