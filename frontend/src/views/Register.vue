<template>
  <div class="register-page">
    <div class="register-card">
      <h2 class="register-title">用户注册</h2>
      <el-form v-model="form" label-width="0" size="large">
        <el-form-item>
          <el-input v-model="form.username" placeholder="用户名" prefix-icon="User" />
        </el-form-item>
        <el-form-item>
          <el-input v-model="form.mobile" placeholder="手机号" prefix-icon="Phone" />
        </el-form-item>
        <el-form-item>
          <div class="captcha-row">
            <img
              v-if="captchaImg"
              :src="captchaImg"
              class="captcha-img"
              @click="loadCaptcha"
              title="点击刷新"
            />
            <div v-else class="captcha-img captcha-placeholder" @click="loadCaptcha">
              点击获取验证码
            </div>
            <el-input v-model="form.captcha_code" placeholder="图形验证码" style="flex:1" />
          </div>
        </el-form-item>
        <el-form-item>
          <div class="sms-row">
            <el-input v-model="form.sms_code" placeholder="短信验证码" style="flex:1" />
            <el-button :disabled="countdown > 0" @click="handleSendSms">
              {{ countdown > 0 ? `${countdown}s` : '获取验证码' }}
            </el-button>
          </div>
        </el-form-item>
        <el-form-item>
          <el-input
            v-model="form.password"
            type="password"
            placeholder="密码（至少8位）"
            prefix-icon="Lock"
            show-password
          />
        </el-form-item>
        <el-form-item>
          <el-input
            v-model="form.password2"
            type="password"
            placeholder="确认密码"
            prefix-icon="Lock"
            show-password
          />
        </el-form-item>
        <el-form-item>
          <el-checkbox v-model="form.allow">
            我已阅读并同意 <a href="javascript:;" class="agreement-link">《用户协议》</a>
          </el-checkbox>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" style="width:100%" :loading="loading" @click="handleRegister">
            注 册
          </el-button>
        </el-form-item>
      </el-form>
      <div class="register-footer">
        已有账号？<router-link to="/login">立即登录</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getImageCode, sendSmsCode } from '../api/user'
import { useUserStore } from '../stores/user'

const router = useRouter()
const userStore = useUserStore()

const form = ref({
  username: '',
  mobile: '',
  captcha_code: '',
  sms_code: '',
  password: '',
  password2: '',
  allow: false
})
const captchaImg = ref('')
const captchaKey = ref('')
const loading = ref(false)
const countdown = ref(0)
let timer = null

async function loadCaptcha() {
  try {
    const data = await getImageCode()
    captchaKey.value = data.captcha_key
    captchaImg.value = `data:image/png;base64,${data.b64_str}`
  } catch {
    ElMessage.error('获取验证码失败')
  }
}

async function handleSendSms() {
  if (!form.value.mobile) {
    ElMessage.warning('请输入手机号')
    return
  }
  if (!form.value.captcha_code) {
    ElMessage.warning('请输入图形验证码')
    return
  }
  try {
    await sendSmsCode({
      mobile: form.value.mobile,
      uuid: captchaKey.value,
      frontend_code: form.value.captcha_code
    })
    ElMessage.success('短信验证码已发送')
    countdown.value = 60
    timer = setInterval(() => {
      countdown.value--
      if (countdown.value <= 0) clearInterval(timer)
    }, 1000)
    loadCaptcha()
  } catch {
    loadCaptcha()
  }
}

async function handleRegister() {
  if (!form.value.username) { ElMessage.warning('请输入用户名'); return }
  if (!form.value.mobile) { ElMessage.warning('请输入手机号'); return }
  if (!form.value.sms_code) { ElMessage.warning('请输入短信验证码'); return }
  if (!form.value.password || form.value.password.length < 8) { ElMessage.warning('密码至少8位'); return }
  if (form.value.password !== form.value.password2) { ElMessage.warning('两次密码不一致'); return }
  loading.value = true
  try {
    await userStore.register({
      username: form.value.username,
      mobile: form.value.mobile,
      sms_code: form.value.sms_code,
      password: form.value.password,
      password2: form.value.password2,
      allow: form.value.allow
    })
    ElMessage.success('注册成功')
    router.push('/login')
  } catch {
    // error handled by interceptor
  } finally {
    loading.value = false
  }
}

onUnmounted(() => { if (timer) clearInterval(timer) })

loadCaptcha()
</script>

<style scoped>
.register-page {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  justify-content: center;
  align-items: center;
  min-height: calc(100vh - 140px);
  display: flex;
}
.register-card {
  background: #fff;
  border-radius: 12px;
  width: 500px;
  padding: 40px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
}
.register-title {
  text-align: center;
  color: #333;
  margin-bottom: 24px;
  font-size: 24px;
}
.captcha-row {
  align-items: center;
  gap: 12px;
  width: 100%;
  display: flex;
}
.captcha-img {
  cursor: pointer;
  object-fit: cover;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  width: 120px;
  height: 40px;
}
.captcha-placeholder {
  color: #999;
  background: #f5f7fa;
  justify-content: center;
  align-items: center;
  font-size: 12px;
  display: flex;
}
.sms-row {
  gap: 12px;
  width: 100%;
  display: flex;
}
.register-footer {
  text-align: center;
  color: #666;
  margin-top: 16px;
  font-size: 14px;
}
.register-footer a {
  color: #409eff;
}
.agreement-link {
  color: #409eff;
  text-decoration: none;
}
</style>
