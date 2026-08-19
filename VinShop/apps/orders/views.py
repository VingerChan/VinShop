import logging
from decimal import Decimal
from django.conf import settings
from django.db import transaction
from django.db.models import F,Prefetch
from django_redis import get_redis_connection
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from apps.orders.models import OrderInfo,OrderGoods
from apps.goods.models import SKU
from apps.users.models import Address
from apps.users.serializers import AddressSerializer
from utils import carts
from utils.order import SKUOrderLock, generate_order_id, OrderLockError, add_order_expire
from apps.orders.serializers import SettlementQuerySerializer,OrderSettlementSKUSerializer,OrderCommitSerializer,OrderInfoSerializer
from django.utils import timezone
from celery_tasks.order.tasks import cancel_timeout_order

# __name__是模块全路径apps.orders.views
logger = logging.getLogger(__name__)
# 获取订单结算页面
# 收获地址、商品清单、金额汇总、支付方式
class OrderSettlementView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self,request):
        user = request.user
        qs = SettlementQuerySerializer(data=request.query_params)
        qs.is_valid(raise_exception=True)
        params = qs.validated_data
        if params:
            cart = {params['sku_id']:params['count']}
            selected_ids = {params['sku_id']}
        else:
            # 获取购物车商品 以及 选中的sku_id
            cart = carts.get_all(user.id)
            selected_ids = carts.get_selected(user.id)
        # 每个地址各查 province / city / district
        # 使用select_related变成1次JOIN查完
        addresses = user.address.all().select_related('province','city','district')
        result = {
            'default_address' : user.default_address_id,
            'addresses' : AddressSerializer(addresses,many=True).data,
            'skus' : [],
            'invalid_skus' : [],
            'freight' : Decimal('0.00'),
            'total_count' : 0,
            'total_amount' : Decimal('0.00'),
            'final_amount' : Decimal('0.00'),
            'pay_methods' : [{'id':value,'name':name} for value,name in OrderInfo.PAY_METHODS_CHOICES],
        }
        # 如果购物车中没有选取任何SKU
        if not selected_ids:
            return Response(result)

        # 提前触发查询，避免重复查数据库
        skus = list(SKU.objects.filter(id__in=selected_ids))
        valid_skus = []             # 上架并且在购物车中的商品
        invalid_skus = []           # 下架并且在购物车中的商品
        # 根据sku 分出需要展示的sku 和 因错误而软提示的sku
        for sku in skus:
            count = cart[sku.id]
            if not sku.is_launched:
                invalid_skus.append({'id':sku.id,'name':sku.name,'reason':'商品已下架'})
            elif count > sku.stock:
                invalid_skus.append({'id':sku.id,'name':sku.name,'reason':'库存不足，请调整数量'})
            else:
                valid_skus.append(sku)
        # 查找不存在的商品id  A - B 表示 集合差集
        not_found_ids = selected_ids - {sku.id for sku in skus}
        invalid_skus.extend({'id':sku_id,'name':'商品不存在','reason':'商品不存在'}for sku_id in sorted(not_found_ids))
        result['invalid_skus'] = invalid_skus

        # 如果没有有效商品，结算页照常打开
        if not valid_skus:
            return Response(result)
        total_count = 0
        total_amount = Decimal('0.00')
        for sku in valid_skus:
            count = cart[sku.id]
            total_count += count
            total_amount += sku.price * count
        # 计算运费
        freight = Decimal('0.00') if total_amount >= settings.FREE_FREIGHT_LIMIT else settings.FREIGHT
        result.update({
            'skus' : OrderSettlementSKUSerializer(valid_skus,many=True,context={'counts':cart}).data,
            'freight' : freight,
            'total_count' : total_count,
            'total_amount' : total_amount,
            'final_amount' : total_amount + freight,
        })
        return Response(result)

class OrderStockError(Exception):
    """业务性失败（下架 / 库存不足）"""

