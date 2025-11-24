from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Patient(models.Model):
    """Modèle pour les informations du patient"""

    SEXE_CHOIX = [
        ('H', 'Homme'),
        ('F', 'Femme'),
        ('A', 'Autre'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profil_patient',
        verbose_name="Compte utilisateur",
    )
    age = models.IntegerField(verbose_name="Âge", default=18)
    location = models.CharField(max_length=200, verbose_name="Localisation", default="Abidjan, Côte d'Ivoire")
    health_profile = models.TextField(
        verbose_name="Profil de santé",
        default="Asthme chronique - Surveillance intelligente et alertes préventives personnalisées",
    )
    connected_sensors = models.IntegerField(default=3, verbose_name="Capteurs connectés")
    max_sensors = models.IntegerField(default=3, verbose_name="Capteurs maximum")
    is_active = models.BooleanField(default=True, verbose_name="Surveillance active")
    phone_number = models.CharField(max_length=20, verbose_name="Numéro", blank=True)
    sex = models.CharField(max_length=1, choices=SEXE_CHOIX, verbose_name="Sexe", blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Mis à jour le")

    class Meta:
        verbose_name = "Patient"
        verbose_name_plural = "Patients"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username}"

    @property
    def sensors_status(self):
        return f"{self.connected_sensors}/{self.max_sensors}"

    @property
    def localisation(self):
        return self.location

    @property
    def profil_sante(self):
        return self.health_profile

    @property
    def statut_capteurs(self):
        return self.sensors_status


class PhysiologicalData(models.Model):
    """Modèle pour les données physiologiques du patient"""

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='physiological_data')
    heart_rate = models.IntegerField(verbose_name="Rythme cardiaque (bpm)", default=72)
    oxygen_saturation = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="Saturation O₂ (%)",
        default=98.0,
    )
    temperature = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        verbose_name="Température (°C)",
        default=36.8,
    )
    recorded_at = models.DateTimeField(default=timezone.now, verbose_name="Date d'enregistrement")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")

    class Meta:
        verbose_name = "Donnée physiologique"
        verbose_name_plural = "Données physiologiques"
        ordering = ['-recorded_at']

    def __str__(self):
        horodatage = self.recorded_at.strftime('%Y-%m-%d %H:%M')
        return f"Données physiologiques - {self.patient} - {horodatage}"


class EnvironmentalData(models.Model):
    """Modèle pour les données environnementales"""

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='environmental_data')
    air_quality_index = models.IntegerField(verbose_name="Indice AQI", default=42)
    co2_level = models.IntegerField(verbose_name="Niveau CO₂ (ppm)", default=420)
    humidity = models.IntegerField(verbose_name="Humidité (%)", default=55)
    pm25 = models.IntegerField(verbose_name="Particules PM2.5 (µg/m³)", default=12)
    co_level = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="CO (ppm)",
        default=0.3,
    )
    no2_level = models.IntegerField(verbose_name="NO₂ (ppb)", default=18)
    o3_level = models.IntegerField(verbose_name="O₃ (ppb)", default=35)
    recorded_at = models.DateTimeField(default=timezone.now, verbose_name="Date d'enregistrement")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")

    class Meta:
        verbose_name = "Donnée environnementale"
        verbose_name_plural = "Données environnementales"
        ordering = ['-recorded_at']

    def __str__(self):
        horodatage = self.recorded_at.strftime('%Y-%m-%d %H:%M')
        return f"Données environnementales - {self.patient} - {horodatage}"


class Alert(models.Model):
    """Modèle pour les alertes et notifications"""

    ALERT_LEVELS = [
        ('low', 'Basse'),
        ('medium', 'Moyenne'),
        ('high', 'Haute'),
        ('critical', 'Critique'),
    ]

    ALERT_TYPES = [
        ('info', 'Information'),
        ('success', 'Succès'),
        ('warning', 'Avertissement'),
        ('danger', 'Danger'),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='alerts')
    title = models.CharField(max_length=200, verbose_name="Titre")
    message = models.TextField(verbose_name="Message")
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES, default='info', verbose_name="Type")
    level = models.CharField(max_length=20, choices=ALERT_LEVELS, default='low', verbose_name="Niveau")
    is_read = models.BooleanField(default=False, verbose_name="Lu")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")

    class Meta:
        verbose_name = "Alerte"
        verbose_name_plural = "Alertes"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.patient}"

