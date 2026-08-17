from decimal import Decimal
from alipay import AliPayException, AliPayValidationError
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import render
from django.conf import settings
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from utils.alipay import get_alipay
from apps.orders.models import OrderInfo
from apps.payment.models import Payment

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
                'total_amount': str(order.total_amount + order.freight),
                'subject': f'VinShop{order_id}',
                # product_code:告诉支付宝 这笔交易是用哪种交易场景
                'product_code': 'FAST_INSTANT_TRADE_PAY',    # 电脑网站支付
                # QUICK_WAP_PAY：手机网站支付  FACE_TO_FACE_PAYMENT：当面付(扫码枪/二维码)
            },
            return_url=settings.ALIPAY_RETURN_URL,
            notify_url=settings.ALIPAY_NOTIFY_URL,
        )
        alipay_url = settings.ALIPAY_URL + '?' + order_string
        return Response({'alipay_url':alipay_url})

# 服务端向支付宝 查询交易状态
class AlipayQueryView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        order_id = request.query_params.get('order_id','')
        user = request.user
        # 校验订单号是否存在 是否属于当前用户
        try:
            order = OrderInfo.objects.get(user=user,order_id=order_id)
        except OrderInfo.DoesNotExist:
            return Response({'message':'订单不存在'},status=status.HTTP_400_BAD_REQUEST)
        alipay = get_alipay()
        try:
            result = alipay.server_api(
                "alipay.trade.query",
                biz_content={
                    'out_trade_no': order.order_id,
                }
            )
        except (AliPayException,AliPayValidationError):    # 交易不存在/验签失败
            return Response({'paid':False,'trade_status':None})
        trade_status = result.get('trade_status')
        # 交易状态
        if trade_status in ('TRADE_SUCCESS','TRADE_FINISHED'):
            with transaction.atomic():
                order = OrderInfo.objects.select_for_update().get(order_id=order_id,user=user)
                if order.status == OrderInfo.STATUS_ENUM['UNPAID']:
                    Payment.objects.update_or_create(
                        order=order,    # 查询条件
                        defaults = {
                            'amount' : Decimal(result.get('total_amount')),
                            'trade_no' : result.get('trade_no'),
                        }
                    )
                    order.status = OrderInfo.STATUS_ENUM['UNSEND']
                    order.save(update_fields=['status'])
            return Response({'paid':True,'trade_no':result.get('trade_no')})
        # 如果交易失败
        return Response({'paid':False,'trade_status':trade_status})

# 支付宝异步通知
class AlipayNotifyView(APIView):
    @transaction.atomic
    def post(self,request):
        alipay = get_alipay()
        data = request.POST.dict()
        # 验证签名
        signature = data.pop("sign")
        if not signature:
            return HttpResponse('fail')
        success = alipay.verify(data,signature)
        if not success:
            return HttpResponse('fail')
        if data.get('app_id') != settings.ALIPAY_APP_ID:
            return HttpResponse('fail')
        if data.get('trade_status') not in ('TRADE_SUCCESS','TRADE_FINISHED'):
            # 返回success 防止支付宝无限重发
            return HttpResponse('success')
        out_trade_no = data['out_trade_no']
        total_amount = Decimal(data['total_amount'])
        alipay_trade_no = data['trade_no']
        try:
            order = OrderInfo.objects.select_for_update().get(order_id=out_trade_no)
        except OrderInfo.DoesNotExist:
            return HttpResponse('fail')
        # 校验金额
        if total_amount != order.total_amount + order.freight:
            return HttpResponse('fail')
        # 校验订单的状态
        if order.status == OrderInfo.STATUS_ENUM['UNPAID']:
            Payment.objects.update_or_create(
                order=order, defaults = {
                    'amount': total_amount,
                    'trade_no': alipay_trade_no,
                }
            )
            order.status = OrderInfo.STATUS_ENUM['UNSEND']
            order.save(update_fields=['status'])
        # 必须返回纯文本 success才能防止重发
        return HttpResponse('success')
