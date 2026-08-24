import { defineStore } from 'pinia'
import { ref } from 'vue'
import { login as loginApi, register as registerApi, getProfile as getProfileApi } from '../api/user'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('access_token') || '')
  const refreshToken = ref(localStorage.getItem('refresh_token') || '')
  const userInfo = ref(null)

  function setToken(access, refresh) {
    token.value = access
    refreshToken.value = refresh
    localStorage.setItem('access_token', access)
    localStorage.setItem('refresh_token', refresh)
  }

  function clearToken() {
    token.value = ''
    refreshToken.value = ''
    userInfo.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  }

  async function login(data) {
    const result = await loginApi(data)
    setToken(result.access, result.refresh)
    userInfo.value = result.user
    return result
  }

  async function register(data) {
    const result = await registerApi(data)
    setToken(result.access, result.refresh)
    userInfo.value = result.user
    return result
  }

  async function fetchProfile() {
    const result = await getProfileApi()
    userInfo.value = result
    return result
  }

  function logout() {
    clearToken()
  }

  return { token, refreshToken, userInfo, setToken, clearToken, login, register, fetchProfile, logout }
})
