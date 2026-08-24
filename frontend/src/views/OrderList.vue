<template>
  <div class="order-list-page container">
    <h2 class="page-title">我的订单</h2>
    <el-tabs v-model="activeStatus" @tab-change="loadOrders">
      <el-tab-pane label="全部" name="all" />
      <el-tab-pane label="待付款" name="1" />
      <el-tab-pane label="待发货" name="2" />
      <el-tab-pane label="待收货" name="3" />
      <el-tab-pane label="待评价" name="4" />
      <el-tab-pane label="已完成" name="5" />
      <el-tab-pane label="已取消" name="6" />
    </el-tabs>

    <template v-if="orders.length">
      <div class="order-card" v-for="order in orders" :key="order.order_id">
        <div class="order-header">
          <span class="order-id">订单号：{{ order.order_id }}</span>
          <span class="order-status" :class="'status-' + order.status">{{ statusMap[order.status] }}</span>
        </div>
        <div class="order-goods" @click="$router.push('/orders/' + order.order_id)">
          <div class="order-item" v-for="sku in order.skus" :key="sku.sku_id">
            <img class="item-thumb" :src="sku.default_image_url || '/placeholder.png'" @error="onImgError" />
            <div class="item-info">
              <div class="item-name">{{ sku.sku_name }}</div>
            </div>
            <div class="item-price">¥{{ sku.price }}</div>
            <div class="item-count">×{{ sku.count }}</div>
          </div>
        </div>
        <div class="order-footer">
          <span>共{{ order.total_count }}件商品</span>
          <span>合计：<span class="price">¥{{ order.total_amount }}</span></span>
          <el-button v-if="order.status === 1" type="primary" @click.stop="goPay(order.order_id)">去支付</el-button>
          <el-button v-if="order.status === 3" type="warning" @click.stop="handleConfirm(order.order_id)">确认收货</el-button>
          <el-button v-if="order.status === 4" type="info" plain @click.stop="goComment(order)">去评价</el-button>
        </div>
      </div>
    </template>

    <el-empty v-else description="暂无订单" />

    <el-pagination
      v-if="total > pageSize"
      class="pagination"
      layout="prev, pager, next"
      :total="total"
      :page-size="pageSize"
      v-model:current-page="currentPage"
      @current-change="loadOrders"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getOrders, confirmReceipt } from '../api/order'

const router = useRouter()

const activeStatus = ref('all')
const orders = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)

const statusMap = {
  1: '待付款',
  2: '待发货',
  3: '待收货',
  4: '待评价',
  5: '已完成',
  6: '已取消'
}

const loadOrders = async () => {
  const params = {
    page: currentPage.value,
    page_size: pageSize.value
  }
  if (activeStatus.value !== 'all') {
    params.status = activeStatus.value
  }
  const res = await getOrders(params)
  orders.value = res.orders || []
  total.value = res.total || 0
}

const goPay = (id) => {
  router.push('/payment/' + id)
}

const handleConfirm = async (orderId) => {
  try {
    await ElMessageBox.confirm('确认已收到商品？', '确认收货', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      type: 'warning'
    })
  } catch {
    return
  }
  try {
    await confirmReceipt(orderId)
    ElMessage.success('确认收货成功')
    loadOrders()
  } catch {
    // axios 拦截器已处理错误提示
  }
}

const goComment = (order) => {
  const uncommented = order.skus.find(s => !s.is_commented)
  if (uncommented) {
    router.push(`/comment/${order.order_id}/${uncommented.id}`)
  }
}

onMounted(() => {
  loadOrders()
})
</script>

<style scoped>
.order-list-page {
  padding: 20px;
}
.page-title {
  margin-bottom: 20px;
  font-size: 22px;
}
.order-card {
  background: #fff;
  border-radius: 8px;
  margin-bottom: 16px;
}
.order-header {
  background: #fafafa;
  border-bottom: 1px solid #f0f0f0;
  justify-content: space-between;
  padding: 12px 20px;
  display: flex;
}
.order-id {
  color: #999;
  font-size: 13px;
}
.order-status {
  font-weight: 700;
}
.status-1 {
  color: #409eff;
}
.status-2 {
  color: #67c23a;
}
.status-3 {
  color: #e6a23c;
}
.status-4 {
  color: #909399;
}
.status-5 {
  color: #67c23a;
}
.status-6 {
  color: #999;
}
.order-goods {
  cursor: pointer;
  padding: 16px 20px;
}
.order-item {
  align-items: center;
  gap: 12px;
  padding: 8px 0;
  display: flex;
  border-bottom: 1px solid #f8f8f8;
}
.item-thumb {
  width: 60px;
  height: 60px;
  object-fit: cover;
}
.item-info {
  flex: 1;
}
.item-name {
  color: #333;
}
.item-price {
  color: #333;
}
.item-count {
  color: #999;
}
.order-footer {
  border-top: 1px solid #f0f0f0;
  justify-content: flex-end;
  align-items: center;
  gap: 20px;
  padding: 12px 20px;
  display: flex;
}
.price {
  color: #e4393c;
  font-weight: 700;
}
.pagination {
  justify-content: center;
  padding: 20px 0;
  display: flex;
}
</style>
