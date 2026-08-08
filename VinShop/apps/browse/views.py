from datetime import datetime
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from utils import browse
from apps.goods.views import SKU
from apps.goods.serializers import SKUSerializer

class BrowseHistoryView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self,request):      # 获取浏览记录
        items = browse.recent(request.user.id)
        time_map = {sku_id:timestamp for sku_id,timestamp in items}
        sku_ids = list(time_map.keys())
        # 在数据库返回的顺序是不确定的 要重新按照sku_ids进行排序
        skus = {sku.id:sku for sku in SKU.objects.filter(pk__in=sku_ids,is_launched=True)}
        # 排序好的sku列表 [{sku1},{sku2}]
        browse_skus = [skus[i] for i in sku_ids if i in skus]
        # 按天分组
        group = {}
        # 获取当前时区 django settings
        time_zone = timezone.get_current_timezone()
        for sku in browse_skus:
            # 将每个 SKU 商品时间戳 转换为当前时区的 年月日
            # datetime包括时分秒 date只包括年月日
            day = datetime.fromtimestamp(time_map[sku.id],time_zone).date()
            group.setdefault(day,[]).append(sku)
        return Response([
            {'date':day,'skus':SKUSerializer(skus,many=True).data}
        for day,skus in group.items()])


