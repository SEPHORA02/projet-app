from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone

from .forms import (
    valider_compte,
    valider_inscription,
    valider_mot_de_passe,
    valider_profil_patient,
)
from .models import Alert, EnvironmentalData, Patient, PhysiologicalData
from .services import (
    ErreurRecuperationDonnees,
    analyser_risque_asthme,
    recuperer_donnees_fastapi,
)

Utilisateur = get_user_model()


def _obtenir_patient(utilisateur):
    """Garantit l'existence d'un profil patient pour l'utilisateur connecté."""
    patient, _ = Patient.objects.get_or_create(
        user=utilisateur,
        defaults={
            "age": 30,
            "location": "Abidjan, Côte d'Ivoire",
            "health_profile": "Profil à personnaliser",
        },
    )
    return patient


def connexion(request):
    """Permet à un utilisateur de se connecter."""
    if request.user.is_authenticated:
        return redirect('health:tableau_de_bord')

    if request.method == 'POST':
        identifiant = request.POST.get('username')
        mot_de_passe = request.POST.get('password')
        utilisateur = authenticate(request, username=identifiant, password=mot_de_passe)
        if utilisateur is not None:
            login(request, utilisateur)
            messages.success(request, "Connexion réussie. Bienvenue sur votre tableau de bord.")
            return redirect('health:tableau_de_bord')
        messages.error(request, "Identifiants incorrects. Veuillez réessayer.")

    return render(request, 'health/login.html')


def inscription(request):
    """Création de compte avec collecte des informations de base."""
    if request.user.is_authenticated:
        return redirect('health:tableau_de_bord')

    donnees = {}
    erreurs = {}

    if request.method == 'POST':
        donnees, erreurs = valider_inscription(request.POST)
        if not erreurs:
            utilisateur = Utilisateur.objects.create_user(
                username=donnees['username'],
                email=donnees['email'],
                first_name=donnees['first_name'],
                last_name=donnees['last_name'],
                password=donnees['password1'],
            )
            Patient.objects.create(
                user=utilisateur,
                age=donnees["age"],
                location=donnees["location"],
                health_profile="Profil à personnaliser",
                phone_number=donnees["phone_number"],
                sex=donnees["sex"],
            )
            login(request, utilisateur)
            messages.success(request, "Inscription réussie. Vos alertes santé sont prêtes.")
            return redirect('health:tableau_de_bord')
        messages.error(request, "Merci de corriger les erreurs ci-dessous.")

    contexte = {
        "donnees": donnees,
        "erreurs": erreurs,
    }
    return render(request, 'health/register.html', contexte)


def deconnexion(request):
    """Déconnecte l'utilisateur et le renvoie vers la connexion."""
    if request.user.is_authenticated:
        logout(request)
        messages.success(request, "Vous êtes déconnecté.")
    return redirect('health:connexion')


