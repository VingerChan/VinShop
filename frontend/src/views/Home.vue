<template>
  <div class="home container">
    <div class="home-layout" @mouseleave="hoveredGroup = null">
      <div v-if="categories" class="category-sidebar">
        <div
          v-for="group in categories.groups"
          :key="group.id"
          class="category-group"
          @mouseenter="hoveredGroup = group"
        >
          <div class="group-channels">
            <div v-for="ch in group.channels" :key="ch.id" class="category-item">
              <router-link
                :to="{ path: '/search', query: { keyword: ch.category_name } }"
                class="channel-name"
              >{{ ch.category_name }}</router-link>
            </div>
          </div>
        </div>
      </div>

      <div v-if="hoveredGroup" class="category-detail">
        <div v-for="ch in hoveredGroup.channels" :key="ch.id">
          <div v-for="sub in ch.sub_category" :key="sub.id" class="sub-row">
            <router-link
              :to="{ path: '/search', query: { keyword: sub.name } }"
              class="sub-label"
            >{{ sub.name }}：</router-link>
            <div class="sub-links">
              <router-link
                v-for="item in sub.subs"
                :key="item.id"
                :to="{ path: '/search', query: { keyword: item.name } }"
                class="sub-link"
              >{{ item.name }}</router-link>
            </div>
          </div>
        </div>
      </div>

      <div class="main-content">
        <div
          v-if="categories?.contents?.index_lbt"
          class="ad-banner"
        >
          <el-carousel height="440px" :autoplay="true" indicator-position="none">
            <el-carousel-item v-for="(img, idx) in categories.contents.index_lbt" :key="idx">
              <router-link :to="img.link" class="banner-link">
                <img :src="img.img_url" class="banner-img" />
              </router-link>
            </el-carousel-item>
          </el-carousel>
        </div>
      </div>
    </div>

    <div class="section" v-if="recommend.length">
      <h3 class="section-title">为你推荐</h3>
      <div class="goods-grid">
        <GoodsCard v-for="item in recommend" :key="item.id" :goods="item" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getCategory, getRecommend } from '../api/goods'
import GoodsCard from '../components/GoodsCard.vue'

const categories = ref(null)
const recommend = ref([])
const hoveredGroup = ref(null)

onMounted(async () => {
  try {
    // 优先使用预渲染数据，不重复请求 API
    if (window.__PRELOADED_CATEGORIES__) {
      categories.value = window.__PRELOADED_CATEGORIES__
      delete window.__PRELOADED_CATEGORIES__
    } else {
      const catData = await getCategory()
      categories.value = catData
    }
    // 推荐商品始终从 API 获取（实时数据）
    const recData = await getRecommend()
    recommend.value = recData
  } catch (e) {
    console.error('加载首页数据失败', e)
  }
})
</script>

<style scoped>
.home {
  padding: 20px;
}
.home-layout {
  gap: 0;
  margin-bottom: 0;
  display: flex;
  position: relative;
}
.category-sidebar {
  z-index: 101;
  background: #fff;
  border-radius: 8px 0 0 8px;
  flex-shrink: 0;
  width: 200px;
  padding: 8px 0;
  height: 440px;
  overflow-y: auto;
}
.category-group {
  border-bottom: 1px dashed #eee;
  padding: 6px 0;
}
.category-group:last-child {
  border-bottom: none;
}
.group-channels {
  flex-wrap: wrap;
  gap: 2px 4px;
  display: flex;
}
.category-item {
  cursor: pointer;
  align-items: center;
  padding: 2px 6px;
  font-size: 12px;
  transition: color 0.2s;
  display: inline-flex;
}
.category-item:hover .channel-name {
  color: #e4393c;
}
.channel-name {
  color: inherit;
  text-decoration: none;
}
.category-detail {
  z-index: 100;
  background: #fff;
  border: 1px solid #eee;
  border-radius: 0 8px 8px 0;
  width: 500px;
  padding: 20px;
  position: absolute;
  top: 0;
  left: 200px;
  box-shadow: 4px 4px 12px rgba(0, 0, 0, 0.1);
}
.sub-row {
  border-bottom: 1px dashed #f0f0f0;
  align-items: flex-start;
  padding: 6px 0;
  display: flex;
}
.sub-row:last-child {
  border-bottom: none;
}
.sub-label {
  color: #666;
  flex-shrink: 0;
  min-width: 80px;
  font-size: 13px;
  font-weight: 700;
  line-height: 28px;
  text-decoration: none;
}
.sub-label:hover {
  color: #e4393c;
}
.sub-links {
  flex-wrap: wrap;
  gap: 4px;
  display: flex;
}
.sub-link {
  color: #666;
  border-radius: 4px;
  padding: 4px 8px;
  font-size: 13px;
}
.sub-link:hover {
  color: #e4393c;
  background: #fef0f0;
}
.main-content {
  flex: 1;
  min-width: 0;
  min-height: auto;
}
.ad-banner {
  border-radius: 8px;
  overflow: hidden;
}
.banner-link {
  display: block;
  width: 100%;
  height: 100%;
}
.banner-img {
  object-fit: cover;
  width: 100%;
  height: 100%;
}
.section {
  margin-bottom: 30px;
}
.section-title {
  color: #333;
  border-left: 4px solid #e4393c;
  margin-bottom: 16px;
  padding-left: 12px;
  font-size: 22px;
  font-weight: 700;
}
.goods-grid {
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
  display: grid;
}
</style>
