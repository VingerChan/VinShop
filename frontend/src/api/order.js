import request from './request'

export function getSettlement(params) {
  return request.get('/order/settlement/', { params }).then(res => res.data)
}

export function commitOrder(data) {
  return request.post('/order/commit/', data).then(res => res.data)
}

export function getOrders(params) {
  return request.get('/orders/', { params }).then(res => res.data)
}

export function getOrderDetail(orderId) {
  return request.get(`/orders/${orderId}/`).then(res => res.data)
}

export function confirmReceipt(orderId) {
  return request.post(`/orders/${orderId}/confirm/`).then(res => res.data)
}
