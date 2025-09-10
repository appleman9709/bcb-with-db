// Добавление кормлений
import { supabase } from '../../../lib/supabase.js'

export default async function handler(req, res) {
    // Настраиваем CORS
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
            const { author_id, author_name, author_role, timestamp } = req.body

            if (!familyId || !author_id || !author_name || !timestamp) {
                return res.status(400).json({ error: 'Missing required fields' })
            }

            console.log(`🍼 Добавление кормления для семьи ${familyId}`)
            
            const { data: feeding, error } = await supabase
                .from('feedings')
                .insert([{
                    family_id: parseInt(familyId),
                    author_id,
                    author_name,
                    author_role,
                    timestamp
                }])
                .select()
                .single()

            if (error) {
                console.error('❌ Ошибка добавления кормления:', error)
                return res.status(500).json({ error: error.message })
            }

            console.log(`✅ Кормление добавлено с ID: ${feeding.id}`)
            res.status(201).json(feeding)
        } catch (error) {
            console.error('❌ Ошибка добавления кормления:', error)
            res.status(500).json({ error: error.message })
        }
    } else {
        res.status(405).json({ error: 'Method not allowed' })
    }
}
