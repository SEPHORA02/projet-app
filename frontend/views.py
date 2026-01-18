import requests
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.conf import settings
from django.http import JsonResponse
from firebase_admin import auth

# -------------------------------
# INSCRIPTION
# -------------------------------
@csrf_protect
def register_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        # Vérifie si l'email existe déjà sur Firebase
        try:
            auth.get_user_by_email(email)
            messages.error(request, 'Cet email est déjà utilisé')
            return render(request, 'frontend/auth/inscription.html')
        except auth.UserNotFoundError:
            # L'email n'existe pas : créer l'utilisateur
            try:
                user_firebase = auth.create_user(
                    email=email,
                    password=password,
                    display_name=name
                )
                # Crée un utilisateur Django minimal pour la session
                user_django, created = User.objects.get_or_create(
                    username=user_firebase.uid,
                    defaults={'email': email, 'first_name': name}
                )
                messages.success(request, "Compte créé avec succès. Connectez-vous.")
                return redirect("connexion")
            except Exception as e:
                messages.error(request, f"Erreur lors de l'inscription : {str(e)}")
    
    return render(request, 'frontend/auth/inscription.html')


# -------------------------------
# CONNEXION
# -------------------------------
@csrf_protect
def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        # Appel API Firebase pour authentification
        payload = {
            "email": email,
            "password": password,
            "returnSecureToken": True
        }

        r = requests.post(
            f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={settings.FIREBASE_API_KEY}",
            json=payload
        )
        data = r.json()

        if "idToken" in data:
            uid = data["localId"]
            user_firebase = auth.get_user(uid)
            display_name = user_firebase.display_name or ""

            user_django, created = User.objects.get_or_create(
                username=uid,
                defaults={'email': email, 'first_name': display_name}
            )
            # Si l'utilisateur existe mais n'a pas de first_name, on met à jour
            if not user_django.first_name and display_name:
                user_django.first_name = display_name
                user_django.save()

            login(request, user_django)
            return redirect("tableau_bord")

        else:
            messages.error(request, 'Email ou mot de passe incorrect')

    return render(request, 'frontend/auth/connexion.html')


# -------------------------------
# DECONNEXION
# -------------------------------
def logout_view(request):
    logout(request)
    messages.info(request, "Vous avez été déconnecté.")
    return redirect('connexion')


# -------------------------------
# VUES PROTEGEES
# -------------------------------
@login_required
def dashboard_view(request):
    return render(request, 'frontend/dashboard/tableau_bord.html')

@login_required
def history_view(request):
    return render(request, 'frontend/dashboard/historique.html')

@login_required
def report_view(request):
    return render(request, 'frontend/dashboard/rapports.html')

@login_required
def alerts_view(request):
    return render(request, 'frontend/dashboard/alertes.html')

@login_required
def settings_view(request):
    return render(request, 'frontend/dashboard/parametres.html')


##MALICK
ESP8266_IP = "http://192.168.1.17"
def get_heartbeat(request):
    """Simple heartbeat pour vérifier que le serveur Django est vivant"""
    return JsonResponse({
        "status": "alive",
        "message": "Django API en ligne",
        "timestamp": __import__('datetime').datetime.now().isoformat()
    })
##end Malick