// Получение истории событий для семьи
import { supabase, getThaiDate } from '../../../lib/supabase.js'

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
    let days = parseInt(req.query.days) || 7

    if (!familyId) {
      return res.status(400).json({ error: 'Family ID is required' })
    }

    if (days > 30) {
      days = 30 // Ограничиваем максимум 30 дней
    }

    // Проверяем существование семьи
    const { data: family, error: familyError } = await supabase
      .from('families')
      .select('id, name')
      .eq('id', familyId)
      .single()

    if (familyError || !family) {
      return res.status(404).json({ error: 'Family not found' })
    }

    // Получаем события за последние N дней
    const endDate = getThaiDate()
    const startDate = new Date(endDate)
    startDate.setDate(startDate.getDate() - days + 1)

    const startDatetime = startDate.toISOString()
    const endDatetime = new Date(endDate + 'T23:59:59.999Z').toISOString()

    // Получаем статистику по дням
    const [feedingsData, diapersData, bathsData, activitiesData] = await Promise.all([
      // Кормления
      supabase
        .from('feedings')
        .select('timestamp')
        .eq('family_id', familyId)
        .gte('timestamp', startDatetime)
        .lte('timestamp', endDatetime),
      
      // Смены подгузников
      supabase
        .from('diapers')
        .select('timestamp')
        .eq('family_id', familyId)
        .gte('timestamp', startDatetime)
        .lte('timestamp', endDatetime),
      
      // Купания
      supabase
        .from('baths')
        .select('timestamp')
        .eq('family_id', familyId)
        .gte('timestamp', startDatetime)
        .lte('timestamp', endDatetime),
      
      // Активности
      supabase
        .from('activities')
        .select('timestamp')
        .eq('family_id', familyId)
        .gte('timestamp', startDatetime)
        .lte('timestamp', endDatetime)
    ])

    // Группируем данные по дням
    const groupByDate = (data) => {
      const grouped = {}
      data.forEach(item => {
        const date = item.timestamp.split('T')[0]
        grouped[date] = (grouped[date] || 0) + 1
      })
      return grouped
    }

    const feedingsByDay = groupByDate(feedingsData.data || [])
    const diapersByDay = groupByDate(diapersData.data || [])
    const bathsByDay = groupByDate(bathsData.data || [])
    const activitiesByDay = groupByDate(activitiesData.data || [])

    // Формируем данные по дням
    const historyData = []
    for (let i = 0; i < days; i++) {
      const currentDate = new Date(startDate)
      currentDate.setDate(currentDate.getDate() + i)
      const dateStr = currentDate.toISOString().split('T')[0]
      
      historyData.push({
        date: dateStr,
        feedings: feedingsByDay[dateStr] || 0,
        diapers: diapersByDay[dateStr] || 0,
        baths: bathsByDay[dateStr] || 0,
        activities: activitiesByDay[dateStr] || 0
      })
    }

    res.status(200).json({
      family_id: family.id,
      family_name: family.name,
      period_days: days,
      history: historyData
    })
  } catch (error) {
    console.error('❌ Ошибка в history:', error)
    res.status(500).json({ error: error.message })
  }
}
