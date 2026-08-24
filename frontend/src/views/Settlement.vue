<template>
  <div class="settlement-page container">
    <h2 class="page-title">确认订单</h2>
    <template v-if="K">
      <div class="section address-section">
        <h3>收货地址</h3>
        <template v-if="K.addresses && K.addresses.length">
          <div class="address-list">
            <div
              v-for="addr in K.addresses"
              :key="addr.id"
              class="address-card"
              :class="{ active: q === addr.id }"
              @click="q = addr.id"
            >
              <div class="addr-info">
                <span class="addr-name">{{ addr.receiver_name }}</span>
                <span class="addr-mobile">{{ addr.mobile }}</span>
                <el-tag v-if="addr.is_default" type="danger" size="small">默认</el-tag>
              </div>
              <div class="addr-detail">{{ addr.province }}{{ addr.city }}{{ addr.district }}{{ addr.place }}</div>
            </div>
          </div>
        </template>
        <el-empty v-else description="暂无收货地址">
          <el-button type="primary" @click="$router.push('/user')">添加地址</el-button>
        </el-empty>
      </div>

      <div class="section goods-section">
        <h3>商品清单</h3>
        <el-table :data="K.skus" style="width: 100%">
          <el-table-column label="商品" min-width="300">
            <template #default="{ row }">
              <div class="settle-goods">
                <img
                  :src="imageUrl(row.default_image_url)"
                  class="goods-thumb goods-link"
                  @click="router.push('/detail/' + row.id)"
                />
                <span class="goods-name-link" @click="router.push('/detail/' + row.id)">{{ row.name }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="单价" width="120">
            <template #default="{ row }">
              <span>¥{{ row.price }}</span>
            </template>
          </el-table-column>
          <el-table-column label="数量" width="160">
            <template #default="{ row }">
              <el-input-number
                v-model="row.count"
                :min="1"
                :max="row.stock"
                size="small"
                @change="handleCountChange(row)"
              />
            </template>
          </el-table-column>
          <el-table-column label="小计" width="120">
            <template #default="{ row }">
              <span>¥{{ (row.price * row.count).toFixed(2) }}</span>
            </template>
          </el-table-column>
        </el-table>
        <template v-if="K.invalid_skus && K.invalid_skus.length">
          <el-alert
            v-for="item in K.invalid_skus"
            :key="item.id"
            :title="item.name + '：' + item.reason"
            type="warning"
            :closable="false"
            show-icon
            style="margin-top: 12px;"
          />
        </template>
      </div>

      <div class="section pay-section">
        <h3>支付方式</h3>
        <el-radio-group v-model="J">
          <el-radio :label="1">支付宝</el-radio>
        </el-radio-group>
      </div>

      <div class="settlement-bar">
        <div class="summary">
          <p>商品合计：¥{{ K.total_amount }}</p>
          <p>运费：¥{{ K.freight }}</p>
          <p class="final">应付总额：<span class="final-price">¥{{ K.final_amount }}</span></p>
        </div>
        <el-button type="danger" size="large" :loading="Y" @click="submitOrder">提交订单</el-button>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getSettlement, commitOrder } from '../api/order'
import { useCartStore } from '../stores/cart'

const route = useRoute()
const router = useRouter()
const cartStore = useCartStore()

const K = ref(null)
const q = ref(null)
const J = ref(1)
const Y = ref(false)

const loadSettlement = async () => {
  try {
    const params = {}
    if (route.query.cart_ids) params.cart_ids = route.query.cart_ids
    if (route.query.sku_id) params.sku_id = route.query.sku_id
    if (route.query.count) params.count = route.query.count
    K.value = await getSettlement(params)
    if (K.value.default_address) {
      q.value = K.value.default_address
    } else if (K.value.addresses && K.value.addresses.length) {
      q.value = K.value.addresses[0].id
    }
  } catch {
    // error handled by interceptor
  }
}

const imageUrl = (url) => {
  return url || 'https://via.placeholder.com/60x60?text=商品'
}

const handleCountChange = (row) => {
  row.amount = row.price * row.count
  let total = 0
  K.value.skus.forEach(s => { total += s.price * s.count })
  K.value.total_amount = total.toFixed(2)
  K.value.final_amount = (total + Number(K.value.freight)).toFixed(2)
}

const submitOrder = async () => {
  if (!q.value) {
    ElMessage.warning('请选择收货地址')
    return
  }
  Y.value = true
  try {
    const payload = {
      address_id: q.value,
      pay_method: J.value,
      client_token: `order_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`,
      skus: K.value.skus.map(s => ({
        sku_id: s.id,
        count: s.count
      }))
    }
    const res = await commitOrder(payload)
    cartStore.fetchCartCount()
    ElMessage.success('订单提交成功')
    router.push('/payment/' + res.order_id)
  } catch {
    // error handled by interceptor
  } finally {
    Y.value = false
  }
}

onMounted(() => {
  loadSettlement()
})
</script>

<style scoped>
.settlement-page {
  padding: 20px;
}

.page-title {
  margin-bottom: 20px;
  font-size: 22px;
}

.section {
  background: #fff;
  border-radius: 8px;
  margin-bottom: 16px;
  padding: 20px;
}

.section h3 {
  border-bottom: 1px solid #f0f0f0;
  margin-bottom: 16px;
  padding-bottom: 12px;
  font-size: 16px;
}

.address-list {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.address-card {
  cursor: pointer;
  border: 2px solid #eee;
  border-radius: 8px;
  width: 280px;
  padding: 12px 16px;
  transition: border-color 0.2s;
}

.address-card.active,
.address-card:hover {
  border-color: #e4393c;
}

.addr-info {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.addr-name {
  font-weight: 700;
}

.addr-detail {
  color: #666;
  font-size: 13px;
}

.settle-goods {
  display: flex;
  align-items: center;
  gap: 10px;
}

.goods-thumb {
  width: 60px;
  height: 60px;
  object-fit: cover;
  border-radius: 4px;
}

.goods-link {
  cursor: pointer;
}

.goods-name-link {
  cursor: pointer;
  color: inherit;
}

.goods-name-link:hover {
  color: #e4393c;
}

.settlement-bar {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 40px;
  padding: 20px;
  background: #fff;
  border-radius: 8px;
  position: sticky;
  bottom: 0;
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.06);
}

.summary p {
  color: #666;
  margin-bottom: 4px;
  font-size: 14px;
}

.summary .final {
  color: #333;
  font-size: 16px;
}

.final-price {
  font-size: 24px;
}
</style>
