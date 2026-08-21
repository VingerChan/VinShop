from celery.schedules import crontab

# 指定RabbitMQ为消息队列
broker_url = 'amqp://127.0.0.1:5672//'
"""
· beat_schedule:Celery Beat读取的一个特殊字典配置,每个键是一个任务名称(可自定义),值告诉Beat执行哪
               一个任务，多久执行一次
· task:任务的全限定名。Celery 根据这个字符串去任务注册表中查找函数。格式必须是 包路径.文件名.函数名，要
       和你在Worker中注册的名称一致
· schedule:时间间隔（秒）。300.0 = 300秒 = 5分钟。Celery Beat 内部通过一个定时器循环来检查当前时间，每过 300 秒就往Broker(Redis)发送一条执行该任务的消息
· args:()   传递给任务函数的参数,因为是空元组,所以调用时就是 generate_static_index_html()
"""
beat_schedule = {
    'check_expired_orders':{
        'task' : 'celery_tasks.order.tasks.check_expired_orders',
        'schedule' : crontab(minute='*'),    # 每分钟第0秒执行一次
    },
    'clean_comment_file':{
        'task' : 'celery_tasks.comments.tasks.clean_comment_file',
        'schedule' : crontab(hour=3,minute=30),    #每天凌晨3:30执行一次
    }
}
timezone = 'Asia/Shanghai'