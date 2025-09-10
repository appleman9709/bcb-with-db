// Добавление активностей
import { supabase } from '../../../lib/supabase.js'

export default async function handler(req, res) {
    res.setHeader('Access-Control-Allow-Origin', '*')
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type')

    if (req.method === 'OPTIONS') {
        res.status(200).end()
        return
    }

    if (req.method === 'POST') {
        try {
            const { id: familyId } = req.query
            const { author_id, author_name, author_role, timestamp, activity_type = 'tummy_time' } = req.body

            if (!familyId || !author_id || !author_name || !timestamp) {
                return res.status(400).json({ error: 'Missing required fields' })
            }

            console.log(`🎮 Добавление активности для семьи ${familyId}`)
            
            const { data: activity, error } = await supabase
                .from('activities')
                .insert([{
                    family_id: parseInt(familyId),
                    author_id,
                    author_name,
                    author_role,
                    timestamp,
                    activity_type
                }])
                .select()
                .single()

            if (error) {
                console.error('❌ Ошибка добавления активности:', error)
                return res.status(500).json({ error: error.message })
            }

            console.log(`✅ Активность добавлена с ID: ${activity.id}`)
            res.status(201).json(activity)
        } catch (error) {
            console.error('❌ Ошибка добавления активности:', error)
            res.status(500).json({ error: error.message })
        }
    } else {
        res.status(405).json({ error: 'Method not allowed' })
    }
}
