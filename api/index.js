// Главный файл API для Vercel
const { createClient } = require('@supabase/supabase-js')

const supabaseUrl = process.env.SUPABASE_URL
const supabaseKey = process.env.SUPABASE_ANON_KEY

const supabase = createClient(supabaseUrl, supabaseKey)

module.exports = async (req, res) => {
  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*')
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization')

  if (req.method === 'OPTIONS') {
    res.status(200).end()
    return
  }

  // Простой health check
  if (req.url === '/api/health') {
    res.status(200).json({ status: 'OK', message: 'API работает!' })
    return
  }

  // Обработка других маршрутов
  res.status(404).json({ error: 'Маршрут не найден' })
}
