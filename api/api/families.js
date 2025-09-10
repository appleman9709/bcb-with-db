// Получение списка всех семей
import { supabase } from '../lib/supabase.js'

export default async function handler(req, res) {
  // Настраиваем CORS
  res.setHeader('Access-Control-Allow-Origin', '*')
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type')

  if (req.method === 'OPTIONS') {
    res.status(200).end()
    return
  }

  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' })
  }

  try {
    console.log('🔍 Запрос на получение списка семей')
    
    const { data: families, error } = await supabase
      .from('families')
      .select('id, name')
      .order('name')

    if (error) {
      console.error('❌ Ошибка Supabase:', error)
      return res.status(500).json({ error: error.message })
    }

    console.log(`✅ Найдено семей: ${families.length}`)
    for (const family of families) {
      console.log(`   • ID: ${family.id}, Название: ${family.name}`)
    }

    res.status(200).json({ families })
  } catch (error) {
    console.error('❌ Ошибка в get_families:', error)
    res.status(500).json({ error: error.message })
  }
}
