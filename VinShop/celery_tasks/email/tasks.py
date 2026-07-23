from celery_tasks.main import app
from VinShop.settings import EMAIL_HOST_USER
from django.core.mail import send_mail
@app.task
def send_email(email,email_code):
    """
    send_mail
        · subject(必选)       ：邮件主题
        · message(必选)       ：邮件信息
        · from_email(必选)    ：发送邮件的地址
        · recipient_list(必选)：接收邮件的地址
        · html_message(可选)  ：邮件信息(html形式)
    """
    subject = 'VinShop 邮箱验证'
    message = f"您的邮箱验证码是{email_code}，请于5分钟内完成验证"
    from_email = EMAIL_HOST_USER
    recipient_list = [email]
    send_mail(subject, message, from_email, recipient_list)