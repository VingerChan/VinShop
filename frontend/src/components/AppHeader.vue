<template>
  <header class="app-header">
    <div class="header-inner container">
      <router-link to="/" class="logo">VinShop</router-link>
      <div class="header-search">
        <el-input
          v-model="keyword"
          placeholder="搜索商品"
          @keyup.enter="handleSearch"
          clearable
        >
          <template #append>
            <el-button :icon="Search" @click="handleSearch" />
          </template>
        </el-input>
      </div>
      <nav class="header-nav">
        <router-link to="/cart" class="nav-item">
          <el-badge :value="cartStore.cartCount" :hidden="!cartStore.cartCount" :max="99">
            <el-icon :size="22"><ShoppingCart /></el-icon>
          </el-badge>
        </router-link>
        <router-link to="/orders" class="nav-item">我的订单</router-link>
        <router-link to="/user" class="nav-item">个人中心</router-link>
        <template v-if="userStore.token">
          <span class="nav-item" @click="handleLogout" style="cursor:pointer">退出</span>
        </template>
        <template v-else>
          <router-link to="/login" class="nav-item">登录</router-link>
        </template>
      </nav>
    </div>
  </header>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { Search, ShoppingCart } from '@element-plus/icons-vue'
import { useUserStore } from '../stores/user'
import { useCartStore } from '../stores/cart'

const router = useRouter()
const userStore = useUserStore()
const cartStore = useCartStore()
const keyword = ref('')

function handleSearch() {
  if (keyword.value.trim()) {
    router.push({ path: '/search', query: { keyword: keyword.value.trim() } })
  }
}

function handleLogout() {
  userStore.logout()
  cartStore.setCount(0)
  router.push('/')
}
</script>

<style scoped>
.app-header {
  background: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  position: sticky;
  top: 0;
  z-index: 999;
}
.header-inner {
  height: 60px;
  display: flex;
  align-items: center;
  gap: 24px;
}
.logo {
  color: #e4393c;
  font-size: 22px;
  font-weight: 700;
  white-space: nowrap;
  text-decoration: none;
}
.header-search {
  flex: 1;
  max-width: 480px;
}
.header-nav {
  display: flex;
  align-items: center;
  gap: 20px;
}
.nav-item {
  color: #333;
  font-size: 14px;
  text-decoration: none;
  white-space: nowrap;
  display: flex;
  align-items: center;
}
.nav-item:hover {
  color: #e4393c;
}
</style>
