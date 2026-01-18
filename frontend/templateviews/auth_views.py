import requests
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.conf import settings
from firebase_admin import auth

@csrf_protect
def inscription(request):
    if request.method == 'POST':
        nom = request.POST.get('nom')
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        try:
            auth.get_user_by_email(email)
            messages.error(request, 'Un compte existe déjà avec cet email')
        except auth.UserNotFoundError:
            try:
                user_firebase = auth.create_user(
                    email=email,
                    password=password,
                    display_name=nom
                )
                # Crée un utilisateur Django pour la session
                user_django, _ = User.objects.get_or_create(
                    username=user_firebase.uid,
                    defaults={
                        'email': email,
                        'first_name': name if name else email.split('@')[0]  # utilise l’email si nom vide
                    }
                )

                login(request, user_django)
                messages.success(request, 'Compte créé avec succès!')
                return redirect('tableau_bord')
            except Exception as e:
                messages.error(request, f'Erreur lors de la création du compte: {str(e)}')
    
    return render(request, 'frontend/auth/inscription.html')

@csrf_protect
def connexion(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
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
            user_django, _ = User.objects.get_or_create(
                username=uid,
                defaults={'email': email}
            )
            login(request, user_django)
            messages.success(request, "Connexion réussie")
            return redirect("tableau_bord")
        else:
            messages.error(request, 'Email ou mot de passe incorrect')
    
    return render(request, 'frontend/auth/connexion.html')

def deconnexion(request):
    logout(request)
    return redirect('connexion')
