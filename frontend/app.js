// BabyCareBot Dashboard - Полнофункциональное веб-приложение
class BabyCareBot {
    constructor() {
        this.currentUser = null;
        this.currentFamily = null;
        this.chart = null;
        this.init();
    }

    async init() {
        console.log('🚀 Инициализация BabyCareBot Dashboard');
        
        // Проверяем, есть ли сохраненные данные пользователя
        const savedUser = localStorage.getItem('babycarebot_user');
        if (savedUser) {
            this.currentUser = JSON.parse(savedUser);
            await this.loadFamilyData();
            this.showDashboard();
        } else {
            this.showLogin();
        }

        this.setupEventListeners();
        this.setupAutoRefresh();
    }

    setupEventListeners() {
        // Login
        document.getElementById('login-btn').addEventListener('click', () => this.handleLogin());
        
        // Logout
        document.getElementById('logout-btn').addEventListener('click', () => this.handleLogout());
        
        // Quick actions
        document.querySelectorAll('.action-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const action = e.currentTarget.dataset.action;
                this.showEventModal(action);
            });
        });
        
        // Sleep button
        document.getElementById('sleep-btn').addEventListener('click', () => this.toggleSleep());
        
        // Modal
        document.getElementById('close-modal').addEventListener('click', () => this.hideEventModal());
        document.getElementById('cancel-event').addEventListener('click', () => this.hideEventModal());
        document.getElementById('save-event').addEventListener('click', () => this.saveEvent());
        
        // Set current time for event modal
        document.getElementById('event-time').value = this.getCurrentDateTime();
    }

    setupAutoRefresh() {
        // Обновляем данные каждые 30 секунд
        setInterval(() => {
            if (this.currentFamily) {
                this.loadDashboardData();
            }
        }, 30000);
    }

    async handleLogin() {
        const familyName = document.getElementById('family-name').value.trim();
        const userName = document.getElementById('user-name-input').value.trim();
        const userRole = document.getElementById('user-role').value;

        if (!familyName || !userName) {
            alert('Пожалуйста, заполните все поля');
            return;
        }

        try {
            // Создаем или находим семью
            let family = await this.findOrCreateFamily(familyName);
            
            // Создаем или находим пользователя
            let user = await this.findOrCreateUser(family.id, userName, userRole);
            
            this.currentUser = user;
            this.currentFamily = family;
            
            // Сохраняем в localStorage
            localStorage.setItem('babycarebot_user', JSON.stringify(user));
            localStorage.setItem('babycarebot_family', JSON.stringify(family));
            
            await this.loadFamilyData();
            this.showDashboard();
            
        } catch (error) {
            console.error('Ошибка входа:', error);
            alert('Ошибка входа. Попробуйте еще раз.');
        }
    }

    async findOrCreateFamily(name) {
        try {
            // Ищем существующую семью
            const response = await fetch(`${window.APP_CONFIG.API_BASE_URL}/families`);
            
            if (!response.ok) {
                console.error('Ошибка загрузки семей:', response.status, response.statusText);
                throw new Error('Ошибка загрузки семей');
            }
            
            const data = await response.json();
            console.log('Загружены семьи:', data);
            
            const existingFamily = data.families?.find(f => f.name === name);
            if (existingFamily) {
                console.log('Найдена существующая семья:', existingFamily);
                return existingFamily;
            }
            
            // Создаем новую семью
            console.log('Создаем новую семью:', name);
            const createResponse = await fetch(`${window.APP_CONFIG.API_BASE_URL}/families`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ name })
            });
            
            if (!createResponse.ok) {
                const errorText = await createResponse.text();
                console.error('Ошибка создания семьи:', createResponse.status, errorText);
                throw new Error(`Ошибка создания семьи: ${createResponse.status}`);
            }
            
            const newFamily = await createResponse.json();
            console.log('Создана новая семья:', newFamily);
            return newFamily;
            
        } catch (error) {
            console.error('Ошибка в findOrCreateFamily:', error);
            throw error;
        }
    }

    async findOrCreateUser(familyId, name, role) {
        // Создаем пользователя (в реальном приложении здесь была бы аутентификация)
        const userId = Date.now(); // Простой ID для демо
        
        const response = await fetch(`${window.APP_CONFIG.API_BASE_URL}/family/${familyId}/members`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                user_id: userId,
                name: name,
                role: role
            })
        });
        
        if (!response.ok) {
            throw new Error('Ошибка создания пользователя');
        }
        
        return {
            id: userId,
            name: name,
            role: role,
            family_id: familyId
        };
    }

    async loadFamilyData() {
        if (!this.currentFamily) return;
        
        try {
            await Promise.all([
                this.loadDashboardData(),
                this.loadFamilyMembers(),
                this.loadHistoryChart()
            ]);
        } catch (error) {
            console.error('Ошибка загрузки данных семьи:', error);
        }
    }

    async loadDashboardData() {
        try {
            const response = await fetch(`${window.APP_CONFIG.API_BASE_URL}/family/${this.currentFamily.id}/dashboard`);
            const data = await response.json();
            
            this.updateStats(data.today_stats);
            this.updateLastEvents(data.last_events);
            this.updateSleepStatus(data.sleep);
            
        } catch (error) {
            console.error('Ошибка загрузки дашборда:', error);
        }
    }

    async loadFamilyMembers() {
        try {
            const response = await fetch(`${window.APP_CONFIG.API_BASE_URL}/family/${this.currentFamily.id}/members`);
            const data = await response.json();
            
            this.updateFamilyMembers(data.members);
            
        } catch (error) {
            console.error('Ошибка загрузки членов семьи:', error);
        }
    }

    async loadHistoryChart() {
        try {
            const response = await fetch(`${window.APP_CONFIG.API_BASE_URL}/family/${this.currentFamily.id}/history?days=7`);
            const data = await response.json();
            
            this.updateHistoryChart(data.history);
            
        } catch (error) {
            console.error('Ошибка загрузки истории:', error);
        }
    }

    updateStats(stats) {
        document.getElementById('feedings-count').textContent = stats.feedings;
        document.getElementById('diapers-count').textContent = stats.diapers;
        document.getElementById('baths-count').textContent = stats.baths;
        document.getElementById('activities-count').textContent = stats.activities;
    }

    updateLastEvents(events) {
        const eventsList = document.getElementById('events-list');
        const eventsArray = [];
        
        if (events.feeding.timestamp) {
            eventsArray.push({
                type: 'feeding',
                icon: '🍼',
                label: 'Кормление',
                time: this.formatTimeAgo(events.feeding.timestamp),
                author: events.feeding.author_name
            });
        }
        
        if (events.diaper.timestamp) {
            eventsArray.push({
                type: 'diaper',
                icon: '👶',
                label: 'Подгузник',
                time: this.formatTimeAgo(events.diaper.timestamp),
                author: events.diaper.author_name
            });
        }
        
        if (events.bath.timestamp) {
            eventsArray.push({
                type: 'bath',
                icon: '🛁',
                label: 'Купание',
                time: this.formatTimeAgo(events.bath.timestamp),
                author: events.bath.author_name
            });
        }
        
        if (events.activity.timestamp) {
            eventsArray.push({
                type: 'activity',
                icon: '🎮',
                label: 'Активность',
                time: this.formatTimeAgo(events.activity.timestamp),
                author: events.activity.author_name
            });
        }
        
        if (eventsArray.length === 0) {
            eventsList.innerHTML = '<div class="no-events">Событий пока нет</div>';
            return;
        }
        
        eventsList.innerHTML = eventsArray.map(event => `
            <div class="event-item">
                <div class="event-icon">${event.icon}</div>
                <div class="event-details">
                    <div class="event-label">${event.label}</div>
                    <div class="event-meta">${event.time} • ${event.author}</div>
                </div>
            </div>
        `).join('');
    }

    updateSleepStatus(sleep) {
        const sleepCard = document.getElementById('sleep-card');
        const sleepStatus = document.getElementById('sleep-status');
        const sleepDuration = document.getElementById('sleep-duration');
        const sleepBtn = document.getElementById('sleep-btn');
        
        if (sleep.is_active) {
            sleepStatus.textContent = 'Спит';
            sleepDuration.textContent = this.formatDuration(sleep.duration);
            sleepBtn.textContent = 'Завершить сон';
            sleepBtn.classList.add('active');
        } else {
            sleepStatus.textContent = 'Не спит';
            sleepDuration.textContent = '';
            sleepBtn.textContent = 'Начать сон';
            sleepBtn.classList.remove('active');
        }
    }

    updateFamilyMembers(members) {
        const membersList = document.getElementById('members-list');
        
        if (members.length === 0) {
            membersList.innerHTML = '<div class="no-members">Членов семьи пока нет</div>';
            return;
        }
        
        membersList.innerHTML = members.map(member => `
            <div class="member-item">
                <div class="member-avatar">${member.name.charAt(0)}</div>
                <div class="member-details">
                    <div class="member-name">${member.name}</div>
                    <div class="member-role">${member.role}</div>
                </div>
            </div>
        `).join('');
    }

    updateHistoryChart(history) {
        const ctx = document.getElementById('history-chart').getContext('2d');
        
        if (this.chart) {
            this.chart.destroy();
        }
        
        const labels = history.map(day => {
            const date = new Date(day.date);
            return date.toLocaleDateString('ru', { weekday: 'short', day: 'numeric' });
        }).reverse();
        
        this.chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Кормления',
                        data: history.map(day => day.feedings).reverse(),
                        borderColor: '#FF6B6B',
                        backgroundColor: 'rgba(255, 107, 107, 0.1)',
                        tension: 0.4
                    },
                    {
                        label: 'Подгузники',
                        data: history.map(day => day.diapers).reverse(),
                        borderColor: '#4ECDC4',
                        backgroundColor: 'rgba(78, 205, 196, 0.1)',
                        tension: 0.4
                    },
                    {
                        label: 'Купания',
                        data: history.map(day => day.baths).reverse(),
                        borderColor: '#45B7D1',
                        backgroundColor: 'rgba(69, 183, 209, 0.1)',
                        tension: 0.4
                    },
                    {
                        label: 'Активности',
                        data: history.map(day => day.activities).reverse(),
                        borderColor: '#96CEB4',
                        backgroundColor: 'rgba(150, 206, 180, 0.1)',
                        tension: 0.4
                    }
                ]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'top',
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    }
                }
            }
        });
    }

    showEventModal(action) {
        const modal = document.getElementById('event-modal');
        const title = document.getElementById('modal-title');
        const author = document.getElementById('event-author');
        const activityGroup = document.getElementById('activity-type-group');
        
        // Устанавливаем заголовок
        const titles = {
            feeding: 'Добавить кормление',
            diaper: 'Смена подгузника',
            bath: 'Добавить купание',
            activity: 'Добавить активность',
            sleep: 'Управление сном'
        };
        
        title.textContent = titles[action] || 'Добавить событие';
        author.value = this.currentUser.name;
        
        // Показываем/скрываем поле типа активности
        if (action === 'activity') {
            activityGroup.style.display = 'block';
        } else {
            activityGroup.style.display = 'none';
        }
        
        // Устанавливаем текущее время
        document.getElementById('event-time').value = this.getCurrentDateTime();
        
        // Сохраняем тип действия
        modal.dataset.action = action;
        
        modal.classList.remove('hidden');
    }

    hideEventModal() {
        document.getElementById('event-modal').classList.add('hidden');
    }

    async saveEvent() {
        const modal = document.getElementById('event-modal');
        const action = modal.dataset.action;
        const time = document.getElementById('event-time').value;
        const activityType = document.getElementById('activity-type').value;
        
        if (!time) {
            alert('Пожалуйста, укажите время');
            return;
        }
        
        try {
            const eventData = {
                family_id: this.currentFamily.id,
                author_id: this.currentUser.id,
                author_name: this.currentUser.name,
                author_role: this.currentUser.role,
                timestamp: new Date(time).toISOString()
            };
            
            let endpoint = '';
            if (action === 'activity') {
                eventData.activity_type = activityType;
                endpoint = 'activities';
            } else {
                endpoint = action + 's';
            }
            
            const response = await fetch(`${window.APP_CONFIG.API_BASE_URL}/family/${this.currentFamily.id}/${endpoint}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(eventData)
            });
            
            if (!response.ok) {
                throw new Error('Ошибка сохранения события');
            }
            
            this.hideEventModal();
            await this.loadDashboardData();
            
            // Показываем уведомление
            this.showNotification('Событие добавлено!');
            
        } catch (error) {
            console.error('Ошибка сохранения события:', error);
            alert('Ошибка сохранения события. Попробуйте еще раз.');
        }
    }

    async toggleSleep() {
        try {
            const sleepCard = document.getElementById('sleep-card');
            const isActive = sleepCard.querySelector('.sleep-btn').classList.contains('active');
            
            if (isActive) {
                // Завершаем сон
                await fetch(`${window.APP_CONFIG.API_BASE_URL}/family/${this.currentFamily.id}/sleep/end`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        family_id: this.currentFamily.id,
                        author_id: this.currentUser.id,
                        author_name: this.currentUser.name,
                        author_role: this.currentUser.role
                    })
                });
            } else {
                // Начинаем сон
                await fetch(`${window.APP_CONFIG.API_BASE_URL}/family/${this.currentFamily.id}/sleep/start`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        family_id: this.currentFamily.id,
                        author_id: this.currentUser.id,
                        author_name: this.currentUser.name,
                        author_role: this.currentUser.role
                    })
                });
            }
            
            await this.loadDashboardData();
            this.showNotification(isActive ? 'Сон завершен!' : 'Сон начат!');
            
        } catch (error) {
            console.error('Ошибка управления сном:', error);
            alert('Ошибка управления сном. Попробуйте еще раз.');
        }
    }

    handleLogout() {
        localStorage.removeItem('babycarebot_user');
        localStorage.removeItem('babycarebot_family');
        this.currentUser = null;
        this.currentFamily = null;
        this.showLogin();
    }

    showLogin() {
        document.getElementById('login-screen').classList.remove('hidden');
        document.getElementById('dashboard-screen').classList.add('hidden');
    }

    showDashboard() {
        document.getElementById('login-screen').classList.add('hidden');
        document.getElementById('dashboard-screen').classList.remove('hidden');
        document.getElementById('user-name').textContent = this.currentUser.name;
    }

    showNotification(message) {
        // Создаем простое уведомление
        const notification = document.createElement('div');
        notification.className = 'notification';
        notification.textContent = message;
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }

    formatTimeAgo(timestamp) {
        const now = new Date();
        const time = new Date(timestamp);
        const diffMs = now - time;
        const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
        const diffMinutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
        
        if (diffHours > 0) {
            return `${diffHours}ч ${diffMinutes}м назад`;
        } else {
            return `${diffMinutes}м назад`;
        }
    }

    formatDuration(duration) {
        if (!duration) return '';
        return `${duration.hours}ч ${duration.minutes}м`;
    }

    getCurrentDateTime() {
        const now = new Date();
        const year = now.getFullYear();
        const month = String(now.getMonth() + 1).padStart(2, '0');
        const day = String(now.getDate()).padStart(2, '0');
        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');
        
        return `${year}-${month}-${day}T${hours}:${minutes}`;
    }
}

// Инициализация приложения
document.addEventListener('DOMContentLoaded', () => {
    new BabyCareBot();
});
