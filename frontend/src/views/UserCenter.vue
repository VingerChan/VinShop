<template>
  <div class="user-center container">
    <el-tabs tab-position="left" class="user-tabs" v-model="activeTab">
      <el-tab-pane label="个人信息" name="profile">
        <div class="panel">
          <h3>个人信息</h3>
          <div class="avatar-row">
            <el-avatar :size="80" :src="profileData.user_img || ''" />
            <el-upload :before-upload="handleAvatarUpload" :show-file-list="false">
              <el-button>更换头像</el-button>
            </el-upload>
          </div>
          <el-form label-width="80px" style="margin-top: 20px;">
            <el-form-item label="昵称">
              <el-input v-model="profileData.nickname" placeholder="请输入昵称" />
            </el-form-item>
            <el-form-item label="性别">
              <el-radio-group v-model="profileData.gender">
                <el-radio :value="0">保密</el-radio>
                <el-radio :value="1">男</el-radio>
                <el-radio :value="2">女</el-radio>
              </el-radio-group>
            </el-form-item>
            <el-form-item label="生日">
              <el-date-picker v-model="profileData.birthday" type="date" placeholder="请选择生日" value-format="YYYY-MM-DD" />
            </el-form-item>
          </el-form>
          <el-button type="primary" @click="saveProfile" :loading="saving">保存</el-button>
        </div>
      </el-tab-pane>

      <el-tab-pane label="收货地址" name="address">
        <div class="panel">
          <div class="address-header">
            <h3>收货地址</h3>
            <el-button type="primary" @click="openAddAddress">新增地址</el-button>
          </div>
          <el-table :data="addressList" style="width: 100%"
            :row-class-name="({ row }) => row.id === defaultAddressId ? 'default-row' : ''">
            <el-table-column prop="receiver_name" label="收货人" width="100" />
            <el-table-column prop="mobile" label="电话/手机" width="140" />
            <el-table-column label="所在地区" width="200">
              <template #default="{ row }">
                {{ row.province }} {{ row.city }} {{ row.district }}
              </template>
            </el-table-column>
            <el-table-column label="详细地址">
              <template #default="{ row }">
                {{ row.place }}
                <el-tag v-if="row.id === defaultAddressId" size="small" type="danger" style="margin-left: 8px;">默认</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="180">
              <template #default="{ row }">
                <el-button link @click="editAddress(row)">编辑</el-button>
                <el-button link @click="handleDeleteAddress(row.id)">删除</el-button>
                <el-button link v-if="row.id !== defaultAddressId" @click="handleSetDefault(row.id)">设为默认</el-button>
              </template>
            </el-table-column>
          </el-table>

          <el-dialog v-model="showAddressDialog" :title="dialogTitle" width="480px">
            <el-form :model="addressForm" label-width="80px">
              <el-form-item label="收货人">
                <el-input v-model="addressForm.receiver_name" placeholder="请输入收货人姓名" />
              </el-form-item>
              <el-form-item label="手机号">
                <el-input v-model="addressForm.mobile" placeholder="请输入手机号" />
              </el-form-item>
              <el-form-item label="省">
                <el-select v-model="addressForm.province" placeholder="请选择省" @change="onProvinceChange">
                  <el-option v-for="p in provinces" :key="p.id" :label="p.name" :value="p.id" />
                </el-select>
              </el-form-item>
              <el-form-item label="市">
                <el-select v-model="addressForm.city" placeholder="请选择市" :disabled="!addressForm.province" @change="onCityChange">
                  <el-option v-for="c in cities" :key="c.id" :label="c.name" :value="c.id" />
                </el-select>
              </el-form-item>
              <el-form-item label="区">
                <el-select v-model="addressForm.district" placeholder="请选择区" :disabled="!addressForm.city">
                  <el-option v-for="d in districts" :key="d.id" :label="d.name" :value="d.id" />
                </el-select>
              </el-form-item>
              <el-form-item label="地址">
                <el-input v-model="addressForm.place" placeholder="请输入详细地址" />
              </el-form-item>
              <el-form-item label="默认地址">
                <el-checkbox v-model="addressForm.is_default">设为默认地址</el-checkbox>
              </el-form-item>
            </el-form>
            <template #footer>
              <el-button @click="showAddressDialog = false">取消</el-button>
              <el-button type="primary" @click="saveAddress">确认</el-button>
            </template>
          </el-dialog>
        </div>
      </el-tab-pane>

      <el-tab-pane label="账户安全" name="security">
        <div class="panel">
          <h3>账户安全</h3>
          <div class="security-cards">
            <div class="security-card">
              <div class="card-title">手机号</div>
              <div class="card-desc">{{ maskMobile(profileData.mobile) }}</div>
              <el-button type="primary" @click="openPhoneDialog">修改手机号</el-button>
            </div>
            <div class="security-card">
              <div class="card-title">登录密码</div>
              <div class="card-desc">定期更换密码有助于账号安全</div>
              <el-button type="primary" @click="openPasswordDialog">修改登录密码</el-button>
            </div>
            <div class="security-card">
              <div class="card-title">邮箱</div>
              <div class="card-desc">{{ profileData.email || '设置邮箱有助于您的账号易用' }}</div>
              <el-button type="primary" @click="openEmailDialog">{{ profileData.email ? '修改邮箱' : '绑定邮箱' }}</el-button>
            </div>
          </div>
        </div>

        <el-dialog v-model="showPhoneDialog" title="修改手机号" width="420px" @close="resetPhoneDialog">
          <div v-if="phoneStep === 1">
            <p class="dialog-tip">为了您的账号安全，请先验证身份</p>
            <p class="dialog-sub">验证码将发送至 {{ profileData.mobile }}</p>
            <div class="dialog-step">
              <el-input v-model="phoneVerifyCode" placeholder="请输入验证码" style="flex:1;" />
              <el-button @click="handleSendVerifySmsForPhone" :disabled="phoneSendCooldown > 0">
                {{ phoneSendCooldown > 0 ? phoneSendCooldown + 's后重发' : '发送验证码' }}
              </el-button>
            </div>
          </div>
          <div v-if="phoneStep === 2">
            <el-input v-model="newMobile" placeholder="请输入新手机号" style="margin-bottom:12px;" />
            <div class="dialog-step">
              <el-input v-model="newMobileCode" placeholder="请输入验证码" style="flex:1;" />
              <el-button @click="handleSendChangeSms" :disabled="newMobileSendCooldown > 0">
                {{ newMobileSendCooldown > 0 ? newMobileSendCooldown + 's后重发' : '发送验证码' }}
              </el-button>
            </div>
          </div>
          <template #footer>
            <el-button @click="showPhoneDialog = false">取消</el-button>
            <el-button v-if="phoneStep === 1" type="primary" @click="handleVerifyPhoneIdentity">确认</el-button>
            <el-button v-if="phoneStep === 2" type="primary" @click="handleChangeMobile">确认</el-button>
          </template>
        </el-dialog>

        <el-dialog v-model="showPasswordDialog" title="修改登录密码" width="420px" @close="resetPasswordDialog">
          <div v-if="passwordStep === 1">
            <p class="dialog-tip">为了您的账号安全，请先验证身份</p>
            <p class="dialog-sub">验证码将发送至 {{ profileData.mobile }}</p>
            <div class="dialog-step">
              <el-input v-model="passwordVerifyCode" placeholder="请输入验证码" style="flex:1;" />
              <el-button @click="handleSendVerifySmsForPassword" :disabled="passwordSendCooldown > 0">
                {{ passwordSendCooldown > 0 ? passwordSendCooldown + 's后重发' : '发送验证码' }}
              </el-button>
            </div>
          </div>
          <div v-if="passwordStep === 2">
            <el-input v-model="newPassword" type="password" placeholder="请输入新密码" show-password style="margin-bottom:12px;" />
            <el-input v-model="newPassword2" type="password" placeholder="请再次输入新密码" show-password />
          </div>
          <template #footer>
            <el-button @click="showPasswordDialog = false">取消</el-button>
            <el-button v-if="passwordStep === 1" type="primary" @click="handleVerifyPasswordIdentity">确认</el-button>
            <el-button v-if="passwordStep === 2" type="primary" @click="handleChangePassword">确认</el-button>
          </template>
        </el-dialog>

        <el-dialog v-model="showEmailDialog" :title="profileData.email ? '修改邮箱' : '绑定邮箱'" width="420px" @close="resetEmailDialog">
          <div v-if="emailStep === 1">
            <p class="dialog-tip">为了您的账号安全，请先验证身份</p>
            <p class="dialog-sub">验证码将发送至 {{ profileData.mobile }}</p>
            <div class="dialog-step">
              <el-input v-model="emailVerifyCode" placeholder="请输入验证码" style="flex:1;" />
              <el-button @click="handleSendVerifySmsForEmail" :disabled="emailSendCooldown > 0">
                {{ emailSendCooldown > 0 ? emailSendCooldown + 's后重发' : '发送验证码' }}
              </el-button>
            </div>
          </div>
          <div v-if="emailStep === 2">
            <el-input v-model="newEmail" placeholder="请输入邮箱地址" style="margin-bottom:12px;" />
            <div class="dialog-step">
              <el-input v-model="emailCode" placeholder="请输入邮箱验证码" style="flex:1;" />
              <el-button @click="handleSendEmailCode" :disabled="emailCodeSendCooldown > 0">
                {{ emailCodeSendCooldown > 0 ? emailCodeSendCooldown + 's后重发' : '发送验证码' }}
              </el-button>
            </div>
          </div>
          <template #footer>
            <el-button @click="showEmailDialog = false">取消</el-button>
            <el-button v-if="emailStep === 1" type="primary" @click="handleVerifyEmailIdentity">确认</el-button>
            <el-button v-if="emailStep === 2" type="primary" @click="handleChangeEmail">确认</el-button>
          </template>
        </el-dialog>
      </el-tab-pane>

      <el-tab-pane label="浏览记录" name="browse">
        <div class="panel">
          <h3>浏览记录</h3>
          <div class="browse-header">
            <span></span>
            <el-button @click="handleClearBrowse">清空全部</el-button>
          </div>
          <div v-for="(group, date) in groupedBrowse" :key="date">
            <div class="browse-date">{{ date }}</div>
            <div class="browse-list">
              <div
                v-for="item in group"
                :key="item.id"
                class="browse-item"
                @click="goToProduct(item.product_id)"
              >
                <div class="browse-delete" @click.stop="handleDeleteBrowse(item.id)">X</div>
                <img :src="item.product_img" alt="" style="width: 120px; height: 120px; object-fit: cover; border-radius: 4px;" />
                <div class="browse-name">{{ item.product_name }}</div>
                <div class="browse-price">¥{{ item.product_price }}</div>
              </div>
            </div>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getProfile,
  updateProfile,
  getAddressList,
  addAddress,
  updateAddress,
  deleteAddress,
  setDefaultAddress,
  sendVerifySms,
  verifySms,
  sendChangeSms,
  changeSms,
  sendVerifyEmail,
  verifyEmail,
  changePassword,
  getAreas
} from '../api/user'
import {
  getBrowseList,
  deleteBrowseItem,
  clearBrowse
} from '../api/browse'

