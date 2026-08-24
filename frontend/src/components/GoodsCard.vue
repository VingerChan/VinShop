<template>
  <div class="goods-card" @click="goDetail">
    <div class="goods-img">
      <img :src="imageUrl" :alt="goods.name" @error="onError" />
    </div>
    <div class="goods-info">
      <p class="goods-name" v-if="highlight" v-html="highlight"></p>
      <p class="goods-name" v-else>{{ goods.name }}</p>
      <p class="goods-price">¥{{ goods.price }}</p>
      <div class="goods-meta">
        <span>评论 {{ goods.comments || 0 }}</span>
        <span>销量 {{ goods.sales || 0 }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  goods: { type: Object, required: true },
  highlight: { type: String, default: '' }
})

const router = useRouter()

const imageUrl = computed(() => {
  const url = props.goods.default_img_url || props.goods.default_image
  return url ? url : 'https://via.placeholder.com/200x200?text=No+Image'
})

function goDetail() {
  router.push(`/detail/${props.goods.id}`)
}

function onError(e) {
  e.target.src = 'https://via.placeholder.com/200x200?text=No+Image'
}
</script>

<style scoped>
.goods-card {
  cursor: pointer;
  background: #fff;
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  transition: all 0.3s;
  overflow: hidden;
}
.goods-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
}
.goods-img {
  aspect-ratio: 1;
  background: #fafafa;
  width: 100%;
  overflow: hidden;
}
.goods-img img {
  object-fit: cover;
  width: 100%;
  height: 100%;
}
.goods-info {
  padding: 12px;
}
.goods-name {
  color: #333;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  min-height: 40px;
  margin-bottom: 8px;
  font-size: 14px;
  line-height: 1.4;
  display: -webkit-box;
  overflow: hidden;
}
.goods-name :deep(em) {
  color: #e4393c;
  font-style: normal;
  font-weight: 700;
}
.goods-price {
  color: #e4393c;
  margin-bottom: 6px;
  font-size: 18px;
  font-weight: 700;
}
.goods-meta {
  color: #999;
  justify-content: space-between;
  font-size: 12px;
  display: flex;
}
</style>
