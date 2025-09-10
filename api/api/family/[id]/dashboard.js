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
      console.log(`📊 Загрузка дашборда для семьи ${familyId}`)

      // Получаем статистику за сегодня
      const today = new Date().toISOString().split('T')[0]
      
      const [feedingsResult, diapersResult, bathsResult, activitiesResult, sleepResult] = await Promise.all([
        supabase.from('feedings').select('*').eq('family_id', familyId).gte('timestamp', today),
        supabase.from('diapers').select('*').eq('family_id', familyId).gte('timestamp', today),
        supabase.from('baths').select('*').eq('family_id', familyId).gte('timestamp', today),
        supabase.from('activities').select('*').eq('family_id', familyId).gte('timestamp', today),
        supabase.from('sleep_sessions').select('*').eq('family_id', familyId).eq('is_active', true)
      ])

      const todayStats = {
        feedings: feedingsResult.data?.length || 0,
        diapers: diapersResult.data?.length || 0,
        baths: bathsResult.data?.length || 0,
        activities: activitiesResult.data?.length || 0
      }

      // Получаем последние события
      const [lastFeeding, lastDiaper, lastBath, lastActivity] = await Promise.all([
        supabase.from('feedings').select('*').eq('family_id', familyId).order('timestamp', { ascending: false }).limit(1).single(),
        supabase.from('diapers').select('*').eq('family_id', familyId).order('timestamp', { ascending: false }).limit(1).single(),
        supabase.from('baths').select('*').eq('family_id', familyId).order('timestamp', { ascending: false }).limit(1).single(),
        supabase.from('activities').select('*').eq('family_id', familyId).order('timestamp', { ascending: false }).limit(1).single()
      ])

      const lastEvents = {
        feeding: lastFeeding.data || null,
        diaper: lastDiaper.data || null,
        bath: lastBath.data || null,
        activity: lastActivity.data || null
      }

      // Получаем информацию о сне
      const sleep = {
        is_active: sleepResult.data?.length > 0,
        duration: null
      }

      if (sleep.is_active && sleepResult.data[0]) {
        const startTime = new Date(sleepResult.data[0].start_time)
        const now = new Date()
        const diffMs = now - startTime
        const hours = Math.floor(diffMs / (1000 * 60 * 60))
        const minutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60))
        sleep.duration = { hours, minutes }
      }

      console.log(`✅ Дашборд загружен для семьи ${familyId}`)
      res.status(200).json({
        today_stats: todayStats,
        last_events: lastEvents,
        sleep
      })

    } else {
      res.status(405).json({ error: 'Method not allowed' })
    }

  } catch (error) {
    console.error('❌ Ошибка API:', error)
    res.status(500).json({ error: 'Внутренняя ошибка сервера' })
  }
}