const router = useRouter()

const activeTab = ref('profile')
const profileData = ref({ nickname: '', gender: 0, birthday: '', user_img: '' })
const saving = ref(false)

const addressList = ref([])
const defaultAddressId = ref(null)
const showAddressDialog = ref(false)
const editingAddress = ref(null)
const addressForm = ref({ receiver_name: '', mobile: '', province: null, city: null, district: null, place: '', is_default: false })
const provinces = ref([])
const cities = ref([])
const districts = ref([])

const dialogTitle = computed(() => (editingAddress.value ? '编辑地址' : '新增地址'))

const showPhoneDialog = ref(false)
const phoneStep = ref(1)
const phoneVerifyCode = ref('')
const newMobile = ref('')
const newMobileCode = ref('')
const phoneSendCooldown = ref(0)
const newMobileSendCooldown = ref(0)

const showPasswordDialog = ref(false)
const passwordStep = ref(1)
const passwordVerifyCode = ref('')
const newPassword = ref('')
const newPassword2 = ref('')
const passwordSendCooldown = ref(0)

const showEmailDialog = ref(false)
const emailStep = ref(1)
const emailVerifyCode = ref('')
const newEmail = ref('')
const emailCode = ref('')
const emailSendCooldown = ref(0)
const emailCodeSendCooldown = ref(0)
const browseList = ref([])
const browseLoading = ref(false)

