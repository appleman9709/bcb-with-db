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
    const { id: familyId } = req.query

    if (!familyId) {
      return res.status(400).json({ error: 'ID семьи обязателен' })
    }

    if (req.method === 'GET') {
      // Получаем членов семьи
      const { data: members, error } = await supabase
        .from('family_members')
        .select('*')
        .eq('family_id', familyId)
        .order('created_at', { ascending: false })

      if (error) {
        console.error('❌ Ошибка получения членов семьи:', error)
        return res.status(500).json({ error: error.message })
      }

      console.log(`✅ Получено членов семьи: ${members.length}`)
      res.status(200).json({ members })

    } else if (req.method === 'POST') {
      // Добавляем члена семьи
      const { user_id, name, role } = req.body

      if (!user_id || !name) {
        return res.status(400).json({ error: 'user_id и name обязательны' })
      }

      console.log(`👥 Добавление члена семьи для семьи ${familyId}`)
      
      const { data: member, error } = await supabase
        .from('family_members')
        .insert([{
          family_id: parseInt(familyId),
          user_id,
          name,
          role: role || 'Родитель'
        }])
        .select()
        .single()

      if (error) {
        console.error('❌ Ошибка добавления члена семьи:', error)
        return res.status(500).json({ error: error.message })
      }

      console.log(`✅ Член семьи добавлен с ID: ${member.id}`)
      res.status(201).json(member)

    } else {
      res.status(405).json({ error: 'Method not allowed' })
    }

  } catch (error) {
    console.error('❌ Ошибка API:', error)
    res.status(500).json({ error: 'Внутренняя ошибка сервера' })
  }
}