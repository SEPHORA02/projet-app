from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from .models import Patient, PhysiologicalData, EnvironmentalData, Alert


def login_view(request):
    """Vue de connexion"""
    if request.user.is_authenticated:
        return redirect('health:dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('health:dashboard')
        else:
            messages.error(request, 'Nom d\'utilisateur ou mot de passe incorrect.')
    
    return render(request, 'health/login.html')


@login_required
def dashboard(request):
    """Vue principale du dashboard"""
    # Récupérer ou créer le profil patient
    try:
        patient = request.user.patient_profile
    except Patient.DoesNotExist:
        # Créer un profil patient par défaut si il n'existe pas
        patient = Patient.objects.create(
            user=request.user,
            age=45,
            location="Paris, France",
            health_profile="Asthme chronique - Surveillance intelligente et alertes préventives personnalisées"
        )
    
    # Récupérer les dernières données physiologiques
    latest_physiological = PhysiologicalData.objects.filter(
        patient=patient
    ).order_by('-recorded_at').first()
    
    # Si aucune donnée n'existe, créer des données par défaut
    if not latest_physiological:
        latest_physiological = PhysiologicalData.objects.create(
            patient=patient,
            heart_rate=72,
            oxygen_saturation=98.0,
            temperature=36.8
        )
    
    # Récupérer les dernières données environnementales
    latest_environmental = EnvironmentalData.objects.filter(
        patient=patient
    ).order_by('-recorded_at').first()
    
    # Si aucune donnée n'existe, créer des données par défaut
    if not latest_environmental:
        latest_environmental = EnvironmentalData.objects.create(
            patient=patient,
            air_quality_index=42,
            co2_level=420,
            humidity=55,
            pm25=12,
            co_level=0.3,
            no2_level=18,
            o3_level=35
        )
    
    # Récupérer les alertes récentes (non lues)
    recent_alerts = Alert.objects.filter(
        patient=patient,
        is_read=False
    ).order_by('-created_at')[:5]
    
    # Récupérer toutes les alertes pour l'onglet alertes
    all_alerts = Alert.objects.filter(
        patient=patient
    ).order_by('-created_at')[:10]
    
    # Récupérer les données des dernières 24h pour les tendances
    last_24h = timezone.now() - timedelta(hours=24)
    physiological_trends = PhysiologicalData.objects.filter(
        patient=patient,
        recorded_at__gte=last_24h
    ).order_by('recorded_at')
    
    environmental_trends = EnvironmentalData.objects.filter(
        patient=patient,
        recorded_at__gte=last_24h
    ).order_by('recorded_at')
    
    context = {
        'patient': patient,
        'physiological': latest_physiological,
        'environmental': latest_environmental,
        'recent_alerts': recent_alerts,
        'all_alerts': all_alerts,
        'physiological_trends': physiological_trends,
        'environmental_trends': environmental_trends,
    }
    
    return render(request, 'health/dashboard.html', context)


@login_required
def environment_view(request):
    """Vue détaillée de l'environnement"""
    try:
        patient = request.user.patient_profile
    except Patient.DoesNotExist:
        return redirect('health:dashboard')
    
    latest_environmental = EnvironmentalData.objects.filter(
        patient=patient
    ).order_by('-recorded_at').first()
    
    if not latest_environmental:
        latest_environmental = EnvironmentalData.objects.create(
            patient=patient,
            air_quality_index=42,
            co2_level=420,
            humidity=55,
            pm25=12
        )
    
    context = {
        'patient': patient,
        'environmental': latest_environmental,
    }
    
    return render(request, 'health/environment.html', context)

