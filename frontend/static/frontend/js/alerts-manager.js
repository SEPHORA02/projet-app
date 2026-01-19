/**
 * Script pour mettre à jour les alertes en temps réel
 * Place ce fichier dans frontend/static/frontend/js/
 */

class AlertsManager {
    constructor(options = {}) {
        this.apiUrl = options.apiUrl || '/api/alerts/';
        this.statsUrl = options.statsUrl || '/api/alerts/stats/';
        this.pollInterval = options.pollInterval || 10000; // 10 secondes par défaut
        this.containerId = options.containerId || 'alertes-container';
        this.isPolling = false;
    }

    /**
     * Récupère les alertes depuis l'API Django
     */
    async fetchAlerts() {
        try {
            const response = await fetch(this.apiUrl);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error('Erreur lors de la récupération des alertes:', error);
            return { alerts: [], count: 0 };
        }
    }

    /**
     * Récupère les statistiques des alertes
     */
    async fetchStats() {
        try {
            const response = await fetch(this.statsUrl);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error('Erreur lors de la récupération des stats:', error);
            return {};
        }
    }

    /**
     * Affiche une alerte dans le DOM
     */
    renderAlert(alert) {
        const div = document.createElement('div');
        div.className = 'bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 hover:shadow-lg transition-all';
        div.style.borderLeft = `4px solid ${alert.style.border_color}`;
        div.id = `alert-${alert.id}`;

        const badgeStyle = `background-color: ${alert.style.bg_color}; color: ${alert.style.text_color}; border: 1px solid ${alert.style.border_color}`;
        const iconStyle = `color: ${alert.style.text_color}`;
        const bgStyle = `background-color: ${alert.style.bg_color}`;

        let sensorDataHtml = '';
        if (alert.sensor_data && Object.keys(alert.sensor_data).length > 0) {
            sensorDataHtml = `
                <details class="mb-3">
                    <summary class="cursor-pointer text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200">
                        Voir les données du capteur
                    </summary>
                    <div class="mt-2 grid grid-cols-2 sm:grid-cols-4 gap-2 text-sm">
                        ${alert.sensor_data.heartRate ? `<div class="bg-gray-50 dark:bg-gray-700 p-2 rounded">
                            <span class="text-gray-500 dark:text-gray-400">FC:</span>
                            <span class="text-dark dark:text-white font-medium">${alert.sensor_data.heartRate} bpm</span>
                        </div>` : ''}
                        ${alert.sensor_data.respiratoryRate ? `<div class="bg-gray-50 dark:bg-gray-700 p-2 rounded">
                            <span class="text-gray-500 dark:text-gray-400">FR:</span>
                            <span class="text-dark dark:text-white font-medium">${alert.sensor_data.respiratoryRate} /min</span>
                        </div>` : ''}
                        ${alert.sensor_data.bodyTemperature ? `<div class="bg-gray-50 dark:bg-gray-700 p-2 rounded">
                            <span class="text-gray-500 dark:text-gray-400">Temp:</span>
                            <span class="text-dark dark:text-white font-medium">${alert.sensor_data.bodyTemperature}°C</span>
                        </div>` : ''}
                        ${alert.sensor_data.co2 ? `<div class="bg-gray-50 dark:bg-gray-700 p-2 rounded">
                            <span class="text-gray-500 dark:text-gray-400">CO₂:</span>
                            <span class="text-dark dark:text-white font-medium">${alert.sensor_data.co2} ppm</span>
                        </div>` : ''}
                    </div>
                </details>
            `;
        }

        let recommendationsHtml = '';
        if (alert.recommendations && alert.recommendations.length > 0) {
            recommendationsHtml = `
                <div class="mb-3">
                    <p class="text-gray-600 dark:text-gray-300 font-medium mb-2">Recommandations :</p>
                    <ul class="list-disc list-inside text-gray-600 dark:text-gray-300 space-y-1">
                        ${alert.recommendations.map(r => `<li>${r}</li>`).join('')}
                    </ul>
                </div>
            `;
        }

        div.innerHTML = `
            <div class="p-6">
                <div class="flex items-start gap-4">
                    <!-- Icône -->
                    <div class="w-12 h-12 rounded-lg flex items-center justify-center" style="${bgStyle}">
                        <i data-lucide="${alert.style.icon}" class="w-6 h-6" style="${iconStyle}"></i>
                    </div>

                    <!-- Contenu -->
                    <div class="flex-1 min-w-0">
                        <div class="flex flex-col sm:flex-row sm:items-start justify-between gap-2 sm:gap-4 mb-2">
                            <h3 class="text-dark dark:text-white font-semibold">${alert.message}</h3>
                            <span class="px-3 py-1 rounded-full text-sm flex items-center gap-1 w-fit" style="${badgeStyle}">
                                <i data-lucide="${alert.badge.icon}" class="w-3 h-3"></i>
                                ${alert.badge.text}
                            </span>
                        </div>

                        ${recommendationsHtml}
                        ${sensorDataHtml}

                        <div class="flex items-center gap-2 text-gray-500 dark:text-gray-400 mb-3">
                            <i data-lucide="clock" class="w-4 h-4"></i>
                            <span>${alert.time_ago}</span>
                            ${alert.ai_analysis && alert.ai_analysis.confidence ? `
                                <span class="ml-4 text-xs">
                                    Confiance IA: ${Math.round(alert.ai_analysis.confidence * 100)}%
                                </span>
                            ` : ''}
                        </div>

                        <div class="flex gap-2">
                            <button onclick="alertsManager.markAsRead(${alert.id})" 
                                    class="px-3 py-1 text-sm bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 rounded hover:bg-blue-200 dark:hover:bg-blue-800 transition">
                                Marquer comme lu
                            </button>
                            <button onclick="alertsManager.dismissAlert(${alert.id})" 
                                    class="px-3 py-1 text-sm bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded hover:bg-gray-200 dark:hover:bg-gray-600 transition">
                                Masquer
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        return div;
    }

    /**
     * Met à jour l'affichage des alertes
     */
    async updateAlerts() {
        const data = await this.fetchAlerts();
        const container = document.getElementById(this.containerId);

        if (!container) {
            console.warn(`Conteneur ${this.containerId} non trouvé`);
            return;
        }

        if (!data.alerts || data.alerts.length === 0) {
            container.innerHTML = `
                <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-12 text-center">
                    <i data-lucide="bell-off" class="w-16 h-16 mx-auto mb-4 text-gray-400"></i>
                    <h3 class="text-dark dark:text-white font-semibold mb-2">Aucune alerte</h3>
                    <p class="text-gray-500 dark:text-gray-400">Aucune alerte n'a été reçue pour le moment.</p>
                </div>
            `;
        } else {
            container.innerHTML = '';
            data.alerts.forEach(alert => {
                container.appendChild(this.renderAlert(alert));
            });
        }

        // Réinitialiser les icônes Lucide
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
    }

    /**
     * Met à jour les statistiques
     */
    async updateStats() {
        const stats = await this.fetchStats();

        // Mettre à jour le badge total
        const totalBadge = document.querySelector('[data-stat="total"]');
        if (totalBadge) {
            totalBadge.textContent = stats.total || 0;
        }

        // Mettre à jour les statistiques des colonnes
        const attentionElement = document.querySelector('[data-stat="attention"]');
        if (attentionElement) {
            attentionElement.textContent = (stats.critical || 0) + (stats.high || 0);
        }

        const infoElement = document.querySelector('[data-stat="info"]');
        if (infoElement) {
            infoElement.textContent = stats.low || 0;
        }

        const improvementElement = document.querySelector('[data-stat="improvement"]');
        if (improvementElement) {
            improvementElement.textContent = stats.by_type?.info || 0;
        }
    }

    /**
     * Marquer une alerte comme lue
     */
    async markAsRead(alertId) {
        try {
            const response = await fetch(`/api/alerts/${alertId}/read/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCsrfToken(),
                }
            });
            if (response.ok) {
                await this.updateAlerts();
                await this.updateStats();
            }
        } catch (error) {
            console.error('Erreur lors du marquage:', error);
        }
    }

    /**
     * Masquer une alerte
     */
    async dismissAlert(alertId) {
        try {
            const response = await fetch(`/api/alerts/${alertId}/dismiss/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCsrfToken(),
                }
            });
            if (response.ok) {
                const alertElement = document.getElementById(`alert-${alertId}`);
                if (alertElement) {
                    alertElement.style.opacity = '0';
                    setTimeout(() => alertElement.remove(), 300);
                }
                await this.updateStats();
            }
        } catch (error) {
            console.error('Erreur lors du masquage:', error);
        }
    }

    /**
     * Obtenir le token CSRF
     */
    getCsrfToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    }

    /**
     * Démarrer le polling
     */
    startPolling() {
        if (this.isPolling) return;
        this.isPolling = true;

        // Mise à jour immédiate
        this.updateAlerts();
        this.updateStats();

        // Polling régulier
        this.pollInterval = setInterval(async () => {
            await this.updateAlerts();
            await this.updateStats();
        }, this.pollInterval);

        console.log('Polling des alertes démarré');
    }

    /**
     * Arrêter le polling
     */
    stopPolling() {
        if (this.isPolling && this.pollInterval) {
            clearInterval(this.pollInterval);
            this.isPolling = false;
            console.log('Polling des alertes arrêté');
        }
    }
}

// Créer une instance globale
let alertsManager;

// Initialiser au chargement du DOM
document.addEventListener('DOMContentLoaded', function() {
    alertsManager = new AlertsManager({
        apiUrl: '/api/alerts/',
        statsUrl: '/api/alerts/stats/',
        pollInterval: 10000, // 10 secondes
        containerId: 'alertes-container'
    });

    // Démarrer le polling
    alertsManager.startPolling();

    // Arrêter le polling quand la page est fermée
    window.addEventListener('beforeunload', () => {
        alertsManager.stopPolling();
    });
});
