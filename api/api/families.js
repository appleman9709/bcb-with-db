// Создание и получение семей
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

    if (req.method === 'GET') {
        // Получение списка семей
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
    } else if (req.method === 'POST') {
        // Создание новой семьи
        try {
            const { name } = req.body
            
            if (!name) {
                return res.status(400).json({ error: 'Name is required' })
            }

            console.log(`🏠 Создание семьи: ${name}`)
            
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
        } catch (error) {
            console.error('❌ Ошибка создания семьи:', error)
            res.status(500).json({ error: error.message })
        }
    } else {
        res.status(405).json({ error: 'Method not allowed' })
    }
}