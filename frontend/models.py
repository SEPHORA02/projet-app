from django.db import models
from django.utils import timezone


class Alert(models.Model):
    """Modèle pour stocker les alertes provenant de l'API FastAPI"""
    
    SEVERITY_CHOICES = [
        ('low', 'Faible'),
        ('medium', 'Moyen'),
        ('high', 'Élevé'),
        ('critical', 'Critique'),
    ]
    
    ALERT_TYPE_CHOICES = [
        ('asthma_risk', 'Risque asthme'),
        ('heart_rate', 'Fréquence cardiaque'),
        ('temperature', 'Température'),
        ('respiratory', 'Respiration'),
        ('environment', 'Environnement'),
        ('info', 'Information'),
    ]
    
    patient_id = models.CharField(max_length=255, default='default_patient')
    alert_type = models.CharField(max_length=50, choices=ALERT_TYPE_CHOICES)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    message = models.TextField()
    sensor_data = models.JSONField(default=dict)
    ai_analysis = models.JSONField(default=dict)
    recommendations = models.JSONField(default=list)
    
    timestamp = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    # Champs pour le suivi
    is_read = models.BooleanField(default=False)
    is_dismissed = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['severity']),
            models.Index(fields=['is_read']),
        ]
    
    def __str__(self):
        return f"{self.get_severity_display()} - {self.message[:50]}"
    
    @property
    def time_ago(self):
        """Retourne le temps écoulé depuis l'alerte"""
        from django.utils.timesince import timesince
        return f"il y a {timesince(self.timestamp)}"
    
    @property
    def style(self):
        """Retourne les styles en fonction du type et de la sévérité"""
        styles = {
            ('asthma_risk', 'critical'): {
                'icon': 'alert-triangle',
                'bg_color': '#FEE2E2',
                'text_color': '#DC2626',
                'border_color': '#EF4444'
            },
            ('asthma_risk', 'high'): {
                'icon': 'alert-circle',
                'bg_color': '#FEF3C7',
                'text_color': '#D97706',
                'border_color': '#FF9F43'
            },
            ('heart_rate', 'high'): {
                'icon': 'heart',
                'bg_color': '#FCE7F3',
                'text_color': '#BE185D',
                'border_color': '#EC4899'
            },
            ('temperature', 'high'): {
                'icon': 'thermometer',
                'bg_color': '#FEE2E2',
                'text_color': '#DC2626',
                'border_color': '#EF4444'
            },
            ('respiratory', 'high'): {
                'icon': 'wind',
                'bg_color': '#E0E7FF',
                'text_color': '#4F46E5',
                'border_color': '#6366F1'
            },
            ('environment', 'medium'): {
                'icon': 'cloud',
                'bg_color': '#DBEAFE',
                'text_color': '#0284C7',
                'border_color': '#0EA5E9'
            },
            ('info', 'low'): {
                'icon': 'info',
                'bg_color': '#D1FAE5',
                'text_color': '#22C58E',
                'border_color': '#10B981'
            },
        }
        
        # Chercher le style exact, sinon chercher par type, sinon par sévérité
        key = (self.alert_type, self.severity)
        if key in styles:
            return styles[key]
        
        # Style par défaut
        return {
            'icon': 'bell',
            'bg_color': '#DBEAFE',
            'text_color': '#0284C7',
            'border_color': '#0EA5E9'
        }
    
    @property
    def badge(self):
        """Retourne les informations du badge"""
        severity_badges = {
            'critical': {'icon': 'alert-triangle', 'text': 'Critique'},
            'high': {'icon': 'alert-circle', 'text': 'Élevé'},
            'medium': {'icon': 'alert-circle', 'text': 'Moyen'},
            'low': {'icon': 'info', 'text': 'Faible'},
        }
        return severity_badges.get(self.severity, {'icon': 'info', 'text': 'Info'})
