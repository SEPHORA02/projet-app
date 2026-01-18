from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        try:
            user = User.objects.get(email=email)
            user = authenticate(request, username=user.username, password=password)
            if user is not None:
                login(request, user)
                return redirect('tableau_bord')
        except User.DoesNotExist:
            pass
        
        messages.error(request, 'Email ou mot de passe incorrect')
        return render(request, 'frontend/auth/connexion.html')
    
    return render(request, 'frontend/auth/connexion.html')

def register_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Cet email est déjà utilisé')
            return render(request, 'frontend/auth/inscription.html')
        
        try:
            # Create user with email as username since we look it up by email in login
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=name
            )
            login(request, user)
            return redirect('tableau_bord')
        except Exception as e:
            messages.error(request, f"Erreur lors de l'inscription: {str(e)}")
            return render(request, 'frontend/auth/inscription.html')
    
    return render(request, 'frontend/auth/inscription.html')

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

def logout_view(request):
    logout(request)
    return JsonResponse({'success': True, 'redirect': '/login/'})

##MALICK
ESP8266_IP = "http://192.168.137.223"
def get_heartbeat(request):
    """Simple heartbeat pour vérifier que le serveur Django est vivant"""
    return JsonResponse({
        "status": "alive",
        "message": "Django API en ligne",
        "timestamp": __import__('datetime').datetime.now().isoformat()
    })
##end Malick