import request from './request'

export function getCategory() {
  return request.get('/category/').then(res => res.data)
}

export function getRecommend() {
  return request.get('/goods/recommend/').then(res => res.data)
}

export function getGoodsDetail(skuId) {
  return request.get(`/goods/${skuId}/`).then(res => res.data)
}

export function searchGoods(params) {
  return request.get('/search/', { params }).then(res => res.data)
}
