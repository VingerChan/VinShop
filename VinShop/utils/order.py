from django.utils import timezone
from django_redis import get_redis_connection

# 生成订单id编号
def generate_order_id(user_id):
    # 把 user.id格式化成 9 位数字，不足前面补 0
    return timezone.localtime().strftime("%Y%m%d%H%M%S%f")+"%09d"%user_id


"""
什么是上下文管理器：一个类只要实现了__enter__()和__exit__()这个两个方法
                通过该类创建的对象就称之为上下文管理器
                · __enter__表示上文方法,需要返回一个操作文件对象
                · __exit__表示下文方法,with语句执行完成会自动执行,即使出现异常也会执行该方法
"""
class OrderLockError(Exception):
    """抢不到 Redis 分布式锁时抛出的异常"""

class SKUOrderLock:
    _PREFIX = 'order_sku_lock'      # PREFIX前缀
    # 只需要指定传参sku_ids
    def __init__(self, sku_ids, timeout=30, blocking_timeout=5):
        self.sku_ids = sorted(set(sku_ids))  # set去重无序 sorted排序
        self.timeout = timeout  # 锁的TTL
        self.blocking_timeout = blocking_timeout  # 抢锁最长等多久
        self.conn = get_redis_connection('default')
        self._locks = []  # 已拿到手的锁，退出时统一归还

    def __enter__(self):
        try:
            for sku_id in self.sku_ids:
                # conn.lock()创建一把锁
                lock = self.conn.lock(
                    f"{self._PREFIX}:{sku_id}",
                    timeout=self.timeout,
                    blocking=True,
                    blocking_timeout=self.blocking_timeout
                )
                # 加锁，超时没枪到锁 返回False
                if not lock.acquire():
                    raise OrderLockError(f"获取商品{sku_id}锁超时，系统繁忙")
                self._locks.append(lock)
        except OrderLockError:
            # 在sku_ids中 一旦某把sku_id的锁获取失败 需要全部还锁
            self._release_all()
            # 先还锁，再把这个异常原样抛除去
            raise
        return self

    # __exit__的返回值：决定with块体里抛出的异常要不要被吞掉
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._release_all()
        return False

    def _release_all(self):
        for lock in reversed(self._locks):
            try:
                lock.release()
            except Exception:
                pass
            self._locks=[]