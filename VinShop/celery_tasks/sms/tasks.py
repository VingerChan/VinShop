from VinShop.settings import RONGLIAN_ACC_ID,RONGLIAN_ACC_TOKEN,RONGLIAN_APP_ID,RONGLIAN_SMS_TEMPLATE_ID
from celery_tasks.main import app
from ronglian_sms_sdk import SmsSDK
# app.task = *告诉 Celery："这个函数我注册成可异步执行的任务了，以后通过 name 来找我执行"*。没有它，Celery Worker 拿到消息也不知道该执行哪个函数
@app.task   # 等价于app.task(send_sms_code)
def send_sms_code(mobile,sms_code):
    sdk = SmsSDK(RONGLIAN_ACC_ID,RONGLIAN_ACC_TOKEN,RONGLIAN_APP_ID)
    # datas是一个元组，意思是请于5分钟内正确输入
    sdk.sendMessage(RONGLIAN_SMS_TEMPLATE_ID,mobile,(sms_code,5))