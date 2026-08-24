import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '../router'

const request = axios.create({
  baseURL: '/api',
  timeout: 15000
})

request.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

request.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      const refreshToken = localStorage.getItem('refresh_token')
      if (refreshToken) {
        try {
          const res = await axios.post('/api/token/refresh/', { refresh: refreshToken })
          const newToken = res.data.access
          localStorage.setItem('access_token', newToken)
          if (res.data.refresh) {
            localStorage.setItem('refresh_token', res.data.refresh)
          }
          originalRequest.headers.Authorization = `Bearer ${newToken}`
          return request(originalRequest)
        } catch {
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          router.push({ name: 'Login', query: { next: router.currentRoute.value.fullPath } })
          return Promise.reject(error)
        }
      } else {
        router.push({ name: 'Login', query: { next: router.currentRoute.value.fullPath } })
        return Promise.reject(error)
      }
    }

    let msg = '请求失败'
    if (error.response?.data) {
      const data = error.response.data
      if (data.detail) msg = data.detail
      else if (data.message) msg = data.message
      else if (typeof data === 'object') {
        const firstKey = Object.keys(data)[0]
        if (firstKey) {
          const val = data[firstKey]
          msg = Array.isArray(val) ? val[0] : val
        }
      }
    }
    ElMessage.error(msg)
    return Promise.reject(error)
  }
)

export default request
