import request from './request'

export function getBrowseList() {
  return request.get('/browse/').then(res => res.data)
}

export function addBrowse(skuId) {
  return request.post('/browse/', { sku_id: skuId }).then(res => res.data)
}

export function deleteBrowseItem(id) {
  return request.delete(`/browse/${id}/`).then(res => res.data)
}

export function clearBrowse() {
  return request.delete('/browse/').then(res => res.data)
}
