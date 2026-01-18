// ============================================
// Configuration de l'API ESP8266
// ============================================

const ESP8266_CONFIG = {
    // Remplacez par l'adresse IP de votre ESP8266
    baseUrl: 'http://192.168.137.223',
    
    // Endpoints de votre ESP8266
    endpoints: {
        sensors: '/api/sensors',      // Toutes les données des capteurs
        heartRate: '/api/heart',       // Rythme cardiaque
        temperature: '/api/temp',      // Températures
        respiratory: '/api/resp',      // Fréquence respiratoire
        environment: '/api/env',       // Environnement (humidité, CO2)
        riskLevel: '/api/risk'         // Niveau de risque calculé
    },
    
    // Intervalle de rafraîchissement (en millisecondes)
    refreshInterval: 5000, // 5 secondes
    
    // Timeout pour les requêtes
    timeout: 3000 // 3 secondes
};

// ============================================
// Classe principale de l'API
// ============================================

class ESP8266DashboardAPI {
    constructor(config) {
        this.config = config;
        this.isConnected = false;
        this.intervalId = null;
        this.errorCount = 0;
        this.maxErrors = 3;
    }

    // Méthode générique pour faire des requêtes avec timeout
    async fetchWithTimeout(url, timeout = this.config.timeout) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), timeout);

        try {
            const response = await fetch(url, {
                signal: controller.signal,
                headers: {
                    'Accept': 'application/json'
                }
            });
            clearTimeout(timeoutId);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            clearTimeout(timeoutId);
            if (error.name === 'AbortError') {
                throw new Error('Timeout: ESP8266 ne répond pas');
            }
            throw error;
        }
    }

    // Récupérer toutes les données des capteurs
    async getAllSensorsData() {
        try {
            const url = `${this.config.baseUrl}${this.config.endpoints.sensors}`;
            const data = await this.fetchWithTimeout(url);
            this.isConnected = true;
            this.errorCount = 0;
            return data;
        } catch (error) {
            this.handleError('getAllSensorsData', error);
            return null;
        }
    }

    // Récupérer le rythme cardiaque
    async getHeartRate() {
        try {
            const url = `${this.config.baseUrl}${this.config.endpoints.heartRate}`;
            const data = await this.fetchWithTimeout(url);
            return data;
        } catch (error) {
            this.handleError('getHeartRate', error);
            return null;
        }
    }

    // Récupérer les températures
    async getTemperatures() {
        try {
            const url = `${this.config.baseUrl}${this.config.endpoints.temperature}`;
            const data = await this.fetchWithTimeout(url);
            return data;
        } catch (error) {
            this.handleError('getTemperatures', error);
            return null;
        }
    }

    // Récupérer la fréquence respiratoire
    async getRespiratoryRate() {
        try {
            const url = `${this.config.baseUrl}${this.config.endpoints.respiratory}`;
            const data = await this.fetchWithTimeout(url);
            return data;
        } catch (error) {
            this.handleError('getRespiratoryRate', error);
            return null;
        }
    }

    // Récupérer les données environnementales
    async getEnvironmentData() {
        try {
            const url = `${this.config.baseUrl}${this.config.endpoints.environment}`;
            const data = await this.fetchWithTimeout(url);
            return data;
        } catch (error) {
            this.handleError('getEnvironmentData', error);
            return null;
        }
    }

    // Récupérer le niveau de risque
    async getRiskLevel() {
        try {
            const url = `${this.config.baseUrl}${this.config.endpoints.riskLevel}`;
            const data = await this.fetchWithTimeout(url);
            return data;
        } catch (error) {
            this.handleError('getRiskLevel', error);
            return null;
        }
    }

    // Gérer les erreurs
    handleError(method, error) {
        console.error(`[ESP8266 API] Erreur dans ${method}:`, error.message);
        this.errorCount++;
        
        if (this.errorCount >= this.maxErrors) {
            this.isConnected = false;
            this.showConnectionError();
        }
    }

    // Afficher une erreur de connexion
    showConnectionError() {
        const alertDiv = document.createElement('div');
        alertDiv.className = 'fixed top-4 right-4 bg-red-500 text-white px-6 py-4 rounded-lg shadow-lg z-50';
        alertDiv.innerHTML = `
            <div class="flex items-center gap-3">
                <i data-lucide="wifi-off" class="w-5 h-5"></i>
                <div>
                    <div class="font-semibold">Connexion perdue</div>
                    <div class="text-sm">Impossible de contacter l'ESP8266</div>
                </div>
            </div>
        `;
        document.body.appendChild(alertDiv);
        
        // Initialiser l'icône Lucide
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
        
        setTimeout(() => alertDiv.remove(), 5000);
    }

    // Démarrer la mise à jour automatique
    startAutoRefresh(callback) {
        this.stopAutoRefresh(); // Arrêter l'ancien intervalle s'il existe
        
        // Première mise à jour immédiate
        callback();
        
        // Puis mise à jour périodique
        this.intervalId = setInterval(() => {
            callback();
        }, this.config.refreshInterval);
        
        console.log(`[ESP8266 API] Auto-refresh démarré (${this.config.refreshInterval}ms)`);
    }

    // Arrêter la mise à jour automatique
    stopAutoRefresh() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
            console.log('[ESP8266 API] Auto-refresh arrêté');
        }
    }

    // Vérifier la connexion
    async checkConnection() {
        try {
            const url = `${this.config.baseUrl}/ping`;
            await this.fetchWithTimeout(url, 2000);
            this.isConnected = true;
            this.errorCount = 0;
            return true;
        } catch (error) {
            this.isConnected = false;
            return false;
        }
    }
}

