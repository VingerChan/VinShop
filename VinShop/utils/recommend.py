from VinShop.settings import POPULAR_LIMIT
from apps.goods.models import SKU
def get_popular_skus():
    skus = SKU.objects.filter(is_launched=True).order_by('-sales','-comments')[:POPULAR_LIMIT]
    return skus
