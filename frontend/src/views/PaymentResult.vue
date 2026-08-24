<template>
  <div class="container" style="text-align:center; padding: 60px;">
    <el-icon><Loading /></el-icon>
    <h2>正在跳转到订单详情...</h2>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Loading } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()

onMounted(() => {
  const orderId = route.query.order_id
  if (orderId) {
    router.replace('/orders/' + orderId)
  } else {
    router.replace('/orders')
  }
})
</script>
