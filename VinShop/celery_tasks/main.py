# main.py
# 1.为celery运行提供Django环境(可以直接照抄manage.py)
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VinShop.settings')
# 2.创建celery实例
from celery import Celery
"""
在 Celery 中，Celery(main=...)里的 main参数，本质上是这个 Celery 应用的“名字”，主要用于：
日志、任务名、监控界面（Flower）、结果后端里标识应用
自动生成任务名（尤其是你不显式指定 name时）
防止多个 Celery app 冲突
"""# Celery的参数1(main)设置成脚本路径就可以了,因为脚本路径是唯一的
app = Celery('celery_tasks')

# 3.设置broker，通过加载配置文件来设置broker
app.config_from_object('celery_tasks.config')

# 4.Celery自动检测指定包的任务
app.autodiscover_tasks(['celery_tasks.sms.tasks','celery_tasks.email.tasks','celery_tasks.search.tasks','celery_tasks.order.tasks','celery_tasks.comments.tasks'])