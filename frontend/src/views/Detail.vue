<template>
  <div class="detail-page container">
    <template v-if="goods">
      <div class="detail-top">
        <div class="detail-left">
          <ImageCarousel :images="goods.images?.length ? goods.images : (goods.default_image ? [goods.default_image] : [])" :alt="goods.name" />
        </div>
        <div class="detail-right">
          <h1 class="detail-title">{{ goods.name }}</h1>
          <p class="detail-desc">{{ goods.desc }}</p>
          <div class="detail-price-box">
            <span class="detail-price">¥{{ currentSku?.price || goods.price }}</span>
          </div>

          <div v-for="(group, gIdx) in goods.specs" :key="gIdx" class="spec-group">
            <p class="spec-label">{{ group.name }}</p>
            <div class="spec-options">
              <span
                v-for="opt in group.options"
                :key="opt.option_id"
                :class="['spec-option', { active: selectedSpecs[gIdx] === opt.option_id }]"
                @click="selectSpec(gIdx, opt)"
              >{{ opt.value }}</span>
            </div>
          </div>

          <div class="detail-stock">
            <template v-if="currentSku?.stock > 0">
              库存：{{ currentSku.stock }} 件
            </template>
            <span v-else class="out-of-stock">暂时缺货</span>
          </div>

          <div class="detail-actions" :class="{ disabled: !currentSku?.stock }">
            <el-input-number
              v-model="count"
              :min="1"
              :max="currentSku?.stock || 99"
              size="large"
              :disabled="!currentSku?.stock"
            />
            <el-button type="primary" size="large" :disabled="!currentSku?.stock" @click="handleAddCart">加入购物车</el-button>
            <el-button type="danger" size="large" :disabled="!currentSku?.stock" @click="handleBuyNow">立即购买</el-button>
          </div>
        </div>
      </div>

      <div class="detail-bottom">
        <el-tabs>
          <el-tab-pane label="商品详情">
            <div v-html="goods.detail" class="detail-content"></div>
          </el-tab-pane>
          <el-tab-pane :label="`商品评论 (${commentsTotal})`">
            <div class="comment-filter-bar">
              <el-radio-group v-model="commentFilter" @change="onFilterChange">
                <el-radio-button value="all">全部({{ commentCounts.all }})</el-radio-button>
                <el-radio-button value="good">好评({{ commentCounts.good }})</el-radio-button>
                <el-radio-button value="mid">中评({{ commentCounts.mid }})</el-radio-button>
                <el-radio-button value="bad">差评({{ commentCounts.bad }})</el-radio-button>
                <el-radio-button value="media">晒图({{ commentCounts.media }})</el-radio-button>
              </el-radio-group>
            </div>
            <div v-if="comments.length">
              <div v-for="c in comments" :key="c.id" class="comment-item">
                <div class="comment-header">
                  <div class="comment-user-info">
                    <img v-if="c.user?.avatar" :src="c.user.avatar" class="comment-avatar" />
                    <span class="comment-user">{{ c.user?.nickname }}</span>
                  </div>
                </div>
                <div class="comment-meta">
                  {{ formatCommentTime(c.create_time) }} 已购：{{ c.sku?.specs?.join(' - ') }}
                </div>
                <div class="comment-content">{{ c.content }}</div>
                <div v-if="c.images?.length" class="comment-images">
                  <el-image v-for="(img, idx) in c.images" :key="idx" :src="img"
                    :preview-src-list="c.images" :initial-index="idx"
                    fit="cover" class="comment-img" />
                </div>
                <div v-if="c.video" class="comment-video-wrap">
                  <video :src="c.video" class="comment-video" controls />
                </div>
                <el-rate v-if="c.score" v-model="c.score" disabled />
              </div>
              <div v-if="commentsTotal > commentsPageSize" class="pagination">
                <el-pagination
                  v-model:current-page="commentsPage"
                  :page-size="commentsPageSize"
                  :total="commentsTotal"
                  layout="prev, pager, next"
                  @current-change="loadComments"
                />
              </div>
            </div>
            <el-empty v-else description="暂无评论" />
          </el-tab-pane>
        </el-tabs>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getGoodsDetail } from '../api/goods'
import { addBrowse } from '../api/browse'
import { addCart } from '../api/cart'
import { useCartStore } from '../stores/cart'
import ImageCarousel from '../components/ImageCarousel.vue'
import axios from 'axios'

const route = useRoute()
const router = useRouter()
const cartStore = useCartStore()

const goods = ref(null)
const selectedSpecs = ref({})
const count = ref(1)
const comments = ref([])
const commentsTotal = ref(0)
const commentsPage = ref(1)
const commentsPageSize = 10
const commentFilter = ref('all')
const commentCounts = ref({ all: 0, good: 0, mid: 0, bad: 0, media: 0 })

const currentSku = computed(() => goods.value || null)

async function loadGoods() {
  try {
    let data
    if (window.__PRELOADED_SKU_DATA__) {
      data = window.__PRELOADED_SKU_DATA__
      delete window.__PRELOADED_SKU_DATA__
    } else {
      data = await getGoodsDetail(route.params.id)
    }
    goods.value = data
    if (data.specs) {
      const currentId = Number(route.params.id)
      data.specs.forEach((group, idx) => {
        const match = group.options.find(o => o.skus.includes(currentId))
        selectedSpecs.value[idx] = match ? match.option_id : group.options[0].option_id
      })
    }
    addBrowse(route.params.id).catch(() => {})
  } catch (e) {
    console.error('获取商品详情失败', e)
  }
}

