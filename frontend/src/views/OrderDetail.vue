<template>
  <div class="order-detail-page container" v-if="data">
    <div class="detail-card">
      <div class="card-header">
        <h2>订单详情</h2>
        <span class="order-status" :class="'status-' + data.status">{{ statusMap[data.status] }}</span>
      </div>
      <div class="info-grid">
        <div class="info-item">
          <span class="label">订单号：</span>
          <span>{{ data.order_id }}</span>
        </div>
        <div class="info-item">
          <span class="label">创建时间：</span>
          <span>{{ formatTime(data.create_time) }}</span>
        </div>
        <div class="info-item">
          <span class="label">支付时间：</span>
          <span>{{ formatTime(data.pay_time) || '未支付' }}</span>
        </div>
        <div class="info-item">
          <span class="label">支付方式：</span>
          <span>{{ data.pay_method_text }}</span>
        </div>
        <div class="info-item">
          <span class="label">收货人：</span>
          <span>{{ data.receiver_name }} {{ data.receiver_mobile }}</span>
        </div>
        <div class="info-item">
          <span class="label">收货地址：</span>
          <span>{{ data.receiver_address }}</span>
        </div>
      </div>

      <el-divider />

      <h3>商品清单</h3>
      <el-table :data="data.skus" border style="width: 100%">
        <el-table-column label="商品" min-width="300">
          <template #default="{ row }">
            <div class="detail-goods" @click="$router.push('/detail/' + row.sku_id)">
              <img class="goods-thumb" :src="row.default_image_url || '/placeholder.png'" />
              <div>
                <div class="item-name">{{ row.sku_name }}</div>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="单价" width="120">
          <template #default="{ row }">{{ row.price }}</template>
        </el-table-column>
        <el-table-column label="数量" width="100" prop="count" />
        <el-table-column label="小计" width="120">
          <template #default="{ row }">{{ (row.price * row.count).toFixed(2) }}</template>
        </el-table-column>
        <el-table-column v-if="data.status === 4" label="操作" width="120">
          <template #default="{ row }">
            <el-button v-if="!row.is_commented" type="primary" link @click="goComment(row)">去评价</el-button>
            <span v-else class="commented-tag">已评价</span>
          </template>
        </el-table-column>
      </el-table>

      <div class="amount-summary">
        <div>商品总额：<span>{{ data.total_amount }}</span></div>
        <div>运费：<span>{{ data.freight || 0 }}</span></div>
        <div class="final">实付金额：<span class="final-price">{{ data.final_amount || data.total_amount }}</span></div>
      </div>

      <div class="action-bar" v-if="data.status === 1 || data.status === 3">
        <template v-if="data.status === 1">
          <span v-if="countdown > 0" class="pay-countdown">剩余支付时间：<span class="time">{{ formatCountdown(countdown) }}</span></span>
          <el-button type="primary" @click="$router.push('/payment/' + data.order_id)">去支付</el-button>
        </template>
        <template v-if="data.status === 3">
          <el-button type="warning" @click="handleConfirm">确认收货</el-button>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getOrderDetail, confirmReceipt } from '../api/order'

const route = useRoute()
const router = useRouter()

const data = ref(null)
const countdown = ref(0)
let countdownTimer = null

const statusMap = {
  1: '待付款',
  2: '待发货',
  3: '待收货',
  4: '待评价',
  5: '已完成',
  6: '已取消'
}

const formatTime = (t) => {
  if (!t) return ''
  const d = new Date(t)
  const utc8 = new Date(d.getTime() + 8 * 60 * 60 * 1000)
  const y = utc8.getUTCFullYear()
  const m = String(utc8.getUTCMonth() + 1).padStart(2, '0')
  const day = String(utc8.getUTCDate()).padStart(2, '0')
  const h = String(utc8.getUTCHours()).padStart(2, '0')
  const min = String(utc8.getUTCMinutes()).padStart(2, '0')
  const s = String(utc8.getUTCSeconds()).padStart(2, '0')
  return `${y}-${m}-${day} ${h}:${min}:${s}`
}

const formatCountdown = (s) => {
  const m = Math.floor(s / 60).toString().padStart(2, '0')
  const sec = (s % 60).toString().padStart(2, '0')
  return m + ':' + sec
}

const handleConfirm = async () => {
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
    await confirmReceipt(data.value.order_id)
    ElMessage.success('确认收货成功')
    data.value.status = 4
  } catch {
    // axios 拦截器已处理错误提示
  }
}

const goComment = (sku) => {
  router.push(`/comment/${data.value.order_id}/${sku.id}`)
}

onMounted(async () => {
  const res = await getOrderDetail(route.params.id)
  data.value = res
  if (res.status === 1 && res.expire_ts) {
    const now = Math.floor(Date.now() / 1000)
    const remaining = res.expire_ts - now
    if (remaining > 0) {
      countdown.value = remaining
      countdownTimer = setInterval(() => {
        if (countdown.value > 0) {
          countdown.value--
        } else {
          clearInterval(countdownTimer)
        }
      }, 1000)
    }
  }
})

onUnmounted(() => {
  clearInterval(countdownTimer)
})
</script>

<style scoped>
.order-detail-page {
  padding: 20px;
}
.detail-card {
  background: #fff;
  border-radius: 8px;
  padding: 30px;
}
.card-header {
  justify-content: space-between;
  align-items: center;
  display: flex;
}
.card-header .order-status {
  font-weight: 700;
}
.status-1 { color: #409eff; }
.status-2 { color: #67c23a; }
.status-3 { color: #e6a23c; }
.status-4 { color: #909399; }
.status-5 { color: #67c23a; }
.status-6 { color: #999; }
.info-grid {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.info-item .label {
  color: #999;
  margin-right: 12px;
}
.detail-goods {
  align-items: center;
  gap: 10px;
  display: flex;
  cursor: pointer;
}
.goods-thumb {
  width: 60px;
  height: 60px;
  object-fit: cover;
  border-radius: 4px;
}
.amount-summary {
  text-align: right;
  color: #666;
  margin-top: 16px;
}
.amount-summary .final {
  color: #333;
  font-size: 16px;
  margin-top: 8px;
}
.final-price {
  font-size: 24px;
  color: #e4393c;
  font-weight: 700;
}
.action-bar {
  justify-content: flex-end;
  align-items: center;
  gap: 20px;
  margin-top: 20px;
  display: flex;
}
.pay-countdown {
  color: #666;
  font-size: 14px;
}
.pay-countdown .time {
  color: #e4393c;
  font-weight: 700;
}
.commented-tag {
  color: #909399;
  font-size: 13px;
}
</style>
