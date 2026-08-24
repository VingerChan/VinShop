<template>
  <div class="payment-page container">
    <div class="payment-card success" v-if="paid">
      <el-icon><SuccessFilled /></el-icon>
      <h2>支付成功</h2>
      <p>订单号：{{ orderId }}</p>
      <el-button type="primary" @click="$router.push('/orders/' + orderId)">查看订单详情</el-button>
    </div>
    <div class="payment-card" v-else-if="expired">
      <el-icon><WarningFilled /></el-icon>
      <h2>订单已超时</h2>
      <p>订单号：{{ orderId }}</p>
      <p class="expire-msg">支付时间已过期，订单已自动取消</p>
      <el-button type="primary" @click="$router.push('/orders')">返回我的订单</el-button>
    </div>
    <div class="payment-card" v-else>
      <h2>支付订单</h2>
      <div class="order-info">订单号：{{ orderId }}</div>
      <div class="pay-method-section">
        <h3>支付方式</h3>
        <el-radio-group v-model="payMethod">
          <el-radio :label="1">支付宝</el-radio>
        </el-radio-group>
      </div>
      <div class="countdown">请在 <span class="time">{{ formatTime(countdown) }}</span> 内完成支付</div>
      <div class="payment-actions">
        <el-button type="primary" size="large" :loading="paying" @click="handlePay">确认支付</el-button>
        <el-button @click="$router.push('/orders')">查看订单</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { SuccessFilled, WarningFilled } from '@element-plus/icons-vue'
import { getOrderDetail } from '../api/order'
import request from '../api/request'

const route = useRoute()
const router = useRouter()

const orderId = route.params.orderId
const payMethod = ref(1)
const paying = ref(false)
const paid = ref(false)
const expired = ref(false)
const countdown = ref(0)

let statusTimer = null
let countdownTimer = null

const formatTime = (s) => {
  const m = Math.floor(s / 60).toString().padStart(2, '0')
  const sec = (s % 60).toString().padStart(2, '0')
  return m + ':' + sec
}

const loadOrder = async () => {
  try {
    const res = await getOrderDetail(orderId)
    if (res.status !== 1) {
      paid.value = true
      return
    }
    const now = Math.floor(Date.now() / 1000)
    const remaining = res.expire_ts - now
    if (remaining <= 0) {
      expired.value = true
      return
    }
    countdown.value = remaining
  } catch {
    ElMessage.error('获取订单信息失败')
  }
}

const handlePay = async () => {
  paying.value = true
  try {
    const res = await request.get('/payment/alipay/', { params: { order_id: orderId } })
    const url = res.data.alipay_url
    if (url) {
      window.open(url, '_blank')
    } else {
      ElMessage.error('获取支付链接失败')
    }
  } catch {
    ElMessage.error('获取支付链接失败')
  } finally {
    paying.value = false
  }
}

const checkStatus = async () => {
  try {
    const res = await request.get('/payment/alipay/status/', { params: { order_id: orderId } })
    if (res.data.paid === true) {
      paid.value = true
      clearInterval(statusTimer)
    }
  } catch {
    // polling error
  }
}

onMounted(async () => {
  await loadOrder()
  if (!paid.value && !expired.value) {
    statusTimer = setInterval(checkStatus, 5000)
    countdownTimer = setInterval(() => {
      if (countdown.value > 0) {
        countdown.value--
      } else {
        expired.value = true
        clearInterval(countdownTimer)
        clearInterval(statusTimer)
      }
    }, 1000)
  }
})

onUnmounted(() => {
  clearInterval(statusTimer)
  clearInterval(countdownTimer)
})
</script>

<style scoped>
.payment-page {
  justify-content: center;
  padding: 60px 20px;
  display: flex;
}
.payment-card {
  text-align: center;
  background: #fff;
  border-radius: 12px;
  padding: 60px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}
.payment-card .el-icon {
  font-size: 64px;
}
h2 {
  margin: 20px 0 12px;
  font-size: 22px;
}
h3 {
  font-size: 16px;
  margin-bottom: 12px;
}
.order-info {
  color: #999;
  font-size: 14px;
}
.pay-method-section {
  margin: 24px 0;
  text-align: left;
  max-width: 300px;
  margin-left: auto;
  margin-right: auto;
}
.countdown {
  color: #666;
  margin: 20px 0;
  font-size: 16px;
}
.time {
  color: #e4393c;
  font-size: 20px;
  font-weight: 700;
}
.payment-actions {
  justify-content: center;
  gap: 16px;
  margin: 24px 0;
  display: flex;
}
.success p {
  color: #666;
  margin: 12px 0 24px;
}
.expire-msg {
  color: #999;
  margin: 12px 0 24px;
}
</style>