const groupedBrowse = computed(() => {
  const groups = {}
  browseList.value.forEach(group => {
    const date = group.date || '未知日期'
    groups[date] = (group.skus || []).map(sku => ({
      id: sku.id,
      product_id: sku.id,
      product_name: sku.name,
      product_price: sku.price,
      product_img: sku.default_img_url
    }))
  })
  return groups
})

async function loadProfile() {
  try {
    const res = await getProfile()
    profileData.value = res.data || res
  } catch (e) {
    console.error(e)
  }
}

async function saveProfile() {
  saving.value = true
  try {
    await updateProfile({
      nickname: profileData.value.nickname,
      gender: profileData.value.gender,
      birthday: profileData.value.birthday
    })
    ElMessage.success('保存成功')
  } catch (e) {
    console.error(e)
  } finally {
    saving.value = false
  }
}

async function handleAvatarUpload(file) {
  const formData = new FormData()
  formData.append('user_img', file)
  try {
    await updateProfile(formData)
    await loadProfile()
    ElMessage.success('头像更新成功')
  } catch (e) {
    console.error(e)
  }
  return false
}

async function loadAddress() {
  try {
    const res = await getAddressList()
    const data = res.data || res
    addressList.value = data.address || []
    defaultAddressId.value = data.default_address || null
  } catch (e) {
    console.error(e)
  }
}

