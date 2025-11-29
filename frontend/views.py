from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
##MALICK
from django.http import JsonResponse
import requests
##end Malick
import json

def login_view(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        email = data.get('email')
        password = data.get('password')
        
        # Rechercher l'utilisateur par email
        try:
            user = User.objects.get(email=email)
            user = authenticate(request, username=user.username, password=password)
            if user is not None:
                login(request, user)
                return JsonResponse({'success': True, 'redirect': '/dashboard/'})
        except User.DoesNotExist:
            pass
        
        return JsonResponse({'success': False, 'error': 'Email ou mot de passe incorrect'})
    
    return render(request, 'frontend/base.html')

def register_view(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        
        if User.objects.filter(email=email).exists():
            return JsonResponse({'success': False, 'error': 'Cet email est déjà utilisé'})
        
        try:
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=name
            )
            login(request, user)
            return JsonResponse({'success': True, 'redirect': '/dashboard/'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return render(request, 'frontend/base.html')

@login_required
def dashboard_view(request):
    return render(request, 'frontend/base.html')

@login_required
def history_view(request):
    return render(request, 'frontend/base.html')

@login_required
def report_view(request):
    return render(request, 'frontend/base.html')

@login_required
def alerts_view(request):
    return render(request, 'frontend/base.html')

@login_required
def settings_view(request):
    return render(request, 'frontend/base.html')

def logout_view(request):
    logout(request)
    return JsonResponse({'success': True, 'redirect': '/login/'})

##Malick
const API_ENDPOINT = '/health/api/heartbeat/'
ESP8266_IP = "http://192.168.1.105"
def get_heartbeat(request):
    """API pour récupérer les données du capteur cardiaque"""
    try:
        response = requests.get(f"{ESP8266_IP}/api/heartbeat", timeout=2)
        data = response.json()
        
        # Ajout d'un message de statut
        if data['finger_detected']:
            if data['bpm_avg'] < 60:
                data['message'] = "Fréquence cardiaque basse"
            elif data['bpm_avg'] > 100:
                data['message'] = "Fréquence cardiaque élevée"
            else:
                data['message'] = "Fréquence cardiaque normale"
        else:
            data['message'] = "Placez votre doigt sur le capteur"
        
        return JsonResponse(data)
        
    except requests.exceptions.Timeout:
        return JsonResponse({"error": "ESP8266 timeout"}, status=503)
    except requests.exceptions.ConnectionError:
        return JsonResponse({"error": "ESP8266 déconnecté"}, status=503)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
##end Malick