async function loadComments() {
  try {
    const params = { page: commentsPage.value, page_size: commentsPageSize }
    const f = commentFilter.value
    if (f === 'good') params.score_type = 'good'
    else if (f === 'mid') params.score_type = 'mid'
    else if (f === 'bad') params.score_type = 'bad'
    else if (f === 'media') params.has_media = 'true'

    const res = await axios.get(`/api/goods/${route.params.id}/comments/`, { params })
    comments.value = res.data.results || []
    commentsTotal.value = res.data.count || 0
    if (res.data.counts) {
      commentCounts.value = res.data.counts
    }
  } catch {
    // ignore
  }
}

function onFilterChange(val) {
  commentFilter.value = val
  commentsPage.value = 1
  loadComments()
}

function selectSpec(groupIdx, opt) {
  selectedSpecs.value[groupIdx] = opt.option_id
  const skuIdSets = goods.value.specs.map((group, idx) => {
    const selectedOptId = selectedSpecs.value[idx]
    const option = group.options.find(o => o.option_id === selectedOptId)
    return option ? new Set(option.skus) : new Set()
  })
  const result = [...skuIdSets[0]].filter(id => skuIdSets.every(set => set.has(id)))
  if (result.length === 1 && String(result[0]) !== route.params.id) {
    router.push(`/detail/${result[0]}`)
  }
}

function formatCommentTime(timeStr) {
  if (!timeStr) return ''
  const d = new Date(timeStr)
  return `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日`
}

async function handleAddCart() {
  if (!currentSku.value) { ElMessage.warning('请选择规格'); return }
  try {
    await addCart({ sku_id: currentSku.value.id, count: count.value })
    ElMessage.success({ message: '已加入购物车', duration: 1000 })
    cartStore.fetchCartCount()
  } catch { /* handled */ }
}

function handleBuyNow() {
  if (!currentSku.value) { ElMessage.warning('请选择规格'); return }
  router.push({
    path: '/settlement',
    query: { sku_id: currentSku.value.id, count: count.value }
  })
}

onMounted(() => {
  loadGoods()
  loadComments()
})

watch(() => route.params.id, () => {
  if (route.params.id) {
    loadGoods()
    loadComments()
  }
})
</script>

<style scoped>
.detail-page {
  padding: 20px;
}
.detail-top {
  background: #fff;
  border-radius: 8px;
  gap: 40px;
  margin-bottom: 20px;
  padding: 30px;
  display: flex;
}
.detail-left {
  flex-shrink: 0;
  width: 400px;
}
.detail-right {
  flex: 1;
}
.detail-title {
  font-size: 22px;
  margin-bottom: 12px;
  font-weight: 700;
}
.detail-desc {
  color: #999;
  margin-bottom: 16px;
  font-size: 14px;
}
.detail-price-box {
  background: #fef0f0;
  border-radius: 8px;
  margin-bottom: 20px;
  padding: 16px;
}
.detail-price {
  color: #e4393c;
  font-size: 28px;
  font-weight: 700;
}
.detail-stock {
  color: #666;
  margin: 12px 0 20px;
  font-size: 14px;
}
.detail-actions {
  gap: 16px;
  display: flex;
  align-items: center;
}
.detail-actions.disabled {
  opacity: 0.5;
  pointer-events: none;
}
.out-of-stock {
  color: #999;
  font-size: 16px;
  font-weight: 700;
}
.spec-group {
  margin-bottom: 16px;
}
.spec-label {
  color: #999;
  margin-bottom: 8px;
  font-size: 14px;
}
.spec-options {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}
.spec-option {
  cursor: pointer;
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 6px 16px;
  font-size: 13px;
  color: #333;
  background: #fff;
  transition: all 0.2s;
}
.spec-option:hover {
  color: #e4393c;
  border-color: #e4393c;
}
.spec-option.active {
  color: #e4393c;
  border-color: #e4393c;
  background: #fef0f0;
}
.detail-bottom {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
}
.detail-content {
  line-height: 1.8;
}
.comment-filter-bar {
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f0f0f0;
}
.comment-item {
  border-bottom: 1px solid #f0f0f0;
  padding: 16px 0;
}
.comment-item:last-child {
  border-bottom: none;
}
.comment-header {
  justify-content: space-between;
  margin-bottom: 8px;
  display: flex;
}
.comment-user-info {
  display: flex;
  align-items: center;
  gap: 8px;
}
.comment-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  object-fit: cover;
}
.comment-user {
  color: #333;
  font-weight: 700;
}
.comment-meta {
  color: #999;
  font-size: 12px;
  margin-bottom: 6px;
}
.comment-content {
  color: #666;
  margin-bottom: 8px;
  font-size: 14px;
}
.comment-images {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 8px;
}
.comment-img {
  width: 80px;
  height: 80px;
  object-fit: cover;
  border-radius: 4px;
  cursor: pointer;
}
.comment-video-wrap {
  margin-bottom: 8px;
}
.comment-video {
  width: 200px;
  border-radius: 4px;
}
.pagination {
  justify-content: center;
  padding: 20px 0;
  display: flex;
}
</style>
