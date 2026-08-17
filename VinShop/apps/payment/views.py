from django.shortcuts import render
from django.conf import settings
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from utils.alipay import get_alipay
from apps.orders.models import OrderInfo

class AlipayURLView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        order_id = request.query_params.get('order_id','')
        user = request.user
        # 校验订单是否存在 订单是否属于当前用户
        try:
            order = OrderInfo.objects.get(user=user,order_id=order_id)
        except OrderInfo.DoesNotExist:
            return Response({'message':'订单不存在'},status=status.HTTP_400_BAD_REQUEST)
        if order.status != OrderInfo.STATUS_ENUM['UNPAID']:
            return Response({'message':'订单当前状态不可支付'},status=status.HTTP_400_BAD_REQUEST)
        alipay = get_alipay()
        order_string = alipay.client_api(
            "alipay.trade.page.pay",
            biz_content={
                'out_trade_no': order.order_id,
                'total_amount': str(order.total_amount),
                'subject': f'VinShop{order_id}',
                # product_code:告诉支付宝 这笔交易是用哪种交易场景
                'product_code': 'FAST_INSTANT_TRADE_PAY',    # 电脑网站支付
                # QUICK_WAP_PAY：手机网站支付  FACE_TO_FACE_PAYMENT：当面付(扫码枪/二维码)
            },
            return_url=settings.ALIPAY_RETURN_URL,
        )
        alipay_url = settings.ALIPAY_URL + '?' + order_string
        return Response({'alipay_url':alipay_url})
