import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getCart } from '../api/cart'

export const useCartStore = defineStore('cart', () => {
  const cartCount = ref(0)

  async function fetchCartCount() {
    try {
      const data = await getCart()
      cartCount.value = data.cart_count
    } catch {
      cartCount.value = 0
    }
  }

  function setCount(val) {
    cartCount.value = val
  }

  return { cartCount, fetchCartCount, setCount }
})
