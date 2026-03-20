import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({ baseURL: API_URL })

export async function analyzeFile(file) {
  const form = new FormData()
  form.append('file', file)
  const res = await api.post('/analyze', form, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
  return res.data
}

export async function getHistory() {
  const res = await api.get('/history')
  return res.data
}

export default api