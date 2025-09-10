import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.SUPABASE_URL
const supabaseKey = process.env.SUPABASE_ANON_KEY

const supabase = createClient(supabaseUrl, supabaseKey)

export default async function handler(req, res) {
  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*')
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization')

  if (req.method === 'OPTIONS') {
    res.status(200).end()
    return
  }

  try {
    if (req.method === 'GET') {
      // Получаем список семей
      const { data: families, error } = await supabase
        .from('families')
        .select('*')
        .order('created_at', { ascending: false })

      if (error) {
        console.error('❌ Ошибка получения семей:', error)
        return res.status(500).json({ error: error.message })
      }

      console.log(`✅ Получено семей: ${families.length}`)
      res.status(200).json({ families })

    } else if (req.method === 'POST') {
      // Создаем новую семью
      const { name } = req.body

      if (!name) {
        return res.status(400).json({ error: 'Название семьи обязательно' })
      }

      console.log(`👨‍👩‍👧‍👦 Создание семьи: ${name}`)
      
      const { data: family, error } = await supabase
        .from('families')
        .insert([{ name }])
        .select()
        .single()

      if (error) {
        console.error('❌ Ошибка создания семьи:', error)
        return res.status(500).json({ error: error.message })
      }

      console.log(`✅ Семья создана с ID: ${family.id}`)
      res.status(201).json(family)

    } else {
      res.status(405).json({ error: 'Method not allowed' })
    }

  } catch (error) {
    console.error('❌ Ошибка API:', error)
    res.status(500).json({ error: 'Внутренняя ошибка сервера' })
  }
}