-- Схема базы данных Supabase для BabyCareBot
-- Создано на основе существующих SQLite таблиц

-- Включаем расширения
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Таблица семей
CREATE TABLE IF NOT EXISTS families (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Таблица членов семьи
CREATE TABLE IF NOT EXISTS family_members (
    id SERIAL PRIMARY KEY,
    family_id INTEGER REFERENCES families(id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL,
    role TEXT DEFAULT 'Родитель',
    name TEXT DEFAULT 'Неизвестно',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(family_id, user_id)
);

-- Таблица кормлений
CREATE TABLE IF NOT EXISTS feedings (
    id SERIAL PRIMARY KEY,
    family_id INTEGER REFERENCES families(id) ON DELETE CASCADE,
    author_id BIGINT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    author_role TEXT DEFAULT 'Родитель',
    author_name TEXT DEFAULT 'Неизвестно',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Таблица смен подгузников
CREATE TABLE IF NOT EXISTS diapers (
    id SERIAL PRIMARY KEY,
    family_id INTEGER REFERENCES families(id) ON DELETE CASCADE,
    author_id BIGINT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    author_role TEXT DEFAULT 'Родитель',
    author_name TEXT DEFAULT 'Неизвестно',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Таблица купаний
CREATE TABLE IF NOT EXISTS baths (
    id SERIAL PRIMARY KEY,
    family_id INTEGER REFERENCES families(id) ON DELETE CASCADE,
    author_id BIGINT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    author_role TEXT DEFAULT 'Родитель',
    author_name TEXT DEFAULT 'Неизвестно',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Таблица активностей
CREATE TABLE IF NOT EXISTS activities (
    id SERIAL PRIMARY KEY,
    family_id INTEGER REFERENCES families(id) ON DELETE CASCADE,
    author_id BIGINT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    activity_type TEXT DEFAULT 'tummy_time',
    author_role TEXT DEFAULT 'Родитель',
    author_name TEXT DEFAULT 'Неизвестно',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Таблица сессий сна
CREATE TABLE IF NOT EXISTS sleep_sessions (
    id SERIAL PRIMARY KEY,
    family_id INTEGER REFERENCES families(id) ON DELETE CASCADE,
    author_id BIGINT NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    author_role TEXT DEFAULT 'Родитель',
    author_name TEXT DEFAULT 'Неизвестно',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Таблица настроек
CREATE TABLE IF NOT EXISTS settings (
    id SERIAL PRIMARY KEY,
    family_id INTEGER REFERENCES families(id) ON DELETE CASCADE,
    feed_interval INTEGER DEFAULT 3,
    diaper_interval INTEGER DEFAULT 2,
    tips_enabled BOOLEAN DEFAULT TRUE,
    tips_time_hour INTEGER DEFAULT 9,
    tips_time_minute INTEGER DEFAULT 0,
    bath_reminder_enabled BOOLEAN DEFAULT TRUE,
    bath_reminder_hour INTEGER DEFAULT 19,
    bath_reminder_minute INTEGER DEFAULT 0,
    bath_reminder_period INTEGER DEFAULT 1,
    activity_reminder_enabled BOOLEAN DEFAULT TRUE,
    activity_reminder_interval INTEGER DEFAULT 2,
    sleep_monitoring_enabled BOOLEAN DEFAULT TRUE,
    baby_age_months INTEGER DEFAULT 0,
    baby_birth_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(family_id)
);

-- Создаем индексы для оптимизации запросов
CREATE INDEX IF NOT EXISTS idx_feedings_family_timestamp ON feedings(family_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_diapers_family_timestamp ON diapers(family_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_baths_family_timestamp ON baths(family_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_activities_family_timestamp ON activities(family_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_sleep_sessions_family_active ON sleep_sessions(family_id, is_active);
CREATE INDEX IF NOT EXISTS idx_family_members_family ON family_members(family_id);

-- Создаем функцию для обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Создаем триггеры для автоматического обновления updated_at
CREATE TRIGGER update_families_updated_at BEFORE UPDATE ON families
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_family_members_updated_at BEFORE UPDATE ON family_members
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_sleep_sessions_updated_at BEFORE UPDATE ON sleep_sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_settings_updated_at BEFORE UPDATE ON settings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Включаем Row Level Security (RLS)
ALTER TABLE families ENABLE ROW LEVEL SECURITY;
ALTER TABLE family_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE feedings ENABLE ROW LEVEL SECURITY;
ALTER TABLE diapers ENABLE ROW LEVEL SECURITY;
ALTER TABLE baths ENABLE ROW LEVEL SECURITY;
ALTER TABLE activities ENABLE ROW LEVEL SECURITY;
ALTER TABLE sleep_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE settings ENABLE ROW LEVEL SECURITY;

-- Создаем политики RLS (пока разрешаем все для API ключа)
-- В продакшене нужно будет настроить более строгие политики
CREATE POLICY "Enable all operations for service role" ON families
    FOR ALL USING (true);

CREATE POLICY "Enable all operations for service role" ON family_members
    FOR ALL USING (true);

CREATE POLICY "Enable all operations for service role" ON feedings
    FOR ALL USING (true);

CREATE POLICY "Enable all operations for service role" ON diapers
    FOR ALL USING (true);

CREATE POLICY "Enable all operations for service role" ON baths
    FOR ALL USING (true);

CREATE POLICY "Enable all operations for service role" ON activities
    FOR ALL USING (true);

CREATE POLICY "Enable all operations for service role" ON sleep_sessions
    FOR ALL USING (true);

CREATE POLICY "Enable all operations for service role" ON settings
    FOR ALL USING (true);
