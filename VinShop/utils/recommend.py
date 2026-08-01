from VinShop.settings import POPULAR_LIMIT,POPULAR_POOL
from apps.goods.models import SKU
import random
def get_popular_skus():
    pool = list(SKU.objects.filter(is_launched=True).order_by('-sales','-comments')[:POPULAR_POOL])
    return random.sample(pool,min(POPULAR_LIMIT,len(pool)))