// ============================================
// Intégration avec le Dashboard
// ============================================

class DashboardController {
    constructor(api) {
        this.api = api;
        this.elements = {};
        this.initElements();
    }

    // Initialiser les références aux éléments DOM
    initElements() {
        this.elements = {
            // Valeurs
            heartRate: document.querySelector('[data-sensor="heart-rate-value"]'),
            bodyTemp: document.querySelector('[data-sensor="body-temp-value"]'),
            respRate: document.querySelector('[data-sensor="resp-rate-value"]'),
            ambientTemp: document.querySelector('[data-sensor="ambient-temp-value"]'),
            humidity: document.querySelector('[data-sensor="humidity-value"]'),
            airQuality: document.querySelector('[data-sensor="air-quality-value"]'),
            
            // Descriptions
            heartRateDesc: document.querySelector('[data-sensor="heart-rate-desc"]'),
            bodyTempDesc: document.querySelector('[data-sensor="body-temp-desc"]'),
            respRateDesc: document.querySelector('[data-sensor="resp-rate-desc"]'),
            ambientTempDesc: document.querySelector('[data-sensor="ambient-temp-desc"]'),
            humidityDesc: document.querySelector('[data-sensor="humidity-desc"]'),
            airQualityDesc: document.querySelector('[data-sensor="air-quality-desc"]'),
            
            // Jauge de risque
            riskValue: document.querySelector('[data-sensor="risk-value"]'),
            riskLabel: document.querySelector('[data-sensor="risk-label"]'),
            riskDesc: document.querySelector('[data-sensor="risk-desc"]'),
            riskGauge: document.querySelector('[data-sensor="risk-gauge"]')
        };
    }

    // Mettre à jour toutes les données
    async updateAllData() {
        const data = await this.api.getAllSensorsData();
        
        if (!data) {
            console.warn('[Dashboard] Aucune donnée reçue de l\'ESP8266');
            return;
        }

        this.updateHeartRate(data.heartRate);
        this.updateBodyTemperature(data.bodyTemperature);
        this.updateRespiratoryRate(data.respiratoryRate);
        this.updateAmbientTemperature(data.ambientTemperature);
        this.updateHumidity(data.humidity);
        this.updateAirQuality(data.co2);
        this.updateRiskLevel(data.riskLevel);
    }

    // Mettre à jour le rythme cardiaque
    updateHeartRate(value) {
        if (this.elements.heartRate) {
            this.elements.heartRate.textContent = value;
        }
        if (this.elements.heartRateDesc) {
            this.elements.heartRateDesc.textContent = this.getHeartRateStatus(value);
        }
    }

    // Mettre à jour la température corporelle
    updateBodyTemperature(value) {
        if (this.elements.bodyTemp) {
            this.elements.bodyTemp.textContent = value.toFixed(1);
        }
        if (this.elements.bodyTempDesc) {
            this.elements.bodyTempDesc.textContent = this.getBodyTempStatus(value);
        }
    }

    // Mettre à jour la fréquence respiratoire
    updateRespiratoryRate(value) {
        if (this.elements.respRate) {
            this.elements.respRate.textContent = value;
        }
        if (this.elements.respRateDesc) {
            this.elements.respRateDesc.textContent = this.getRespRateStatus(value);
        }
    }

    // Mettre à jour la température ambiante
    updateAmbientTemperature(value) {
        if (this.elements.ambientTemp) {
            this.elements.ambientTemp.textContent = value;
        }
        if (this.elements.ambientTempDesc) {
            this.elements.ambientTempDesc.textContent = this.getAmbientTempStatus(value);
        }
    }

