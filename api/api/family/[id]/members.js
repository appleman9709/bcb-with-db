// Получение и добавление членов семьи
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

    if (req.method === 'GET') {
        try {
            const { id: familyId } = req.query

            if (!familyId) {
                return res.status(400).json({ error: 'Family ID is required' })
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

            // Получаем членов семьи
            const { data: members, error: membersError } = await supabase
                .from('family_members')
                .select('user_id, role, name')
                .eq('family_id', familyId)
                .order('role, name')

            if (membersError) {
                console.error('❌ Ошибка получения членов семьи:', membersError)
                return res.status(500).json({ error: membersError.message })
            }

            res.status(200).json({
                family_id: family.id,
                family_name: family.name,
                members: members || []
            })
        } catch (error) {
            console.error('❌ Ошибка в members:', error)
            res.status(500).json({ error: error.message })
        }
    } else if (req.method === 'POST') {
        try {
            const { id: familyId } = req.query
            const { user_id, name, role } = req.body

            if (!familyId || !user_id || !name) {
                return res.status(400).json({ error: 'Missing required fields' })
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
        } catch (error) {
            console.error('❌ Ошибка добавления члена семьи:', error)
            res.status(500).json({ error: error.message })
        }
    } else {
        res.status(405).json({ error: 'Method not allowed' })
    }
}
