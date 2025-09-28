class HabitTracker {
    constructor() {
        this.baseUrl = '/api';
        this.currentTab = 'dashboard';
        this.habits = [];
        this.init();
    }

    init() {
        this.habitForm = document.getElementById('habit-form');
        this.habitsContainer = document.getElementById('habits-container');
        this.editModal = document.getElementById('edit-modal');
        this.editForm = document.getElementById('edit-form');
        this.initTabs();
        this.initEditModal();

        this.habitForm.addEventListener('submit', this.handleSubmit.bind(this));
        this.loadHabits();
    }

    initEditModal() {
        this.editForm.addEventListener('submit', this.handleEditSubmit.bind(this));
        document.getElementById('cancel-edit').addEventListener('click', () => {
            this.editModal.classList.remove('active');
        });

        // Close modal when clicking outside
        this.editModal.addEventListener('click', (e) => {
            if (e.target === this.editModal) {
                this.editModal.classList.remove('active');
            }
        });
    }

    initTabs() {
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.switchTab(e.target.dataset.tab);
            });
        });
    }

    switchTab(tabName) {
        document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
        document.getElementById(tabName).classList.add('active');

        this.currentTab = tabName;
        if (tabName === 'analytics') {
            this.initThresholdSlider();
            this.loadAnalytics();
        }
    }

    async initThresholdSlider() {
        const thresholdInput = document.getElementById('threshold-input');
        const quartileInput = document.getElementById('quartile-input');

        if (!thresholdInput || !quartileInput) return;

        // Load saved preferences
        await this.loadPreferences();

        // Add event listeners for real-time updates
        thresholdInput.addEventListener('change', () => this.saveAndUpdateAnalytics());
        quartileInput.addEventListener('change', () => this.saveAndUpdateAnalytics());
    }

    async loadPreferences() {
        try {
            const response = await fetch(`${this.baseUrl}/preferences`);
            if (response.ok) {
                const preferences = await response.json();
                document.getElementById('threshold-input').value = Math.round(preferences.struggle_threshold * 100);
                document.getElementById('quartile-input').value = Math.round(preferences.show_bottom_percent * 100);
            }
        } catch (error) {
            console.error('Failed to load preferences:', error);
        }
    }

    async saveAndUpdateAnalytics() {
        const threshold = document.getElementById('threshold-input').value / 100;
        const quartile = document.getElementById('quartile-input').value / 100;

        // Save preferences
        try {
            await fetch(`${this.baseUrl}/preferences`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    struggle_threshold: threshold,
                    show_bottom_percent: quartile
                })
            });

            // Reload struggled habits with new settings
            this.loadStruggledHabits(threshold, quartile);
        } catch (error) {
            console.error('Failed to save preferences:', error);
        }
    }

    async handleSubmit(e) {
        e.preventDefault();

        const nameInput = document.getElementById('habit-name');
        const periodicitySelect = document.getElementById('habit-periodicity');

        const name = nameInput.value.trim();
        const periodicity = periodicitySelect.value;

        if (!name || !periodicity) return;

        try {
            await this.createHabit(name, periodicity);
            nameInput.value = '';
            periodicitySelect.value = '';
            this.showMessage('Habit added successfully!', 'success');
            this.loadHabits();
        } catch (error) {
            this.showMessage('Error adding habit', 'error');
        }
    }

    async createHabit(name, periodicity) {
        const response = await fetch(`${this.baseUrl}/habits`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, periodicity })
        });

        if (!response.ok) throw new Error('Failed to create habit');
        return response.json();
    }

    async loadHabits() {
        try {
            const response = await fetch(`${this.baseUrl}/habits`);
            if (!response.ok) throw new Error('Failed to load habits');

            const habits = await response.json();
            this.renderHabits(habits);
        } catch (error) {
            this.habitsContainer.innerHTML = '<p class="error">Failed to load habits</p>';
        }
    }

    async renderHabits(habits) {
        this.habits = habits;
        if (habits.length === 0) {
            this.habitsContainer.innerHTML = '<p class="loading">No habits yet. Add your first habit above!</p>';
            return;
        }

        const habitsWithData = await Promise.all(habits.map(async habit => {
            const [streaks, completionStatus] = await Promise.all([
                this.getHabitStreaks(habit.id),
                this.getHabitCompletionStatus(habit.id)
            ]);
            return {
                ...habit,
                currentStreak: streaks.current_streak,
                isCompleted: completionStatus.completed
            };
        }));

        this.habitsContainer.innerHTML = habitsWithData.map(habit => `
            <div class="habit-item ${habit.isCompleted ? 'completed' : ''}">
                <div class="habit-info">
                    <h3>${this.escapeHtml(habit.name)}</h3>
                    <div class="periodicity">${habit.periodicity}</div>
                    <div class="streak-display">Current streak: ${habit.currentStreak}</div>
                    ${habit.isCompleted ? '<div class="completion-indicator">✓ Completed</div>' : ''}
                </div>
                <div class="habit-actions">
                    ${habit.isCompleted ? '' : `<button class="btn-complete" onclick="app.completeHabit(${habit.id})">Complete</button>`}
                    <button class="btn-edit" onclick="app.editHabit(${habit.id})">
                        Edit
                    </button>
                    <button class="btn-delete" onclick="app.deleteHabit(${habit.id})">
                        Delete
                    </button>
                </div>
            </div>
        `).join('');
    }

    async completeHabit(id) {
        try {
            const response = await fetch(`${this.baseUrl}/habits/${id}/checkoff`, {
                method: 'POST'
            });

            if (!response.ok) throw new Error('Failed to complete habit');
            this.showMessage('Habit completed!', 'success');
            this.loadHabits(); // Refresh the habits list to update UI
        } catch (error) {
            this.showMessage('Error completing habit', 'error');
        }
    }

    async deleteHabit(id) {
        if (!confirm('Are you sure you want to delete this habit?')) return;

        try {
            const response = await fetch(`${this.baseUrl}/habits/${id}`, {
                method: 'DELETE'
            });

            if (!response.ok) throw new Error('Failed to delete habit');
            this.showMessage('Habit deleted', 'success');
            this.loadHabits();
        } catch (error) {
            this.showMessage('Error deleting habit', 'error');
        }
    }

    showMessage(text, type) {
        const existing = document.querySelector('.success, .error');
        if (existing) existing.remove();

        const message = document.createElement('div');
        message.className = type;
        message.textContent = text;

        document.querySelector('.container').insertBefore(message, document.querySelector('main'));

        setTimeout(() => message.remove(), 3000);
    }

    async getHabitStreaks(habitId) {
        try {
            const response = await fetch(`${this.baseUrl}/analytics/habits/${habitId}/streaks`);
            return response.ok ? await response.json() : { current_streak: 0, longest_streak: 0 };
        } catch {
            return { current_streak: 0, longest_streak: 0 };
        }
    }

    async getHabitCompletionStatus(habitId) {
        try {
            const response = await fetch(`${this.baseUrl}/habits/${habitId}/completed`);
            return response.ok ? await response.json() : { completed: false };
        } catch {
            return { completed: false };
        }
    }

    async loadAnalytics() {
        await Promise.all([
            this.loadSummaryCards(),
            this.loadCompletionChart(),
            this.loadStruggledHabitsFromPreferences(),
            this.loadDayAnalysis()
        ]);
    }

    async loadStruggledHabitsFromPreferences() {
        // Use stored preferences (API will handle defaults)
        try {
            const struggled = await fetch(`${this.baseUrl}/analytics/habits/struggled`).then(r => r.json());
            this.renderStruggledHabits(struggled);
        } catch (error) {
            document.getElementById('struggled-habits').innerHTML = '<div class="insights-section"><h3>Struggled Habits</h3><p class="error">Failed to load data</p></div>';
        }
    }

    async loadSummaryCards() {
        try {
            const [habits, completionRates] = await Promise.all([
                fetch(`${this.baseUrl}/habits`).then(r => r.json()),
                fetch(`${this.baseUrl}/analytics/habits/completion-rates`).then(r => r.json())
            ]);

            const totalHabits = habits.length;
            const avgCompletion = completionRates.length > 0
                ? Math.round(completionRates.reduce((sum, h) => sum + h.completion_rate, 0) / completionRates.length * 100)
                : 0;

            const allStreaks = await Promise.all(habits.map(h => this.getHabitStreaks(h.id)));
            const longestStreak = Math.max(...allStreaks.map(s => s.longest_streak), 0);

            document.getElementById('summary-cards').innerHTML = `
                <div class="summary-card">
                    <div class="card-value">${totalHabits}</div>
                    <div class="card-label">Total Habits</div>
                </div>
                <div class="summary-card">
                    <div class="card-value">${avgCompletion}%</div>
                    <div class="card-label">Avg Completion</div>
                </div>
                <div class="summary-card">
                    <div class="card-value">${longestStreak}</div>
                    <div class="card-label">Longest Streak</div>
                </div>
            `;
        } catch {
            document.getElementById('summary-cards').innerHTML = '<p class="error">Failed to load summary</p>';
        }
    }

    async loadCompletionChart() {
        try {
            const rates = await fetch(`${this.baseUrl}/analytics/habits/completion-rates`).then(r => r.json());

            if (rates.length === 0) {
                document.getElementById('completion-chart').innerHTML = '<p class="loading">No data available</p>';
                return;
            }

            document.getElementById('completion-chart').innerHTML = rates.map(habit => {
                const percentage = Math.round(habit.completion_rate * 100);
                return `
                    <div class="chart-bar">
                        <div class="chart-label">${this.escapeHtml(habit.name)}</div>
                        <div class="chart-progress">
                            <div class="chart-fill" style="width: ${percentage}%"></div>
                        </div>
                        <div class="chart-value">${percentage}%</div>
                    </div>
                `;
            }).join('');
        } catch {
            document.getElementById('completion-chart').innerHTML = '<p class="error">Failed to load chart</p>';
        }
    }

    async loadStruggledHabits(threshold, quartile) {
        try {
            const struggled = await fetch(`${this.baseUrl}/analytics/habits/struggled?threshold=${threshold}&quartile=${quartile}`).then(r => r.json());
            this.renderStruggledHabits(struggled);
        } catch {
            document.getElementById('struggled-habits').innerHTML = '<div class="insights-section"><h3>Struggled Habits</h3><p class="error">Failed to load data</p></div>';
        }
    }

    renderStruggledHabits(struggled) {
        const container = document.getElementById('struggled-habits');
        if (struggled.length === 0) {
            container.innerHTML = '<div class="insights-section"><h3>Struggled Habits</h3><p>All habits are doing well!</p></div>';
            return;
        }

        container.innerHTML = `
            <div class="insights-section">
                <h3>Struggled Habits (Last 30 days)</h3>
                ${struggled.map(habit => `
                    <div class="struggled-item">
                        <span>${this.escapeHtml(habit.name)}</span>
                        <span>${Math.round(habit.completion_rate * 100)}%</span>
                    </div>
                `).join('')}
            </div>
        `;
    }

    async loadDayAnalysis() {
        try {
            const weeklyHabits = this.habits.filter(h => h.periodicity === 'weekly');
            if (weeklyHabits.length === 0) {
                document.getElementById('day-analysis').innerHTML = '<div class="insights-section"><h3>Day Analysis</h3><p>No weekly habits found</p></div>';
                return;
            }

            const analyses = await Promise.all(
                weeklyHabits.map(async habit => {
                    const analysis = await fetch(`${this.baseUrl}/analytics/habits/${habit.id}/best-worst-day`).then(r => r.json());
                    return { ...habit, ...analysis };
                })
            );

            document.getElementById('day-analysis').innerHTML = `
                <div class="insights-section">
                    <h3>Best & Worst Days (Weekly Habits)</h3>
                    ${analyses.map(habit => `
                        <div class="day-item">
                            <div>
                                <strong>${this.escapeHtml(habit.name)}</strong><br>
                                <small>Best: ${habit.best_day || 'N/A'} | Worst: ${habit.worst_day || 'N/A'}</small>
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
        } catch {
            document.getElementById('day-analysis').innerHTML = '<div class="insights-section"><h3>Day Analysis</h3><p class="error">Failed to load data</p></div>';
        }
    }

    editHabit(id) {
        const habit = this.habits.find(h => h.id === id);
        if (!habit) return;

        document.getElementById('edit-habit-id').value = habit.id;
        document.getElementById('edit-habit-name').value = habit.name;
        document.getElementById('edit-habit-periodicity').value = habit.periodicity.toLowerCase();
        this.editModal.classList.add('active');
    }

    async handleEditSubmit(e) {
        e.preventDefault();

        const id = document.getElementById('edit-habit-id').value;
        const name = document.getElementById('edit-habit-name').value.trim();
        const periodicity = document.getElementById('edit-habit-periodicity').value;

        if (!name || !periodicity) return;

        try {
            await this.updateHabit(id, name, periodicity);
            this.editModal.classList.remove('active');
            this.showMessage('Habit updated successfully!', 'success');
            this.loadHabits();
        } catch (error) {
            this.showMessage('Error updating habit', 'error');
        }
    }

    async updateHabit(id, name, periodicity) {
        const response = await fetch(`${this.baseUrl}/habits/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, periodicity })
        });

        if (!response.ok) throw new Error('Failed to update habit');
        return response.json();
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

const app = new HabitTracker();
