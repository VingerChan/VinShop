import request from './request'

export function getImageCode() {
  return request.post('/image_code/').then(res => res.data)
}

export function sendSmsCode(data) {
  return request.post('/sms_code/', data).then(res => res.data)
}

export function login(data) {
  return request.post('/login/', data).then(res => res.data)
}

export function register(data) {
  return request.post('/register/', data).then(res => res.data)
}

export function getProfile() {
  return request.get('/profile/').then(res => res.data)
}

export function updateProfile(data) {
  return request.patch('/profile/', data).then(res => res.data)
}

export function sendVerifySms() {
  return request.post('/center/sms/').then(res => res.data)
}

export function verifySms(data) {
  return request.patch('/center/sms/', data).then(res => res.data)
}

export function sendChangeSms(mobile) {
  return request.post('/center/sms/change/', null, { params: { mobile } }).then(res => res.data)
}

export function changeSms(data) {
  return request.patch('/center/sms/change/', data).then(res => res.data)
}

export function sendVerifyEmail(email) {
  return request.post('/center/email/', null, { params: { email } }).then(res => res.data)
}

export function verifyEmail(data) {
  return request.patch('/center/email/', data).then(res => res.data)
}

export function changePassword(data) {
  return request.patch('/center/psw/', data).then(res => res.data)
}

export function getAddressList() {
  return request.get('/address/').then(res => res.data)
}

export function addAddress(data) {
  return request.post('/address/', data).then(res => res.data)
}

export function updateAddress(id, data) {
  return request.put(`/address/${id}/`, data).then(res => res.data)
}

export function deleteAddress(id) {
  return request.delete(`/address/${id}/`).then(res => res.data)
}

export function setDefaultAddress(id) {
  return request.patch(`/address/${id}/`, { is_default: true }).then(res => res.data)
}

export async function getAreas(parentId = null) {
  const results = []
  let page = 1
  for (;;) {
    const url = parentId ? `/areas/${parentId}/?page=${page}` : `/areas/?page=${page}`
    const data = await request.get(url).then(res => res.data)
    results.push(...data.results)
    if (!data.next) break
    page++
  }
  return results
}