async function loadProvinces() {
  provinces.value = await getAreas()
}

function onProvinceChange() {
  addressForm.value.city = null
  addressForm.value.district = null
  cities.value = []
  districts.value = []
  if (addressForm.value.province) {
    getAreas(addressForm.value.province).then(list => { cities.value = list })
  }
}

function onCityChange() {
  addressForm.value.district = null
  districts.value = []
  if (addressForm.value.city) {
    getAreas(addressForm.value.city).then(list => { districts.value = list })
  }
}

function openAddAddress() {
  addressForm.value = { receiver_name: '', mobile: '', province: null, city: null, district: null, place: '', is_default: false }
  editingAddress.value = null
  cities.value = []
  districts.value = []
  showAddressDialog.value = true
  loadProvinces()
}

function editAddress(addr) {
  addressForm.value = {
    receiver_name: addr.receiver_name,
    mobile: addr.mobile,
    province: null,
    city: null,
    district: null,
    place: addr.place,
    is_default: !!addr.is_default
  }
  editingAddress.value = addr
  showAddressDialog.value = true
  loadProvinces().then(() => {
    const p = provinces.value.find(item => item.name === addr.province)
    if (p) {
      addressForm.value.province = p.id
      return getAreas(p.id)
    }
    return []
  }).then(list => {
    cities.value = list
    const c = cities.value.find(item => item.name === addr.city)
    if (c) {
      addressForm.value.city = c.id
      return getAreas(c.id)
    }
    return []
  }).then(list => {
    districts.value = list
    const d = districts.value.find(item => item.name === addr.district)
    if (d) {
      addressForm.value.district = d.id
    }
  })
}

async function saveAddress() {
  try {
    if (editingAddress.value) {
      await updateAddress(editingAddress.value.id, addressForm.value)
    } else {
      await addAddress(addressForm.value)
    }
    await loadAddress()
    showAddressDialog.value = false
    ElMessage.success(editingAddress.value ? '地址已更新' : '地址已添加')
  } catch (e) {
    console.error(e)
  }
}

async function handleDeleteAddress(id) {
  try {
    await ElMessageBox.confirm('确定删除该地址吗？', '提示', { type: 'warning' })
    await deleteAddress(id)
    await loadAddress()
    ElMessage.success('地址已删除')
  } catch (e) {
    if (e !== 'cancel') console.error(e)
  }
}

async function handleSetDefault(id) {
  try {
    await setDefaultAddress(id)
    await loadAddress()
    ElMessage.success('已设为默认地址')
  } catch (e) {
    console.error(e)
  }
}

