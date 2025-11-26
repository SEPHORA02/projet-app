from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect

@csrf_protect
def connexion(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        try:
            user = User.objects.get(email=email)
            user = authenticate(request, username=user.username, password=password)
            if user is not None:
                login(request, user)
                return redirect('tableau_bord')
            else:
                messages.error(request, 'Email ou mot de passe incorrect')
        except User.DoesNotExist:
            messages.error(request, 'Aucun compte trouvé avec cet email')
    
    return render(request, 'frontend/auth/connexion.html')

@csrf_protect
def inscription(request):
    if request.method == 'POST':
        nom = request.POST.get('nom')
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Un compte existe déjà avec cet email')
        else:
            try:
                user = User.objects.create_user(
                    username=email,
                    email=email,
                    password=password,
                    first_name=nom
                )
                login(request, user)
                messages.success(request, 'Compte créé avec succès!')
                return redirect('tableau_bord')
            except Exception as e:
                messages.error(request, f'Erreur lors de la création du compte: {str(e)}')
    
    return render(request, 'frontend/auth/inscription.html')

def deconnexion(request):
    logout(request)
    return redirect('connexion')