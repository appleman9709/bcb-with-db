// Завершение сессии сна
import { supabase } from '../../../../lib/supabase.js'

export default async function handler(req, res) {
    res.setHeader('Access-Control-Allow-Origin', '*')
    res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS')
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type')

    if (req.method === 'OPTIONS') {
        res.status(200).end()
        return
    }

    if (req.method === 'POST') {
        try {
            const { id: familyId } = req.query
            const { author_id, author_name, author_role } = req.body

            if (!familyId || !author_id || !author_name) {
                return res.status(400).json({ error: 'Missing required fields' })
            }

            console.log(`😴 Завершение сна для семьи ${familyId}`)
            
            // Завершаем активную сессию сна
            const { data: sleepSession, error } = await supabase
                .from('sleep_sessions')
                .update({ 
                    is_active: false, 
                    end_time: new Date().toISOString() 
                })
                .eq('family_id', parseInt(familyId))
                .eq('is_active', true)
                .select()
                .single()

            if (error) {
                console.error('❌ Ошибка завершения сна:', error)
                return res.status(500).json({ error: error.message })
            }

            console.log(`✅ Сон завершен`)
            res.status(200).json(sleepSession)
        } catch (error) {
            console.error('❌ Ошибка завершения сна:', error)
            res.status(500).json({ error: error.message })
        }
    } else {
        res.status(405).json({ error: 'Method not allowed' })
    }
}
