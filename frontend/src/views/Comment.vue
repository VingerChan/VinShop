<template>
  <div class="comment-page container" v-if="orderGoods">
    <div class="comment-card">
      <h2>发表评价</h2>

      <div class="goods-info">
        <img class="goods-thumb" :src="orderGoods.default_image_url || '/placeholder.png'" />
        <div class="goods-detail">
          <div class="goods-name">{{ orderGoods.sku_name }}</div>
          <div class="goods-price">¥{{ orderGoods.price }} × {{ orderGoods.count }}</div>
        </div>
      </div>

      <el-divider />

      <div class="form-item">
        <label class="form-label">商品评分 <span class="required">*</span></label>
        <el-rate v-model="score" :colors="['#99A9BF','#F7BA2A','#FF9900']" show-text :texts="['很差','较差','一般','不错','非常好']" />
      </div>

      <div class="form-item">
        <label class="form-label">评价内容</label>
        <el-input v-model="content" type="textarea" :rows="4" maxlength="2000" show-word-limit placeholder="分享您的使用体验，帮助更多买家（选填）" />
      </div>

      <div class="form-item">
        <label class="form-label">上传图片</label>
        <div class="upload-area">
          <div class="image-list">
            <div class="image-item" v-for="(img, idx) in images" :key="img.file_id">
              <img :src="img.url" class="preview-img" />
              <el-icon class="delete-btn" @click="removeImage(idx)"><Close /></el-icon>
            </div>
            <div v-if="images.length < 6" class="upload-trigger image-trigger" @click="$refs.imageInput.click()">
              <input ref="imageInput" type="file" accept="image/jpeg,image/png,image/webp" style="display:none" @change="handleImageSelect" />
              <el-icon class="upload-icon"><Plus /></el-icon>
              <div class="upload-text">添加图片</div>
            </div>
          </div>
          <div class="upload-hint">最多6张，支持 jpeg/png/webp，单张不超过5MB</div>
        </div>
      </div>

      <div class="form-item">
        <label class="form-label">上传视频</label>
        <div class="upload-area">
          <div v-if="video" class="video-item">
            <video :src="video.url" class="preview-video" controls />
            <el-icon class="delete-btn" @click="removeVideo"><Close /></el-icon>
          </div>
          <div v-if="!video" class="upload-trigger video-trigger" @click="$refs.videoInput.click()">
            <input ref="videoInput" type="file" accept="video/mp4" style="display:none" @change="handleVideoSelect" />
            <el-icon class="upload-icon"><VideoCamera /></el-icon>
            <div class="upload-text">添加视频</div>
          </div>
          <div class="upload-hint">最多1个，支持 mp4，不超过100MB</div>
        </div>
      </div>

      <div class="form-item">
        <el-checkbox v-model="isAnonymous">匿名评价</el-checkbox>
      </div>

      <div class="form-actions">
        <el-button @click="$router.back()">取消</el-button>
        <el-button type="primary" :loading="submitting" :disabled="!score" @click="handleSubmit">提交评价</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Close, Plus, VideoCamera } from '@element-plus/icons-vue'
import { getOrderDetail } from '../api/order'
import { uploadCommentFile, createComment } from '../api/comment'

const route = useRoute()
const router = useRouter()

const orderId = route.params.orderId
const orderGoodsId = route.params.orderGoodsId

const orderGoods = ref(null)
const score = ref(0)
const content = ref('')
const images = ref([])
const video = ref(null)
const isAnonymous = ref(false)
const submitting = ref(false)

const handleImageSelect = async (e) => {
  const file = e.target.files[0]
  e.target.value = ''
  if (!file) return
  if (file.size > 5 * 1024 * 1024) {
    ElMessage.error('图片大小不能超过5MB')
    return
  }
  try {
    const res = await uploadCommentFile(file)
    images.value.push({ file_id: res.file_id, url: res.url })
  } catch {
    // axios 拦截器已处理错误提示
  }
}

const handleVideoSelect = async (e) => {
  const file = e.target.files[0]
  e.target.value = ''
  if (!file) return
  if (file.size > 100 * 1024 * 1024) {
    ElMessage.error('视频大小不能超过100MB')
    return
  }
  try {
    const res = await uploadCommentFile(file)
    video.value = { file_id: res.file_id, url: res.url }
  } catch {
    // axios 拦截器已处理错误提示
  }
}

const removeImage = (idx) => {
  images.value.splice(idx, 1)
}

const removeVideo = () => {
  video.value = null
}

const handleSubmit = async () => {
  if (!score.value) {
    ElMessage.warning('请选择评分')
    return
  }
  submitting.value = true
  try {
    await createComment({
      order_goods_id: Number(orderGoodsId),
      score: score.value,
      content: content.value,
      images: images.value.map(img => img.file_id),
      video: video.value ? video.value.file_id : '',
      is_anonymous: isAnonymous.value
    })
    ElMessage.success('评价成功')
    router.push('/orders')
  } catch {
    // axios 拦截器已处理错误提示
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  try {
    const res = await getOrderDetail(orderId)
    orderGoods.value = res.skus.find(s => s.id === Number(orderGoodsId))
    if (!orderGoods.value) {
      ElMessage.error('订单商品不存在')
      router.back()
    }
  } catch {
    ElMessage.error('加载订单信息失败')
    router.back()
  }
})
</script>

<style scoped>
.comment-page {
  padding: 20px;
}
.comment-card {
  background: #fff;
  border-radius: 8px;
  padding: 30px;
}
.comment-card h2 {
  margin-bottom: 20px;
  font-size: 20px;
}
.goods-info {
  align-items: center;
  gap: 16px;
  display: flex;
}
.goods-thumb {
  width: 80px;
  height: 80px;
  object-fit: cover;
  border-radius: 4px;
}
.goods-name {
  color: #333;
  font-size: 16px;
  margin-bottom: 4px;
}
.goods-price {
  color: #999;
  font-size: 14px;
}
.form-item {
  margin-bottom: 24px;
}
.form-label {
  display: block;
  color: #333;
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 700;
}
.required {
  color: #e4393c;
}
.upload-area {
  margin-top: 4px;
}
.image-list {
  gap: 12px;
  display: flex;
  flex-wrap: wrap;
}
.image-item {
  position: relative;
}
.preview-img {
  width: 80px;
  height: 80px;
  object-fit: cover;
  border-radius: 4px;
}
.video-item {
  position: relative;
}
.preview-video {
  width: 200px;
  height: 150px;
  border-radius: 4px;
  object-fit: cover;
}
.delete-btn {
  position: absolute;
  top: -6px;
  right: -6px;
  background: #f56c6c;
  border-radius: 50%;
  color: #fff;
  cursor: pointer;
  font-size: 14px;
  padding: 2px;
}
.upload-trigger {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border: 1px dashed #dcdfe6;
  border-radius: 4px;
  cursor: pointer;
  text-align: center;
  transition: border-color 0.2s;
}
.image-trigger {
  width: 80px;
  height: 80px;
}
.video-trigger {
  width: 200px;
  height: 150px;
}
.upload-trigger:hover {
  border-color: #409eff;
}
.upload-icon {
  color: #999;
  font-size: 28px;
}
.upload-text {
  color: #999;
  font-size: 12px;
}
.upload-hint {
  color: #c0c4cc;
  font-size: 12px;
  margin-top: 8px;
}
.form-actions {
  justify-content: flex-end;
  gap: 12px;
  margin-top: 30px;
  display: flex;
}
</style>
