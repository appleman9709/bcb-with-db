// Получение данных дашборда для семьи
import { supabase, getThaiTime, getThaiDate } from '../../../lib/supabase.js'

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
    const { id: familyId } = req.query
    const period = req.query.period || 'today'

    if (!familyId) {
      return res.status(400).json({ error: 'Family ID is required' })
    }

    // Получаем информацию о семье
    const { data: family, error: familyError } = await supabase
      .from('families')
      .select('id, name')
      .eq('id', familyId)
      .single()

    if (familyError || !family) {
      return res.status(404).json({ error: 'Family not found' })
    }

    // Получаем настройки семьи
    const { data: settings } = await supabase
      .from('settings')
      .select('*')
      .eq('family_id', familyId)
      .single()

    // Определяем период для статистики
    const today = getThaiDate()
    let startDate, endDate

    if (period === 'week') {
      const start = new Date(today)
      start.setDate(start.getDate() - 6)
      startDate = start.toISOString()
      endDate = new Date(today + 'T23:59:59.999Z').toISOString()
    } else if (period === 'month') {
      const start = new Date(today)
      start.setDate(start.getDate() - 29)
      startDate = start.toISOString()
      endDate = new Date(today + 'T23:59:59.999Z').toISOString()
    } else { // today
      startDate = new Date(today + 'T00:00:00.000Z').toISOString()
      endDate = new Date(today + 'T23:59:59.999Z').toISOString()
    }

    // Получаем последние события
    const [lastFeeding, lastDiaper, lastBath, lastActivity, activeSleep] = await Promise.all([
      // Последнее кормление
      supabase
        .from('feedings')
        .select('timestamp, author_role, author_name')
        .eq('family_id', familyId)
        .order('timestamp', { ascending: false })
        .limit(1)
        .single(),
      
      // Последняя смена подгузника
      supabase
        .from('diapers')
        .select('timestamp, author_role, author_name')
        .eq('family_id', familyId)
        .order('timestamp', { ascending: false })
        .limit(1)
        .single(),
      
      // Последнее купание
      supabase
        .from('baths')
        .select('timestamp, author_role, author_name')
        .eq('family_id', familyId)
        .order('timestamp', { ascending: false })
        .limit(1)
        .single(),
      
      // Последняя активность
      supabase
        .from('activities')
        .select('timestamp, activity_type, author_role, author_name')
        .eq('family_id', familyId)
        .order('timestamp', { ascending: false })
        .limit(1)
        .single(),
      
      // Активная сессия сна
      supabase
        .from('sleep_sessions')
        .select('start_time, author_role, author_name')
        .eq('family_id', familyId)
        .eq('is_active', true)
        .order('start_time', { ascending: false })
        .limit(1)
        .single()
    ])

    // Получаем статистику за период
    const [feedingsStats, diapersStats, bathsStats, activitiesStats] = await Promise.all([
      supabase
        .from('feedings')
        .select('id', { count: 'exact' })
        .eq('family_id', familyId)
        .gte('timestamp', startDate)
        .lte('timestamp', endDate),
      
      supabase
        .from('diapers')
        .select('id', { count: 'exact' })
        .eq('family_id', familyId)
        .gte('timestamp', startDate)
        .lte('timestamp', endDate),
      
      supabase
        .from('baths')
        .select('id', { count: 'exact' })
        .eq('family_id', familyId)
        .gte('timestamp', startDate)
        .lte('timestamp', endDate),
      
      supabase
        .from('activities')
        .select('id', { count: 'exact' })
        .eq('family_id', familyId)
        .gte('timestamp', startDate)
        .lte('timestamp', endDate)
    ])

    // Вычисляем время с последних событий
    const currentTime = getThaiTime()

    const calculateTimeAgo = (timestamp) => {
      if (!timestamp) return null
      const eventTime = new Date(timestamp)
      const diffMs = currentTime - eventTime
      const hours = Math.floor(diffMs / (1000 * 60 * 60))
      const minutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60))
      return { hours, minutes }
    }

    const calculateSleepDuration = (startTime) => {
      if (!startTime) return null
      const start = new Date(startTime)
      const diffMs = currentTime - start
      const hours = Math.floor(diffMs / (1000 * 60 * 60))
      const minutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60))
      return { hours, minutes }
    }

    const dashboardData = {
      family: {
        id: family.id,
        name: family.name
      },
      settings: {
        feed_interval: settings?.feed_interval || 3,
        diaper_interval: settings?.diaper_interval || 2,
        baby_age_months: settings?.baby_age_months || 0,
        baby_birth_date: settings?.baby_birth_date || null,
        tips_enabled: settings?.tips_enabled ?? true,
        bath_reminder_enabled: settings?.bath_reminder_enabled ?? true,
        activity_reminder_enabled: settings?.activity_reminder_enabled ?? true
      },
      last_events: {
        feeding: {
          timestamp: lastFeeding.data?.timestamp || null,
          author_role: lastFeeding.data?.author_role || null,
          author_name: lastFeeding.data?.author_name || null,
          time_ago: calculateTimeAgo(lastFeeding.data?.timestamp)
        },
        diaper: {
          timestamp: lastDiaper.data?.timestamp || null,
          author_role: lastDiaper.data?.author_role || null,
          author_name: lastDiaper.data?.author_name || null,
          time_ago: calculateTimeAgo(lastDiaper.data?.timestamp)
        },
        bath: {
          timestamp: lastBath.data?.timestamp || null,
          author_role: lastBath.data?.author_role || null,
          author_name: lastBath.data?.author_name || null,
          time_ago: calculateTimeAgo(lastBath.data?.timestamp)
        },
        activity: {
          timestamp: lastActivity.data?.timestamp || null,
          activity_type: lastActivity.data?.activity_type || null,
          author_role: lastActivity.data?.author_role || null,
          author_name: lastActivity.data?.author_name || null,
          time_ago: calculateTimeAgo(lastActivity.data?.timestamp)
        }
      },
      sleep: {
        is_active: !!activeSleep.data,
        start_time: activeSleep.data?.start_time || null,
        author_role: activeSleep.data?.author_role || null,
        author_name: activeSleep.data?.author_name || null,
        duration: calculateSleepDuration(activeSleep.data?.start_time)
      },
      today_stats: {
        feedings: feedingsStats.count || 0,
        diapers: diapersStats.count || 0,
        baths: bathsStats.count || 0,
        activities: activitiesStats.count || 0
      }
    }

    res.status(200).json(dashboardData)
  } catch (error) {
    console.error('❌ Ошибка в dashboard:', error)
    res.status(500).json({ error: error.message })
  }
}
