from django.conf import settings
from utils.es_util import get_client
# 只有 text 类型的字段才会走分词器（analyzer），数值类型天然就不支持全文检索式的“分词匹配”
mappings = {
    'properties' : {
        # text + IK :要参与中文关键词匹配的字段
        'name' : {'type':'text','analyzer':'ik_max_word','search_analyzer':'ik_smart'},
        'spu_name' : {'type':'text','analyzer':'ik_max_word','search_analyzer':'ik_smart'},
        'brand_name' : {'type':'text','analyzer':'ik_max_word','search_analyzer':'ik_smart'},
        # 三级目录
        'category_1' : {'type':'text','analyzer':'ik_max_word','search_analyzer':'ik_smart'},
        'category_2' : {'type':'text','analyzer':'ik_max_word','search_analyzer':'ik_smart'},
        'category_3' : {'type':'text','analyzer':'ik_max_word','search_analyzer':'ik_smart'},
        # 只用于排序/展示/过滤 不参与分词匹配
        'price' : {'type':'integer'},
        'sales' : {'type':'integer'},
        'comments' : {'type':'integer'},
        'default_image' : {'type':'text','index':False},
        'is_launched' : {'type':'boolean'},
    }
}

# 高亮配置：命中的关键词用 <em> 包裹
HIGHLIGHT = {
    'pre_tags':  ['<em>'],
    'post_tags': ['</em>'],
    'fields':    {'name': {}},   # 只对 SKU 名称做高亮
}

# 把 Django 的 SKU 对象序列化成一条 ES 文档（dict）
def sku_doc(sku):
    cat = sku.spu.category
    return {
        'name' : sku.name,
        'spu_name' : sku.spu.name,
        'brand_name' : sku.spu.brand.name,
        'category_1' : (cat.parent.parent.name if cat.parent and cat.parent.parent else ''),
        'category_2' : (cat.parent.name if cat and cat.parent else ''),
        'category_3' : cat.name,
        'price' : int(sku.price*100),        # Decimal 元 -> int 分
        'sales' : sku.sales,
        'comments' : sku.comments,
        'default_image' : sku.default_image.url if sku.default_image else '',
        'is_launched' : sku.is_launched,
    }

# 幂等创建 sku 索引（存在则跳过）
def ensure_sku_index():
    client = get_client()
    if not client.indices.exists(index=settings.ES_SKU_INDEX):
        client.indices.create(index=settings.ES_SKU_INDEX,mappings=mappings)

# 构建搜索的 query DSL（布尔查询 = must 匹配关键词 + filter 过滤）
# 排序白名单
_SORTABLE = {'sales','comments','price'}
FIELDS = ['name','spu_name','brand_name','category_1','category_2','category_3']
def sku_query(keyword,page,page_size,ordering='',min_price=None,max_price=None):
    sort_body = []
    if ordering:        # 如果进行价格/评论数/销量排序
        # 判断用户选择的是否为降序 如果不是，则为False
        desc = ordering.startswith('-')
        # 如果为降序，则去除掉第一个 -
        field = ordering[1:] if desc else ordering
        if field in _SORTABLE:
            sort_body = [{field:{'order':'desc' if desc else 'asc'}}]
    # 价格区间：接口按'元'接，ES存的是'分'(*100换算)
    price_filter = {}
    if min_price is not None:
        price_filter['gte'] = int(float(min_price)*100)
    if max_price is not None:
        price_filter['lte'] = int(float(max_price)*100)
    body = {
        'query' : {
            'bool' : {
                # must : 关键词命中 只影响打分 参与排序相关度
                'must' : [{
                    'multi_match' : {
                        'query' : keyword,
                        'fields' : FIELDS,
                    }
                }],
                # filter ： 只过滤 不影响打分 (上架+价格区间)
                'filter' : [
                    # term ： 精准匹配(等值)
                    {'term' : {'is_launched' : True}},
                    # range :范围匹配(区间)
                    # *()让 可选过滤子句 按需整体存在 而不是塞一个空的/无效的值进去
                    # *() 只能再列表内部展开元素
                    *([{'range' : {'price' : price_filter }}] if price_filter else []),
                ]
            }
        },
        'from' : (page-1) * page_size,
        'size' : page_size,
    }
    # 如果 用户 要求排序，不要求排序 默认走_score 即关键字匹配分数
    if sort_body:
        body['sort'] = sort_body
    return body