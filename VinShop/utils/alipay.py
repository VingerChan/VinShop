from alipay import AliPay
from alipay.utils import AliPayConfig
from django.conf import settings
import logging
from django.utils import timezone

logger = logging.getLogger(__name__)

def get_alipay():
    # 初始化Alipay
    app_private_key_string = open(settings.APP_PRIVATE_KEY_PATH).read()
    alipay_public_key_string = open(settings.ALIPAY_PUBLIC_KEY_PATH).read()
    alipay = AliPay(
        appid=settings.ALIPAY_APP_ID,
        app_notify_url=None,  # 默认回调 url
        app_private_key_string=app_private_key_string,
        alipay_public_key_string=alipay_public_key_string,
        sign_type="RSA2",
        debug=True,
        verbose=False,  # 输出调试数据
        config=AliPayConfig(timeout=15)  # 可选，请求超时时间
    )
    return alipay

def refund_order(order,refund_amount):
    """
    调用支付宝退款接口 alipay.trade.refund
    :param order: 订单对象
    :param refund_amount: 退款金额
    :return: 支付宝返回的响应字典 {'code':'10000,......}
    """
    alipay = get_alipay()
    return alipay.server_api(
        'alipay.trade.refund',
        biz_content={
            'out_trade_no': order.order_id,
            'refund_amount': str(refund_amount),
            'out_request_no': order.order_id,
        },
    )

def handle_expired_payment(order,total_amount,trade_no):
    """

    :param order: 订单对象
    :param total_amount: 退款总金额
    :param trade_no: 支付宝交易订单号
    :return: True(已退款) / False(退款失败)
    """
    from apps.payment.models import Payment
    payment,_ = Payment.objects.update_or_create(
        order=order,
        defaults={
            'amount':total_amount,
            'trade_no':trade_no,
        }
    )
    # 如果订单已存在 并且已 退款
    if payment.is_refunded:
        return True
    try:    # 调用支付宝退款接口
        result = refund_order(order,total_amount)
    except Exception:
        logger.warning('退款接口调用异常 order = %s',order.order_id,exc_info=True)
        return False
    # 成功调用后，根据code检查是否调用成功
    if result.get('code') == '10000':
        payment.is_refunded = True
        payment.refund_time = timezone.now()
        payment.save(update_fields=['is_refunded','refund_time'])
        return True
    logger.warning('退款被支付宝拒绝 order = %s result = %s',order.order_id,result)
    return False