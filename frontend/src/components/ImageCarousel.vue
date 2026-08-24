<template>
  <div class="image-carousel">
    <div class="image-main-wrapper">
      <div
        class="main-image"
        ref="mainImageRef"
        @mouseenter="showZoom = true"
        @mouseleave="showZoom = false"
        @mousemove="handleMouseMove"
      >
        <img :src="currentImage" :alt="alt" @error="onError" />
        <div v-if="showZoom" class="lens" :style="lensStyle"></div>
      </div>
      <div v-if="showZoom" class="zoom-panel">
        <img :src="currentImage" :style="zoomStyle" />
      </div>
    </div>

    <div v-if="images.length > 1" class="thumbnail-list">
      <div
        v-for="(img, idx) in images"
        :key="idx"
        :class="['thumbnail-item', { active: currentIndex === idx }]"
        @mouseenter="currentIndex = idx"
      >
        <img :src="img" @error="onError" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  images: { type: Array, default: () => [] },
  alt: { type: String, default: '' }
})

const mainImageRef = ref(null)
const currentIndex = ref(0)
const showZoom = ref(false)
const offsetX = ref(0)
const offsetY = ref(0)

const LENS_SIZE = 160
const ZOOM_SIZE = 400
const ZOOM_RATIO = ZOOM_SIZE / LENS_SIZE

const currentImage = computed(() => {
  if (props.images.length === 0) return 'https://via.placeholder.com/400x400?text=No+Image'
  return props.images[currentIndex.value]
})

const lensStyle = computed(() => ({
  width: '160px',
  height: '160px',
  transform: `translate(${offsetX.value}px, ${offsetY.value}px)`
}))

const zoomStyle = computed(() => ({
  width: '1000px',
  height: '1000px',
  transform: `translate(${-offsetX.value * ZOOM_RATIO}px, ${-offsetY.value * ZOOM_RATIO}px)`
}))

function getValidUrl(url) {
  return url ? (url.startsWith('http') ? url : url) : 'https://via.placeholder.com/400x400?text=No+Image'
}

function onError(e) {
  e.target.src = 'https://via.placeholder.com/400x400?text=No+Image'
}

function handleMouseMove(e) {
  const rect = mainImageRef.value.getBoundingClientRect()
  let x = e.clientX - rect.left
  let y = e.clientY - rect.top
  const halfLens = LENS_SIZE / 2
  x = Math.max(0, Math.min(x - halfLens, rect.width - LENS_SIZE))
  y = Math.max(0, Math.min(y - halfLens, rect.height - LENS_SIZE))
  offsetX.value = x
  offsetY.value = y
}
</script>

<style scoped>
.image-carousel {
  width: 100%;
}
.image-main-wrapper {
  margin-bottom: 12px;
  position: relative;
}
.main-image {
  cursor: crosshair;
  border: 1px solid #eee;
  border-radius: 8px;
  flex-shrink: 0;
  width: 400px;
  height: 400px;
  position: relative;
  overflow: hidden;
}
.main-image img {
  object-fit: cover;
  pointer-events: none;
  width: 100%;
  height: 100%;
}
.lens {
  pointer-events: none;
  z-index: 1;
  background: rgba(255, 255, 255, 0.3);
  border: 1px solid rgba(228, 57, 60, 0.5);
  position: absolute;
  top: 0;
  left: 0;
}
.zoom-panel {
  z-index: 100;
  background: #fff;
  border: 1px solid #eee;
  border-radius: 8px;
  width: 400px;
  height: 400px;
  position: absolute;
  top: 0;
  left: 416px;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);
}
.zoom-panel img {
  position: absolute;
  top: 0;
  left: 0;
}
.thumbnail-list {
  gap: 8px;
  padding-bottom: 4px;
  display: flex;
  overflow-x: auto;
}
.thumbnail-item {
  cursor: pointer;
  border: 2px solid transparent;
  border-radius: 4px;
  flex-shrink: 0;
  width: 60px;
  height: 60px;
  transition: border-color 0.2s;
  overflow: hidden;
}
.thumbnail-item.active {
  border-color: #e4393c;
}
.thumbnail-item img {
  object-fit: cover;
  width: 100%;
  height: 100%;
}
</style>
