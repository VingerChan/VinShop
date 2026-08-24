import request from './request'

export function uploadCommentFile(file) {
  const formData = new FormData()
  formData.append('file', file)
  return request.post('/comments/upload/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }).then(res => res.data)
}

export function createComment(data) {
  return request.post('/comments/', data).then(res => res.data)
}