class OrderCommitView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self,request):
        serializer = OrderCommitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data      # 获取校验后的反序列化数据
        user = request.user
        # 1.幂等键(Idempotency（幂等性）)：防止“同一笔交两次”
        conn = get_redis_connection('orders')
        idem_key = f"order_idem:{user.id}:{data['client_token']}"
        ok = conn.set(idem_key,'1',nx=True,ex=60)
        if not ok:
            return Response({'message':'订单提交过于频繁，请勿重复提交'},status=status.HTTP_409_CONFLICT)
        # 2.校验前端传的Address_id是否属于该用户的
        try:
            address = Address.objects.select_related('province','city','district').get(pk=data['address_id'],user=user)
        except Address.DoesNotExist:
            return Response({'message':'收货地址不存在'},status=status.HTTP_400_BAD_REQUEST)
        # 3. 组装购买清单
        if 'skus' in data:      # 购物车结算
            cart = {item['sku_id']:{'count':item['count'],'note':item.get('note','')} for item in data['skus']}
        else:                   # 立即购买结算
            cart = {data['sku_id']: {'count':data['count'],'note':data['note']}}
        goods_list = []
        try:
            with transaction.atomic():  # 事务：扣库存 建单 清购物车，失败则回滚
                with SKUOrderLock(cart.keys()):  # Redis分布式锁：互斥同一批商品
                    skus = list(SKU.objects.filter(id__in=cart.keys()))
                    if {sku.id for sku in skus} != set(cart.keys()):    # 去重集合
                        raise OrderStockError('部分商品不存在，请返回结算页')
                    for sku in skus:
                        if not sku.is_launched:
                            raise OrderStockError(f"{sku.name} 已下架")
                    total_count = 0
                    total_amount = Decimal('0.00')
                    # 4.扣减库存，乐观锁：条件更新+原子自增减
                    for sku in skus:
                        sku_info = cart[sku.id]
                        count = sku_info['count']
                        note = sku_info['note']
                        # 先查库存量是否大于 购物车 所需要的数量，再进行更新
                        result = SKU.objects.filter(pk=sku.id,stock__gte=count).update(stock=F('stock')-count,sales=F('sales')+count)
                        if result == 0:
                            raise OrderStockError(f"{sku.name} 库存不足")
                        goods_list.append((sku,count,note))
                        total_count += count
                        total_amount += sku.price * count
                    # 根据total_amount计算运费
                    freight = Decimal('0.00') if total_amount >= settings.FREE_FREIGHT_LIMIT else settings.FREIGHT
                    # 创建订单
                    order = OrderInfo.objects.create(
                        order_id = generate_order_id(user.id),
                        user = user,
                        address = address,
                        receiver_name = address.receiver_name,
                        receiver_mobile = address.mobile,
                        receiver_address = f"{address.province.name}{address.city.name}{address.district.name}{address.place}",
                        total_count = total_count,
                        total_amount = total_amount,
                        freight = freight,
                        pay_method = data['pay_method'],
                        status = OrderInfo.STATUS_ENUM['UNPAID']
                    )
                    # 根据order批量创建OrderGoods
                    OrderGoods.objects.bulk_create([
                        OrderGoods(order=order,sku=sku,count=count,price=sku.price,note=note) for sku,count,note in goods_list
                    ])
        except OrderStockError as e:    # 业务失败
            conn.delete(idem_key)
            return Response({'message':str(e)},status=status.HTTP_409_CONFLICT)
        except OrderLockError as e:    # 抢锁超时
            conn.delete(idem_key)
            return Response({'message':str(e)},status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception:
            conn.delete(idem_key)
            raise
        if 'sku_id' not in data:    # 购物车结算 --> 清空购物车
            try:
                carts.consume_cart(user.id,{sku_id:sku_info['count'] for sku_id,sku_info in cart.items()})
            except Exception as e:
                logger.warning("订单 %s 提交成功但清理购物车失败: %s", order.order_id, e, exc_info=True)
        # 订单创建成功后,注册"30分钟自动取消"
        try:
            # 截止订单时间戳 将create_time转换为时间戳并相加
            expire_ts = int(order.create_time.timestamp()) + settings.ORDER_PAY_TIMEOUT
            # 将订单信息 放入ZSET：倒计时 取消订单
            add_order_expire(order.order_id,expire_ts)
            # apply_async生成消息{"task":"","args":[order_id],"eta":截止时间}
            # celery生成一个任务，在截止时间一到就执行这个任务
            cancel_timeout_order.apply_async(
                args=[order.order_id,expire_ts],
                countdown=settings.ORDER_PAY_TIMEOUT,
            )
        except Exception as e:
            logger.warning("订单 %s 自动取消调度失败：%s",order.order_id, e, exc_info=True)
            expire_ts = int(timezone.now().timestamp()) + settings.ORDER_PAY_TIMEOUT
        return Response({
            'order_id':order.order_id,
            'total_amount':order.total_amount,
            'freight':order.freight,
            'final_amount':order.total_amount +  order.freight,
            'expire_ts':expire_ts,
        },status=status.HTTP_201_CREATED)

class OrderCenterView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self,request):
        user = request.user
        # 分页
        try:
            page = int(request.query_params.get('page',1))
            page = min(max(page,1),1000)    # 下限1,上限1000
            page_size = int(request.query_params.get('page_size',5))
            page_size = min(max(page_size,1),50)        # 下限1,上限50
        except ValueError:
            return Response({'message':'page/page_size必须是正整数'},status=status.HTTP_400_BAD_REQUEST)
        # 获取当前用户订单
        orders = OrderInfo.objects.filter(user=user)
        # 状态筛选
        raw_status = request.query_params.get('status')
        if raw_status is not None:
            try:
                status_value = int(raw_status)
            except ValueError:
                return Response({'message':'status必须是整数'},status=status.HTTP_400_BAD_REQUEST)
            if status_value not in OrderInfo.STATUS_ENUM.values():
                return Response({'message':'不支持的订单状态'},status=status.HTTP_400_BAD_REQUEST)
            orders = orders.filter(status=status_value)
        # 排序
        orders = orders.order_by('-create_time').prefetch_related(
            Prefetch('skus',queryset=OrderGoods.objects.select_related('sku'))
        )
        # 分页 切片[start : end]
        order_count = orders.count()
        page_orders = orders[(page-1)*page_size:page*page_size]
        serializer = OrderInfoSerializer(page_orders,many=True)
        return Response({
            'total':order_count,'page':page,'page_size':page_size,'orders':serializer.data
        })

class OrderDetailView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self,request,order_id):
        user = request.user
        try:
            order = OrderInfo.objects.filter(user=user).prefetch_related(
                Prefetch(
                    'skus',
                    queryset=OrderGoods.objects.select_related('sku')
                )
            ).get(order_id=order_id)
        except OrderInfo.DoesNotExist:
            return Response({'message':'订单不存在'},status=status.HTTP_404_NOT_FOUND)
        return Response(OrderInfoSerializer(order).data)