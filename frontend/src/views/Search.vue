<template>
  <div class="search-page container">
    <div class="search-header">
      <h2 v-if="keyword">
        搜索 "<span class="keyword">{{ keyword }}</span>" 的结果
      </h2>
      <h2 v-else>全部商品</h2>
      <div class="search-bar">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索商品"
          @keyup.enter="handleSearch"
          clearable
        >
          <template #append>
            <el-button :icon="Search" @click="handleSearch" />
          </template>
        </el-input>
      </div>
    </div>

    <div class="filter-bar">
      <div class="sort-options">
        <span
          v-for="opt in sortOptions"
          :key="opt.value"
          :class="['sort-item', { active: ordering === opt.value }]"
          @click="changeSort(opt.value)"
        >{{ opt.label }}</span>
      </div>
      <div class="price-filter">
        <el-input v-model="minPrice" placeholder="最低价" style="width:100px" @keyup.enter="doSearch" />
        <span>-</span>
        <el-input v-model="maxPrice" placeholder="最高价" style="width:100px" @keyup.enter="doSearch" />
        <el-button @click="doSearch">筛选</el-button>
      </div>
    </div>

    <div v-if="loading" style="text-align:center;padding:40px">
      <el-icon class="is-loading" :size="30"><Loading /></el-icon>
    </div>
    <template v-else>
      <p v-if="total > 0" class="result-info">共找到 {{ total }} 个商品</p>
      <div v-if="goods.length" class="goods-grid">
        <GoodsCard v-for="item in goods" :key="item.id" :goods="item" :highlight="highlights[item.id]" />
      </div>
      <el-empty v-else description="暂无搜索结果" />
      <div v-if="total > pageSize" class="pagination">
        <el-pagination
          v-model:current-page="page"
          :page-size="pageSize"
          :total="total"
          layout="prev, pager, next"
          @current-change="doSearch"
        />
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Search, Loading } from '@element-plus/icons-vue'
import { searchGoods } from '../api/goods'
import GoodsCard from '../components/GoodsCard.vue'

const route = useRoute()
const router = useRouter()

const keyword = ref('')
const searchKeyword = ref('')
const goods = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const loading = ref(false)
const highlights = ref({})
const ordering = ref('')
const minPrice = ref('')
const maxPrice = ref('')

const sortOptions = [
  { label: '综合', value: '' },
  { label: '销量↓', value: '-sales' },
  { label: '评论↓', value: '-comments' },
  { label: '价格↑', value: 'price' },
  { label: '价格↓', value: '-price' }
]

async function doSearch() {
  loading.value = true
  try {
    const params = {
      keyword: keyword.value,
      page: page.value,
      page_size: pageSize.value
    }
    if (ordering.value) params.ordering = ordering.value
    if (minPrice.value) params.min_price = minPrice.value
    if (maxPrice.value) params.max_price = maxPrice.value
    const data = await searchGoods(params)
    goods.value = data.skus || []
    total.value = data.total || 0
    highlights.value = data.highlights || {}
  } catch (e) {
    console.error('搜索失败', e)
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  if (searchKeyword.value.trim()) {
    router.push({ path: '/search', query: { keyword: searchKeyword.value.trim() } })
  }
}

function changeSort(val) {
  ordering.value = val
  page.value = 1
  doSearch()
}

function resetAndSearch() {
  keyword.value = route.query.keyword || ''
  searchKeyword.value = keyword.value
  page.value = 1
  ordering.value = ''
  minPrice.value = ''
  maxPrice.value = ''
  highlights.value = {}
  doSearch()
}

onMounted(resetAndSearch)
watch(() => route.query.keyword, resetAndSearch)
</script>

<style scoped>
.search-page {
  padding: 20px;
}
.search-header {
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  display: flex;
}
.search-header h2 {
  font-size: 20px;
}
.keyword {
  color: #e4393c;
}
.search-bar {
  width: 360px;
}
.filter-bar {
  background: #fff;
  border-radius: 8px;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding: 12px 20px;
  display: flex;
}
.sort-options {
  gap: 4px;
  display: flex;
}
.sort-item {
  cursor: pointer;
  color: #666;
  border-radius: 4px;
  padding: 6px 14px;
  font-size: 14px;
}
.sort-item:hover {
  color: #e4393c;
}
.sort-item.active {
  color: #e4393c;
  background: #fef0f0;
}
.price-filter {
  align-items: center;
  gap: 8px;
  display: flex;
}
.result-info {
  color: #666;
  margin-bottom: 16px;
  font-size: 14px;
}
.goods-grid {
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 20px;
  display: grid;
}
.pagination {
  justify-content: center;
  padding: 20px 0;
  display: flex;
}
</style>