function maskMobile(mobile) {
  if (!mobile || mobile.length < 7) return mobile || '未绑定'
  return mobile.slice(0, 3) + '****' + mobile.slice(-4)
}

function startCooldown(cooldownRef, seconds) {
  cooldownRef.value = seconds
  const timer = setInterval(() => {
    cooldownRef.value--
    if (cooldownRef.value <= 0) clearInterval(timer)
  }, 1000)
}

function openPhoneDialog() {
  showPhoneDialog.value = true
  phoneStep.value = 1
  phoneVerifyCode.value = ''
  newMobile.value = ''
  newMobileCode.value = ''
  phoneSendCooldown.value = 0
  newMobileSendCooldown.value = 0
}

function resetPhoneDialog() {
  phoneStep.value = 1
  phoneVerifyCode.value = ''
  newMobile.value = ''
  newMobileCode.value = ''
  phoneSendCooldown.value = 0
  newMobileSendCooldown.value = 0
}

function openPasswordDialog() {
  showPasswordDialog.value = true
  passwordStep.value = 1
  passwordVerifyCode.value = ''
  newPassword.value = ''
  newPassword2.value = ''
  passwordSendCooldown.value = 0
}

function resetPasswordDialog() {
  passwordStep.value = 1
  passwordVerifyCode.value = ''
  newPassword.value = ''
  newPassword2.value = ''
  passwordSendCooldown.value = 0
}

function openEmailDialog() {
  showEmailDialog.value = true
  emailStep.value = 1
  emailVerifyCode.value = ''
  newEmail.value = ''
  emailCode.value = ''
  emailSendCooldown.value = 0
  emailCodeSendCooldown.value = 0
}

function resetEmailDialog() {
  emailStep.value = 1
  emailVerifyCode.value = ''
  newEmail.value = ''
  emailCode.value = ''
  emailSendCooldown.value = 0
  emailCodeSendCooldown.value = 0
}

async function handleSendVerifySmsForPhone() {
  try {
    await sendVerifySms()
    startCooldown(phoneSendCooldown, 60)
    ElMessage.success('验证码已发送')
  } catch (e) {
    console.error(e)
  }
}

async function handleVerifyPhoneIdentity() {
  try {
    await verifySms({ sms_code: phoneVerifyCode.value })
    ElMessage.success('身份验证成功')
    phoneStep.value = 2
  } catch (e) {
    console.error(e)
  }
}

async function handleSendChangeSms() {
  try {
    await sendChangeSms(newMobile.value)
    startCooldown(newMobileSendCooldown, 60)
    ElMessage.success('验证码已发送')
  } catch (e) {
    console.error(e)
  }
}

async function handleChangeMobile() {
  try {
    await changeSms({ mobile: newMobile.value, sms_code: newMobileCode.value })
    ElMessage.success('手机号修改成功')
    showPhoneDialog.value = false
    await loadProfile()
  } catch (e) {
    console.error(e)
  }
}

async function handleSendVerifySmsForPassword() {
  try {
    await sendVerifySms()
    startCooldown(passwordSendCooldown, 60)
    ElMessage.success('验证码已发送')
  } catch (e) {
    console.error(e)
  }
}

async function handleVerifyPasswordIdentity() {
  try {
    await verifySms({ sms_code: passwordVerifyCode.value })
    ElMessage.success('身份验证成功')
    passwordStep.value = 2
  } catch (e) {
    console.error(e)
  }
}

async function handleChangePassword() {
  if (!newPassword.value || !newPassword2.value) {
    ElMessage.warning('请填写完整密码信息')
    return
  }
  if (newPassword.value !== newPassword2.value) {
    ElMessage.warning('两次输入的新密码不一致')
    return
  }
  try {
    await changePassword({ psw1: newPassword.value, psw2: newPassword2.value })
    ElMessage.success('密码修改成功，请重新登录')
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    showPasswordDialog.value = false
    router.push('/login')
  } catch (e) {
    console.error(e)
  }
}

async function handleSendVerifySmsForEmail() {
  try {
    await sendVerifySms()
    startCooldown(emailSendCooldown, 60)
    ElMessage.success('验证码已发送')
  } catch (e) {
    console.error(e)
  }
}