@login_required
def tableau_de_bord(request):
    """Vue principale pour suivre ses données et alertes."""
    patient = _obtenir_patient(request.user)

    donnees_physio = PhysiologicalData.objects.filter(patient=patient).order_by('-recorded_at').first()
    if not donnees_physio:
        donnees_physio = PhysiologicalData.objects.create(
            patient=patient,
            heart_rate=72,
            oxygen_saturation=98.0,
            temperature=36.8,
        )

    donnees_env = EnvironmentalData.objects.filter(patient=patient).order_by('-recorded_at').first()
    if not donnees_env:
        donnees_env = EnvironmentalData.objects.create(
            patient=patient,
            air_quality_index=42,
            co2_level=420,
            humidity=55,
            pm25=12,
            co_level=0.3,
            no2_level=18,
            o3_level=35,
        )

    alertes_recentes = Alert.objects.filter(patient=patient, is_read=False).order_by('-created_at')[:5]
    toutes_alertes = Alert.objects.filter(patient=patient).order_by('-created_at')[:10]

    dernier_jour = timezone.now() - timedelta(hours=24)
    tendances_physio = PhysiologicalData.objects.filter(
        patient=patient, recorded_at__gte=dernier_jour
    ).order_by('recorded_at')
    tendances_env = EnvironmentalData.objects.filter(
        patient=patient, recorded_at__gte=dernier_jour
    ).order_by('recorded_at')

    donnees_api = None
    erreur_api = None
    analyse_risque = None
    try:
        donnees_api = recuperer_donnees_fastapi(patient)
        analyse_risque = analyser_risque_asthme(donnees_api)
        if analyse_risque["risque"]:
            recents = Alert.objects.filter(
                patient=patient,
                title__icontains="Risque de crise d'asthme",
                created_at__gte=timezone.now() - timedelta(hours=1),
            ).exists()
            if not recents:
                Alert.objects.create(
                    patient=patient,
                    title="Risque de crise d'asthme détecté",
                    message="Les données externes indiquent un risque potentiel: "
                    + "; ".join(analyse_risque["facteurs"]),
                    alert_type='warning',
                    level='high',
                )
    except ErreurRecuperationDonnees as exc:
        erreur_api = str(exc)

    contexte = {
        "patient": patient,
        "donnees_physiologiques": donnees_physio,
        "donnees_environnementales": donnees_env,
        "alertes_recentes": alertes_recentes,
        "toutes_alertes": toutes_alertes,
        "tendances_physio": tendances_physio,
        "tendances_env": tendances_env,
        "donnees_externes": donnees_api,
        "erreur_donnees_externes": erreur_api,
        "analyse_risque": analyse_risque,
    }
    return render(request, 'health/dashboard.html', contexte)


@login_required
def modifier_compte(request):
    """Permet de modifier ses informations personnelles et médicales."""
    patient = _obtenir_patient(request.user)
    erreurs_compte = {}
    erreurs_profil = {}
    donnees_compte = {
        'first_name': request.user.first_name or '',
        'last_name': request.user.last_name or '',
        'email': request.user.email or '',
        'username': request.user.username or '',
    }
    donnees_profil = {
        'age': patient.age,
        'location': patient.location,
        'health_profile': patient.health_profile,
        'phone_number': patient.phone_number or '',
        'sex': patient.sex or '',
    }

    if request.method == 'POST':
        donnees_compte, erreurs_compte = valider_compte(request.user, request.POST)
        donnees_profil, erreurs_profil = valider_profil_patient(request.POST)
        if not erreurs_compte and not erreurs_profil:
            request.user.first_name = donnees_compte['first_name']
            request.user.last_name = donnees_compte['last_name']
            request.user.email = donnees_compte['email']
            request.user.username = donnees_compte['username']
            request.user.save()

            patient.age = donnees_profil['age']
            patient.location = donnees_profil['location']
            patient.health_profile = donnees_profil['health_profile']
            patient.phone_number = donnees_profil['phone_number']
            patient.sex = donnees_profil['sex']
            patient.save()
            messages.success(request, "Votre compte a été mis à jour.")
            return redirect('health:tableau_de_bord')
        messages.error(request, "Merci de vérifier les informations saisies.")

    contexte = {
        "donnees_compte": donnees_compte,
        "erreurs_compte": erreurs_compte,
        "donnees_profil": donnees_profil,
        "erreurs_profil": erreurs_profil,
    }
    return render(request, 'health/account_edit.html', contexte)


@login_required
def modifier_mot_de_passe(request):
    """Vue permettant de changer son mot de passe."""
    erreurs = {}
    if request.method == 'POST':
        donnees, erreurs = valider_mot_de_passe(request.user, request.POST)
        if not erreurs:
            request.user.set_password(donnees['new_password1'])
            request.user.save()
            update_session_auth_hash(request, request.user)
            messages.success(request, "Mot de passe mis à jour.")
            return redirect('health:tableau_de_bord')
        messages.error(request, "Veuillez corriger les erreurs de saisie.")

    return render(request, 'health/password_update.html', {"erreurs": erreurs})

