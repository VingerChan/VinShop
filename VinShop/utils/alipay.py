from alipay import AliPay
from alipay.utils import AliPayConfig
from django.conf import settings
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