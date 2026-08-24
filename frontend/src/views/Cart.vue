<template>
  <div class="cart-page container">
    <h2 class="page-title">我的购物车</h2>
    <template v-if="cartData.cart && cartData.cart.length">
      <div class="cart-content">
        <el-table :data="cartData.cart" style="width: 100%">
          <el-table-column width="50">
            <template #default="{ row }">
              <el-checkbox v-model="row.selected" @change="handleSelect(row)" />
            </template>
          </el-table-column>
          <el-table-column label="商品" min-width="300">
            <template #default="{ row }">
              <div class="cart-goods">
                <img :src="imageUrl(row.default_image_url)" class="goods-thumb" @error="onImgError" />
                <div>
                  <router-link :to="'/detail/' + row.id" class="goods-name">{{ row.name }}</router-link>
                </div>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="单价" width="120">
            <template #default="{ row }">
              <span>¥{{ row.price }}</span>
            </template>
          </el-table-column>
          <el-table-column label="数量" width="180">
            <template #default="{ row }">
              <el-input-number v-model="row.count" :min="1" :max="99" @change="handleCountChange(row)" />
            </template>
          </el-table-column>
          <el-table-column label="小计" width="120">
            <template #default="{ row }">
              <span>¥{{ (row.price * row.count).toFixed(2) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="80">
            <template #default="{ row }">
              <el-button type="danger" link @click="handleDelete(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <div class="cart-footer">
        <div class="footer-left">
          <el-checkbox v-model="allSelected" @change="handleSelectAll">全选</el-checkbox>
          <span>已选 {{ selectedCount }} 件</span>
        </div>
        <div class="footer-right">
          <div class="total-info">
            合计：<span class="total-price">¥{{ totalPrice }}</span>
          </div>
          <el-button type="danger" @click="goSettle">去结算</el-button>
        </div>
      </div>
    </template>
    <el-empty v-else description="购物车是空的" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { getCart, updateCartItem, deleteCartItem, selectAllCart, selectCartItem, deleteSelectedCart } from '../api/cart'
import { useCartStore } from '../stores/cart'

const router = useRouter()
const cartStore = useCartStore()

const cartData = ref({ cart: [] })

const allSelected = computed({
  get() {
    return cartData.value.cart.length > 0 && cartData.value.cart.every(item => item.selected)
  },
  set() {}
})

const selectedCount = computed(() => {
  return cartData.value.cart.filter(item => item.selected).reduce((sum, item) => sum + item.count, 0)
})

const totalPrice = computed(() => {
  return cartData.value.cart
    .filter(item => item.selected)
    .reduce((sum, item) => sum + item.price * item.count, 0)
    .toFixed(2)
})

const loadCart = async () => {
  try {
    cartData.value = await getCart()
  } catch (e) {
    console.error('Failed to load cart', e)
  }
}

const imageUrl = (url) => {
  return url || 'https://via.placeholder.com/80x80?text=商品'
}

const onImgError = (e) => {
  e.target.src = 'https://via.placeholder.com/80x80?text=商品'
}

const handleSelect = async (row) => {
  try {
    await selectCartItem(row.id, { selected: row.selected })
    cartStore.fetchCartCount()
  } catch (e) {
    console.error('Failed to update selection', e)
  }
}

const handleSelectAll = async (val) => {
  try {
    await selectAllCart({ selected: val })
    cartData.value.cart.forEach(item => (item.selected = val))
    cartStore.fetchCartCount()
  } catch (e) {
    console.error('Failed to select all', e)
  }
}

const handleCountChange = async (row) => {
  try {
    await updateCartItem(row.id, { count: row.count })
  } catch (e) {
    console.error('Failed to update count', e)
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除该商品吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await deleteCartItem(row.id)
    await loadCart()
    cartStore.fetchCartCount()
  } catch (e) {
    if (e !== 'cancel') {
      console.error('Failed to delete item', e)
    }
  }
}

const goSettle = () => {
  router.push('/settlement')
}

onMounted(() => {
  loadCart()
})
</script>

<style scoped>
.cart-page {
  padding: 20px;
}

.page-title {
  margin-bottom: 20px;
  font-size: 22px;
}

.cart-content {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
}

.cart-goods {
  display: flex;
  align-items: center;
  gap: 12px;
}

.goods-thumb {
  width: 80px;
  height: 80px;
  object-fit: cover;
  border-radius: 4px;
  border: 1px solid #f0f0f0;
}

.goods-name {
  color: #333;
  font-size: 14px;
  display: -webkit-box;
  overflow: hidden;
  -webkit-line-clamp: 2;
}

.goods-spec {
  color: #999;
  font-size: 12px;
  margin-top: 4px;
}

.cart-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 16px;
  padding: 20px 0 0;
  border-top: 1px solid #f0f0f0;
}

.footer-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.footer-right {
  display: flex;
  align-items: center;
  gap: 24px;
}

.total-info {
  color: #666;
  font-size: 14px;
}

.total-price {
  font-size: 22px;
}
</style>