async function handleVerifyEmailIdentity() {
  try {
    await verifySms({ sms_code: emailVerifyCode.value })
    ElMessage.success('身份验证成功')
    emailStep.value = 2
  } catch (e) {
    console.error(e)
  }
}

async function handleSendEmailCode() {
  try {
    await sendVerifyEmail(newEmail.value)
    startCooldown(emailCodeSendCooldown, 60)
    ElMessage.success('邮箱验证码已发送')
  } catch (e) {
    console.error(e)
  }
}

async function handleChangeEmail() {
  try {
    await verifyEmail({ email: newEmail.value, email_code: emailCode.value })
    ElMessage.success('邮箱绑定成功')
    showEmailDialog.value = false
    await loadProfile()
  } catch (e) {
    console.error(e)
  }
}

async function loadBrowse() {
  browseLoading.value = true
  try {
    const res = await getBrowseList()
    browseList.value = res.data || res || []
  } catch (e) {
    console.error(e)
  } finally {
    browseLoading.value = false
  }
}

async function handleDeleteBrowse(id) {
  try {
    await ElMessageBox.confirm('确定删除该浏览记录吗？', '提示', { type: 'warning' })
    await deleteBrowseItem(id)
    await loadBrowse()
    ElMessage.success('已删除')
  } catch (e) {
    if (e !== 'cancel') console.error(e)
  }
}

async function handleClearBrowse() {
  try {
    await ElMessageBox.confirm('确定清空全部浏览记录吗？', '提示', { type: 'warning' })
    await clearBrowse()
    await loadBrowse()
    ElMessage.success('已清空')
  } catch (e) {
    if (e !== 'cancel') console.error(e)
  }
}

function goToProduct(productId) {
  if (productId) {
    router.push(`/product/${productId}`)
  }
}

onMounted(() => {
  loadProfile()
  loadAddress()
  loadBrowse()
})
</script>

<style scoped>
.user-center {
  padding: 20px;
}

.user-tabs {
  background: #fff;
  border-radius: 8px;
  min-height: 500px;
}

.user-tabs .el-tabs__header {
  min-width: 120px;
}

.panel {
  padding: 20px 30px;
}

.panel h3 {
  border-bottom: 1px solid #f0f0f0;
  margin-bottom: 20px;
  padding-bottom: 12px;
  font-size: 18px;
}

.address-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.address-header h3 {
  margin-bottom: 0;
  padding-bottom: 0;
  border-bottom: none;
}

.default-row {
  background-color: #fef0f0 !important;
}

.avatar-row {
  display: flex;
  align-items: center;
  gap: 16px;
}

.security-cards {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
}

.security-card {
  border: 1px solid #e4e4e4;
  border-radius: 8px;
  padding: 24px;
  width: 220px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.card-title {
  font-size: 16px;
  font-weight: 700;
  color: #333;
}

.card-desc {
  font-size: 13px;
  color: #999;
  min-height: 20px;
}

.dialog-tip {
  font-size: 14px;
  color: #333;
  margin-bottom: 8px;
}

.dialog-sub {
  font-size: 13px;
  color: #999;
  margin-bottom: 16px;
}

.dialog-step {
  display: flex;
  gap: 12px;
  align-items: center;
}

.browse-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.browse-date {
  color: #999;
  border-bottom: 1px solid #f0f0f0;
  margin-bottom: 12px;
  padding: 8px 0;
  font-size: 14px;
}

.browse-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 16px;
  margin-bottom: 20px;
}

.browse-item {
  cursor: pointer;
  text-align: center;
  position: relative;
}

.browse-delete {
  text-align: center;
  color: #fff;
  cursor: pointer;
  z-index: 1;
  background: rgba(0, 0, 0, 0.5);
  border-radius: 50%;
  width: 20px;
  height: 20px;
  font-size: 14px;
  line-height: 20px;
  position: absolute;
  top: 4px;
  right: 4px;
}

.browse-delete:hover {
  background: #e4393c;
}

.browse-name {
  color: #333;
  font-size: 13px;
  margin-top: 6px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.browse-price {
  color: #e4393c;
  font-size: 14px;
}
</style>
