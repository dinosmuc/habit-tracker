class HabitTracker {
    constructor() {
        this.baseUrl = '/api';
        this.init();
    }

    init() {
        this.habitForm = document.getElementById('habit-form');
        this.habitsContainer = document.getElementById('habits-container');

        this.habitForm.addEventListener('submit', this.handleSubmit.bind(this));
        this.loadHabits();
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

    renderHabits(habits) {
        if (habits.length === 0) {
            this.habitsContainer.innerHTML = '<p class="loading">No habits yet. Add your first habit above!</p>';
            return;
        }

        this.habitsContainer.innerHTML = habits.map(habit => `
            <div class="habit-item">
                <div class="habit-info">
                    <h3>${this.escapeHtml(habit.name)}</h3>
                    <div class="periodicity">${habit.periodicity}</div>
                </div>
                <div class="habit-actions">
                    <button class="btn-complete" onclick="app.completeHabit(${habit.id})">
                        Complete
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

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

const app = new HabitTracker();