    // Mettre à jour l'humidité
    updateHumidity(value) {
        if (this.elements.humidity) {
            this.elements.humidity.textContent = value;
        }
        if (this.elements.humidityDesc) {
            this.elements.humidityDesc.textContent = this.getHumidityStatus(value);
        }
    }

    // Mettre à jour la qualité de l'air
    updateAirQuality(value) {
        if (this.elements.airQuality) {
            this.elements.airQuality.textContent = value;
        }
        if (this.elements.airQualityDesc) {
            this.elements.airQualityDesc.textContent = this.getAirQualityStatus(value);
        }
    }

    // Mettre à jour le niveau de risque
    updateRiskLevel(value) {
        if (this.elements.riskValue) {
            this.elements.riskValue.textContent = value;
        }
        
        const riskData = this.getRiskData(value);
        
        if (this.elements.riskLabel) {
            this.elements.riskLabel.textContent = riskData.label;
            this.elements.riskLabel.style.backgroundColor = riskData.bgColor;
            this.elements.riskLabel.style.color = riskData.color;
            this.elements.riskLabel.style.borderColor = riskData.color;
        }
        
        if (this.elements.riskDesc) {
            this.elements.riskDesc.textContent = riskData.description;
        }
        
        if (this.elements.riskGauge) {
            this.updateGauge(value, riskData.color);
        }
    }

    // Mettre à jour la jauge circulaire
    updateGauge(value, color) {
        const circumference = 502.65;
        const offset = circumference - (value / 100) * circumference;
        
        if (this.elements.riskGauge) {
            this.elements.riskGauge.style.strokeDashoffset = offset;
            this.elements.riskGauge.style.stroke = color;
        }
        
        if (this.elements.riskValue) {
            this.elements.riskValue.style.color = color;
        }
    }

    // Fonctions de détermination du statut
    getHeartRateStatus(value) {
        if (value < 60) return 'Bradycardie - Consultez un médecin';
        if (value > 100) return 'Tachycardie - Repos recommandé';
        return 'Fréquence cardiaque normale';
    }

    getBodyTempStatus(value) {
        if (value < 36) return 'Hypothermie légère';
        if (value > 37.5) return 'Fièvre détectée';
        return 'Température optimale';
    }

    getRespRateStatus(value) {
        if (value < 12) return 'Respiration lente';
        if (value > 20) return 'Respiration rapide';
        return 'Respiration stable';
    }

    getAmbientTempStatus(value) {
        if (value < 18) return 'Environnement froid';
        if (value > 26) return 'Environnement chaud';
        return 'Environnement confortable';
    }

    getHumidityStatus(value) {
        if (value < 30) return 'Air trop sec';
        if (value > 70) return 'Air trop humide';
        return 'Niveau idéal';
    }

    getAirQualityStatus(value) {
        if (value < 400) return 'Air excellent';
        if (value < 800) return 'Air sain';
        if (value < 1200) return 'Air moyen';
        return 'Air de mauvaise qualité';
    }

    getRiskData(value) {
        if (value < 30) {
            return {
                label: 'Risque faible',
                color: '#22C58E',
                bgColor: '#d4f4e8',
                description: 'Votre environnement est optimal pour votre santé respiratoire. Continuez ainsi!'
            };
        } else if (value < 60) {
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
                bgColor: '#fdd8d8',
                description: 'Attention! Votre environnement présente des conditions défavorables. Prenez des mesures immédiates.'
            };
        }
    }
}

// ============================================
// Initialisation
// ============================================

// Créer l'instance de l'API
const esp8266API = new ESP8266DashboardAPI(ESP8266_CONFIG);

// Créer le contrôleur du dashboard
const dashboardController = new DashboardController(esp8266API);

// Démarrer la mise à jour automatique au chargement de la page
document.addEventListener('DOMContentLoaded', () => {
    console.log('[Dashboard] Initialisation...');
    
    // Vérifier la connexion
    esp8266API.checkConnection().then(connected => {
        if (connected) {
            console.log('[Dashboard] Connecté à l\'ESP8266');
            
            // Démarrer les mises à jour automatiques
            esp8266API.startAutoRefresh(() => {
                dashboardController.updateAllData();
            });
        } else {
            console.error('[Dashboard] Impossible de se connecter à l\'ESP8266');
            esp8266API.showConnectionError();
        }
    });
});

// Arrêter les mises à jour quand l'utilisateur quitte la page
window.addEventListener('beforeunload', () => {
    esp8266API.stopAutoRefresh();
});

// Export pour utilisation globale
window.ESP8266API = {
    api: esp8266API,
    controller: dashboardController,
    config: ESP8266_CONFIG
};
console.log('[Dashboard] API ESP8266 initialisée et prête à l\'emploi.');
console.log(ESP8266_CONFIG);