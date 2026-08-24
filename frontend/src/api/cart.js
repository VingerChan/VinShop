import request from './request'

export function getCart() {
  return request.get('/cart/').then(res => res.data)
}

export function addCart(data) {
  return request.post('/cart/', data).then(res => res.data)
}

export function updateCartItem(id, data) {
  return request.put(`/cart/${id}/`, data).then(res => res.data)
}

export function deleteCartItem(id) {
  return request.delete(`/cart/${id}/`).then(res => res.data)
}

export function selectAllCart(data) {
  return request.put('/cart/selection/', data).then(res => res.data)
}

export function selectCartItem(id, data) {
  return request.put(`/cart/selection/${id}/`, data).then(res => res.data)
}

export function deleteSelectedCart() {
  return request.delete('/cart/selection/delete/').then(res => res.data)
}
