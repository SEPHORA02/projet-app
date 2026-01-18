// ============================================
// Dashboard ESP8266 - Gestion de l'affichage
// ============================================

class ESP8266Dashboard {
    constructor() {
        this.isConnected = false;
        this.updateInterval = null;
        this.init();
    }

    // Initialisation
    init() {
        console.log('[Dashboard] Initialisation...');
        this.testConnection();
        this.startAutoUpdate();
    }

    // Test de connexion initial
    async testConnection() {
        try {
            const url = `${ESP8266_CONFIG.baseUrl}/ping`;
            console.log('[Dashboard] Test de connexion vers:', url);
            
            const response = await fetch(url, { 
                method: 'GET',
                mode: 'cors',
                cache: 'no-cache'
            });
            
            if (response.ok) {
                const data = await response.json();
                console.log('[Dashboard] API ESP8266 initialisée et prête à l\'emploi.', data);
                this.isConnected = true;
                this.updateConnectionStatus(true);
                // Première récupération des données
                await this.fetchAndUpdateData();
            }
        } catch (error) {
            console.error('[Dashboard] Impossible de se connecter à l\'ESP8266', error);
            this.isConnected = false;
            this.updateConnectionStatus(false);
        }
    }

    // Récupérer et mettre à jour toutes les données
    async fetchAndUpdateData() {
        try {
            const url = `${ESP8266_CONFIG.baseUrl}${ESP8266_CONFIG.endpoints.sensors}`;
            console.log('[Dashboard] Récupération des données depuis:', url);
            
            const response = await fetch(url, {
                method: 'GET',
                mode: 'cors',
                cache: 'no-cache'
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            console.log('[Dashboard] Données reçues:', data);

            // Mettre à jour l'interface avec les nouvelles données
            this.updateUI(data);
            
            // Marquer comme connecté
            if (!this.isConnected) {
                this.isConnected = true;
                this.updateConnectionStatus(true);
            }

        } catch (error) {
            console.error('[Dashboard] Erreur lors de la récupération des données:', error);
            this.isConnected = false;
            this.updateConnectionStatus(false);
        }
    }

    // Mettre à jour l'interface utilisateur
    updateUI(data) {
        // Rythme cardiaque
        this.updateElement('heart-rate-value', data.heartRate);
        this.updateElement('heart-rate-desc', this.getHeartRateDesc(data.heartRate));

        // Température corporelle
        this.updateElement('body-temp-value', data.bodyTemperature.toFixed(1));
        this.updateElement('body-temp-desc', this.getBodyTempDesc(data.bodyTemperature));

        // Fréquence respiratoire
        this.updateElement('resp-rate-value', data.respiratoryRate);
        this.updateElement('resp-rate-desc', this.getRespRateDesc(data.respiratoryRate));

        // Température ambiante
        this.updateElement('ambient-temp-value', data.ambientTemperature);
        this.updateElement('ambient-temp-desc', this.getAmbientTempDesc(data.ambientTemperature));

        // Humidité
        this.updateElement('humidity-value', data.humidity);
        this.updateElement('humidity-desc', this.getHumidityDesc(data.humidity));

        // Qualité de l'air (CO2)
        this.updateElement('air-quality-value', data.co2);
        this.updateElement('air-quality-desc', this.getAirQualityDesc(data.co2));

        // Niveau de risque
        this.updateRiskLevel(data.riskLevel);
    }

    // Mettre à jour le niveau de risque
    updateRiskLevel(riskLevel) {
        // Valeur numérique
        this.updateElement('risk-value', riskLevel);

        // Label et couleur
        const riskInfo = this.getRiskInfo(riskLevel);
        const labelElement = document.querySelector('[data-sensor="risk-label"]');
        if (labelElement) {
            labelElement.textContent = riskInfo.label;
            labelElement.style.backgroundColor = riskInfo.bgColor;
            labelElement.style.color = riskInfo.color;
            labelElement.style.border = `2px solid ${riskInfo.color}`;
        }

        // Valeur avec couleur
        const valueElement = document.querySelector('[data-sensor="risk-value"]');
        if (valueElement) {
            valueElement.style.color = riskInfo.color;
        }

        // Description
        this.updateElement('risk-desc', riskInfo.description);

        // Jauge circulaire (circumference = 2 * π * r = 2 * π * 80 ≈ 502.65)
        const circumference = 502.65;
        const offset = circumference - (riskLevel / 100) * circumference;
        const gaugeElement = document.querySelector('[data-sensor="risk-gauge"]');
        if (gaugeElement) {
            gaugeElement.setAttribute('stroke-dashoffset', offset);
            gaugeElement.setAttribute('stroke', riskInfo.color);
        }
    }

    // Obtenir les informations de risque
    getRiskInfo(riskLevel) {
        if (riskLevel <= 30) {
            return {
                label: 'Risque faible',
                color: '#22C58E',
                bgColor: '#d4f4e8',
                description: 'Votre environnement est optimal. Continuez à maintenir ces bonnes conditions pour votre santé respiratoire.'
            };
        } else if (riskLevel <= 60) {
            return {
                label: 'Risque modéré',
                color: '#FF9F43',
                bgColor: '#f4e2d1',
                description: 'Votre environnement est globalement favorable. Quelques ajustements sont recommandés pour optimiser votre confort respiratoire.'
            };
        } else {
            return {
                label: 'Risque élevé',
                color: '#EF4444',
                bgColor: '#fdd9d9',
                description: 'Attention ! Votre environnement présente des conditions défavorables. Des actions correctives sont fortement recommandées.'
            };
        }
    }

    // Descriptions pour chaque capteur
    getHeartRateDesc(value) {
        if (value < 60) return 'Fréquence cardiaque basse';
        if (value > 100) return 'Fréquence cardiaque élevée';
        return 'Fréquence cardiaque normale';
    }

    getBodyTempDesc(value) {
        if (value < 36.0) return 'Température basse';
        if (value > 37.5) return 'Température élevée';
        return 'Température optimale';
    }

    getRespRateDesc(value) {
        if (value < 12) return 'Respiration lente';
        if (value > 20) return 'Respiration rapide';
        return 'Respiration stable';
    }

    getAmbientTempDesc(value) {
        if (value < 18) return 'Environnement froid';
        if (value > 26) return 'Environnement chaud';
        return 'Environnement confortable';
    }

    getHumidityDesc(value) {
        if (value < 30) return 'Air trop sec';
        if (value > 70) return 'Air trop humide';
        return 'Niveau idéal';
    }

    getAirQualityDesc(value) {
        if (value > 800) return 'Air de mauvaise qualité';
        if (value > 600) return 'Qualité d\'air moyenne';
        return 'Air sain';
    }

    // Mettre à jour un élément du DOM
    updateElement(sensorName, value) {
        const element = document.querySelector(`[data-sensor="${sensorName}"]`);
        if (element) {
            element.textContent = value;
        }
    }

    // Mettre à jour le statut de connexion
    updateConnectionStatus(isConnected) {
        const indicator = document.getElementById('status-indicator');
        const text = document.getElementById('status-text');
        
        if (isConnected) {
            indicator.className = 'w-2 h-2 rounded-full bg-green-500 animate-pulse';
            text.textContent = 'Connecté';
            text.className = 'text-sm text-green-600 dark:text-green-400';
        } else {
            indicator.className = 'w-2 h-2 rounded-full bg-red-500';
            text.textContent = 'Déconnecté';
            text.className = 'text-sm text-red-600 dark:text-red-400';
        }
    }

    // Démarrer la mise à jour automatique
    startAutoUpdate() {
        console.log(`[Dashboard] Mise à jour automatique toutes les ${ESP8266_CONFIG.refreshInterval / 1000} secondes`);
        
        // Mettre à jour périodiquement
        this.updateInterval = setInterval(() => {
            this.fetchAndUpdateData();
        }, ESP8266_CONFIG.refreshInterval);
    }

    // Arrêter la mise à jour automatique
    stopAutoUpdate() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
            console.log('[Dashboard] Mise à jour automatique arrêtée');
        }
    }
}

// Initialiser le dashboard au chargement de la page
let dashboard;

document.addEventListener('DOMContentLoaded', () => {
    console.log('[Dashboard] Page chargée, démarrage du dashboard...');
    dashboard = new ESP8266Dashboard();
});

// Nettoyer lors de la fermeture de la page
window.addEventListener('beforeunload', () => {
    if (dashboard) {
        dashboard.stopAutoUpdate();
    }
});

// Exposer l'instance pour le débogage
window.ESP8266Dashboard = dashboard;