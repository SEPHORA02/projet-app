import requests
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from frontend.firebase import FIREBASE_INITIALIZED
from django.views.decorators.http import require_http_methods
from frontend.models import Alert
import json
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.pdfgen import canvas

if FIREBASE_INITIALIZED:
    from firebase_admin import auth
else:
    auth = None

# -------------------------------
# INSCRIPTION
# -------------------------------
@csrf_protect
def register_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        # Check if user already exists in Django
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Cet email est déjà utilisé')
            return render(request, 'frontend/auth/inscription.html')
        
        try:
            if FIREBASE_INITIALIZED and auth:
                # Use Firebase if available
                try:
                    auth.get_user_by_email(email)
                    messages.error(request, 'Cet email est déjà utilisé')
                    return render(request, 'frontend/auth/inscription.html')
                except:
                    pass
                
                user_firebase = auth.create_user(
                    email=email,
                    password=password,
                    display_name=name
                )
                user_django, created = User.objects.get_or_create(
                    username=user_firebase.uid,
                    defaults={'email': email, 'first_name': name}
                )
            else:
                # Fallback: Create user with Django auth only
                user_django = User.objects.create_user(
                    username=email,
                    email=email,
                    first_name=name,
                    password=password
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
        
        if FIREBASE_INITIALIZED and settings.FIREBASE_API_KEY:
            # Use Firebase API
            payload = {
                "email": email,
                "password": password,
                "returnSecureToken": True
            }

            try:
                r = requests.post(
                    f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={settings.FIREBASE_API_KEY}",
                    json=payload
                )
                data = r.json()

                if "idToken" in data:
                    uid = data["localId"]
                    if auth:
                        user_firebase = auth.get_user(uid)
                        display_name = user_firebase.display_name or ""
                    else:
                        display_name = ""

                    user_django, created = User.objects.get_or_create(
                        username=uid,
                        defaults={'email': email, 'first_name': display_name}
                    )
                    if not user_django.first_name and display_name:
                        user_django.first_name = display_name
                        user_django.save()

                    login(request, user_django)
                    return redirect("tableau_bord")
                else:
                    messages.error(request, 'Email ou mot de passe incorrect')
            except Exception as e:
                messages.error(request, f'Erreur Firebase: {str(e)}')
        else:
            # Fallback: Use Django authentication
            try:
                user = User.objects.get(email=email)
                user_auth = authenticate(request, username=user.username, password=password)
                if user_auth is not None:
                    login(request, user_auth)
                    return redirect("tableau_bord")
                else:
                    messages.error(request, 'Email ou mot de passe incorrect')
            except User.DoesNotExist:
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
    """Vue pour afficher les alertes/notifications"""
    from .models import Alert
    
    # Récupérer les alertes récentes non masquées
    alertes = Alert.objects.filter(is_dismissed=False).order_by('-timestamp')[:100]
    
    # Calculer les statistiques
    all_alerts = Alert.objects.filter(is_dismissed=False)
    alertes_attention = all_alerts.filter(severity__in=['high', 'critical']).count()
    alertes_info = all_alerts.filter(severity='low').count()
    alertes_amelioration = all_alerts.filter(alert_type='info').count()
    
    context = {
        'alertes': alertes,
        'total_alertes': all_alerts.count(),
        'alertes_attention': alertes_attention,
        'alertes_info': alertes_info,
        'alertes_amelioration': alertes_amelioration,
    }
    
    return render(request, 'frontend/dashboard/alertes.html', context)

@login_required
def settings_view(request):
    return render(request, 'frontend/dashboard/parametres.html')


# API JSON Endpoints
@login_required
def api_get_alerts(request):
    """API pour obtenir les alertes en JSON"""
    from .models import Alert
    import json
    from django.core.serializers.json import DjangoJSONEncoder
    
    alertes = Alert.objects.filter(is_dismissed=False).order_by('-timestamp')[:100]
    
    alertes_data = []
    for alerte in alertes:
        alertes_data.append({
            'id': alerte.id,
            'message': alerte.message,
            'severity': alerte.severity,
            'alert_type': alerte.alert_type,
            'timestamp': alerte.timestamp.isoformat(),
            'time_ago': alerte.time_ago,
            'sensor_data': alerte.sensor_data,
            'ai_analysis': alerte.ai_analysis,
            'recommendations': alerte.recommendations,
            'style': alerte.style,
            'badge': alerte.badge,
        })
    
    return JsonResponse({
        'status': 'success',
        'count': len(alertes_data),
        'alerts': alertes_data
    })


@login_required
def api_get_alerts_stats(request):
    """API pour obtenir les statistiques des alertes"""
    from .models import Alert
    
    all_alerts = Alert.objects.filter(is_dismissed=False)
    
    stats = {
        'total': all_alerts.count(),
        'critical': all_alerts.filter(severity='critical').count(),
        'high': all_alerts.filter(severity='high').count(),
        'medium': all_alerts.filter(severity='medium').count(),
        'low': all_alerts.filter(severity='low').count(),
        'unread': all_alerts.filter(is_read=False).count(),
        'by_type': {
            'asthma_risk': all_alerts.filter(alert_type='asthma_risk').count(),
            'heart_rate': all_alerts.filter(alert_type='heart_rate').count(),
            'temperature': all_alerts.filter(alert_type='temperature').count(),
            'respiratory': all_alerts.filter(alert_type='respiratory').count(),
            'environment': all_alerts.filter(alert_type='environment').count(),
            'info': all_alerts.filter(alert_type='info').count(),
        }
    }
    
    return JsonResponse(stats)


@login_required
def api_mark_alert_as_read(request, alert_id):
    """Marquer une alerte comme lue"""
    from .models import Alert
    
    if request.method == 'POST':
        try:
            alert = Alert.objects.get(id=alert_id)
            alert.is_read = True
            alert.save()
            return JsonResponse({'status': 'success'})
        except Alert.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Alert not found'}, status=404)
    
    return JsonResponse({'status': 'error'}, status=405)


@login_required
def api_dismiss_alert(request, alert_id):
    """Masquer une alerte"""
    from .models import Alert
    
    if request.method == 'POST':
        try:
            alert = Alert.objects.get(id=alert_id)
            alert.is_dismissed = True
            alert.save()
            return JsonResponse({'status': 'success'})
        except Alert.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Alert not found'}, status=404)
    
    return JsonResponse({'status': 'error'}, status=405)


def api_receive_alert_from_fastapi(request):
    """Endpoint pour recevoir les alertes depuis FastAPI"""
    from .models import Alert
    from django.views.decorators.csrf import csrf_exempt
    import json
    
    # Protection par clé API (optionnel)
    api_key = request.headers.get('Authorization', '').replace('Bearer ', '')
    expected_key = getattr(settings, 'FASTAPI_API_KEY', None)
    
    if expected_key and api_key != expected_key:
        return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=401)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Créer l'alerte
            alert = Alert.objects.create(
                patient_id=data.get('patient_id', 'default_patient'),
                alert_type=data.get('alert_type', 'info'),
                severity=data.get('severity', 'low'),
                message=data.get('message', ''),
                sensor_data=data.get('sensor_data', {}),
                ai_analysis=data.get('ai_analysis', {}),
                recommendations=data.get('recommendations', []),
            )
            
            return JsonResponse({
                'status': 'success',
                'alert_id': alert.id,
                'message': 'Alerte reçue et sauvegardée'
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
    
    return JsonResponse({'status': 'error'}, status=405)

# Appliquer le décorateur csrf_exempt
api_receive_alert_from_fastapi = csrf_exempt(api_receive_alert_from_fastapi)


##MALICK
def get_esp8266_config(request):
    """API endpoint pour obtenir la configuration ESP8266"""
    return JsonResponse({
        "baseUrl": settings.ESP8266_BASE_URL,
        "endpoints": {
            "sensors": "/api/sensors",
            "heartRate": "/api/heart",
            "temperature": "/api/temp",
            "respiratory": "/api/resp",
            "environment": "/api/env",
            "riskLevel": "/api/risk"
        }
    })

def get_heartbeat(request):
    """Simple heartbeat pour vérifier que le serveur Django est vivant"""
    return JsonResponse({
        "status": "alive",
        "message": "Django API en ligne",
        "timestamp": __import__('datetime').datetime.now().isoformat()
    })
##end Malick


# Stockage temporaire des alertes (en mémoire)
# Pour la production, utilisez une base de données
ALERTES_STORAGE = []


@csrf_exempt
@require_http_methods(["POST"])
def receive_alert(request):
    """
    Endpoint qui reçoit les alertes de FastAPI
    URL: http://127.0.0.1:8000/alertes/
    """
    try:
        # Parser le JSON envoyé par FastAPI
        data = json.loads(request.body)
        
        # Ajouter un ID et timestamp si pas présent
        alerte = {
            'id': len(ALERTES_STORAGE) + 1,
            'patient_id': data.get('patient_id', 'default_patient'),
            'alert_type': data.get('alert_type', 'asthma_risk'),
            'severity': data.get('severity', 'medium'),
            'message': data.get('message', 'Alerte reçue'),
            'sensor_data': data.get('sensor_data', {}),
            'ai_analysis': data.get('ai_analysis', {}),
            'recommendations': data.get('recommendations', []),
            'timestamp': data.get('timestamp', datetime.now().isoformat()),
            'received_at': datetime.now().isoformat(),
            'read': False
        }
        
        # Ajouter au début de la liste (plus récent en premier)
        ALERTES_STORAGE.insert(0, alerte)
        
        # Garder seulement les 50 dernières alertes
        if len(ALERTES_STORAGE) > 50:
            ALERTES_STORAGE.pop()
        
        print(f"✅ Alerte reçue: {alerte['severity']} - {alerte['message']}")
        
        return JsonResponse({
            'status': 'success',
            'message': 'Alerte reçue et enregistrée',
            'alert_id': alerte['id']
        }, status=201)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'JSON invalide'
        }, status=400)
    except Exception as e:
        print(f"❌ Erreur réception alerte: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


def alertes_page(request):
    """
    Vue pour afficher la page des alertes avec données de la base de données
    URL: /dashboard/alertes/
    """
    # Récupérer toutes les alertes non lues et réduites de la DB
    alertes = Alert.objects.filter(is_dismissed=False).order_by('-timestamp')[:50]
    
    # Compter les alertes par sévérité
    alertes_attention = alertes.filter(severity__in=['high', 'critical']).count()
    alertes_info = alertes.filter(severity='medium').count()
    alertes_amelioration = alertes.filter(severity='low').count()
    
    # Formater les alertes pour l'affichage
    alertes_formatted = []
    for alerte in alertes:
        style = alerte.style  # Utilise la propriété style du modèle
        
        alertes_formatted.append({
            'id': alerte.id,
            'message': alerte.message,
            'severity': alerte.severity,
            'alert_type': alerte.alert_type,
            'timestamp': alerte.timestamp.isoformat(),
            'time_ago': alerte.time_ago,
            'sensor_data': alerte.sensor_data,
            'ai_analysis': alerte.ai_analysis,
            'recommendations': alerte.recommendations,
            'style': style,
            'badge': {
                'icon': 'activity',
                'text': alerte.get_alert_type_display()
            }
        })
    
    context = {
        'alertes': alertes_formatted,
        'alertes_attention': alertes_attention,
        'alertes_info': alertes_info,
        'alertes_amelioration': alertes_amelioration,
        'total_alertes': len(alertes_formatted)
    }
    
    return render(request, 'frontend/alertes.html', context)


@require_http_methods(["GET"])
def get_alerts_json(request):
    """
    API REST pour récupérer les alertes en JSON (pour mises à jour en temps réel)
    URL: /api/alertes/
    """
    # Récupérer les alertes non lues
    limit = request.GET.get('limit', 50)
    alertes = Alert.objects.filter(is_dismissed=False).order_by('-timestamp')[:int(limit)]
    
    alerts_data = []
    for alerte in alertes:
        alerts_data.append({
            'id': alerte.id,
            'message': alerte.message,
            'severity': alerte.severity,
            'alert_type': alerte.alert_type,
            'timestamp': alerte.timestamp.isoformat(),
            'time_ago': alerte.time_ago,
            'sensor_data': alerte.sensor_data,
            'ai_analysis': alerte.ai_analysis,
            'recommendations': alerte.recommendations,
            'is_read': alerte.is_read
        })
    
    return JsonResponse({
        'status': 'success',
        'count': len(alerts_data),
        'alerts': alerts_data
    })


@require_http_methods(["POST"])
def mark_alert_as_read(request, alert_id):
    """
    Marquer une alerte comme lue
    URL: /api/alertes/{id}/read/
    """
    try:
        alerte = Alert.objects.get(id=alert_id)
        alerte.is_read = True
        alerte.save()
        return JsonResponse({'status': 'success', 'message': 'Alerte marquée comme lue'})
    except Alert.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Alerte non trouvée'}, status=404)


@require_http_methods(["POST"])
def dismiss_alert(request, alert_id):
    """
    Ignorer une alerte
    URL: /api/alertes/{id}/dismiss/
    """
    try:
        alerte = Alert.objects.get(id=alert_id)
        alerte.is_dismissed = True
        alerte.save()
        return JsonResponse({'status': 'success', 'message': 'Alerte supprimée'})
    except Alert.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Alerte non trouvée'}, status=404)


@csrf_exempt
@require_http_methods(["DELETE", "POST"])
def clear_all_alerts(request):
    """
    Marquer toutes les alertes comme supprimées
    URL: /api/alertes/clear/
    """
    Alert.objects.update(is_dismissed=True)
    return JsonResponse({
        'status': 'success',
        'message': 'Toutes les alertes ont été supprimées'
    })


@csrf_exempt
@require_http_methods(["POST"])
def generate_report_pdf(request):
    """
    Générer un PDF du rapport
    URL: /generate-report-pdf/
    """
    try:
        alerts_data = request.POST.get('alerts_data', '[]')
        alerts = json.loads(alerts_data)
        
        # Créer le PDF en mémoire
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#0A74DA'),
            spaceAfter=30,
            alignment=1
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#0A74DA'),
            spaceAfter=12,
            spaceBefore=12
        )
        
        # Titre
        elements.append(Paragraph("📋 Rapport de Prévention Personnalisé", title_style))
        elements.append(Spacer(1, 0.3*inch))
        
        # Date
        from datetime import datetime
        date_text = datetime.now().strftime("%d %B %Y")
        elements.append(Paragraph(f"<b>Date:</b> {date_text}", styles['Normal']))
        elements.append(Spacer(1, 0.2*inch))
        
        # Résumé des métriques
        if alerts:
            severity_map = {'critical': 80, 'high': 60, 'medium': 40, 'low': 20}
            risk_values = [severity_map.get(a.get('severity', 'low'), 20) for a in alerts]
            avg_risk = sum(risk_values) // len(risk_values) if risk_values else 0
            min_risk = min(risk_values) if risk_values else 0
            max_risk = max(risk_values) if risk_values else 0
            
            elements.append(Paragraph("Résumé des Métriques", heading_style))
            
            metrics_data = [
                ['Métrique', 'Valeur'],
                ['Risque moyen', f'{avg_risk}/100'],
                ['Risque min', f'{min_risk}/100'],
                ['Risque max', f'{max_risk}/100'],
                ['Total alertes', str(len(alerts))],
                ['Amélioration', f'{max(0, 100 - avg_risk)}%']
            ]
            
            metrics_table = Table(metrics_data, colWidths=[3*inch, 2*inch])
            metrics_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0A74DA')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F0F0F0')])
            ]))
            
            elements.append(metrics_table)
            elements.append(Spacer(1, 0.3*inch))
        
        # Recommandations
        elements.append(Paragraph("Recommandations IA", heading_style))
        
        if alerts and len(alerts) > 0:
            latest_alert = alerts[0]
            analysis = latest_alert.get('ai_analysis', {})
            recommendations = analysis.get('recommendations', latest_alert.get('recommendations', []))
            
            for i, reco in enumerate(recommendations[:3], 1):
                priority = ['Haute', 'Moyenne', 'Faible'][i-1]
                elements.append(Paragraph(f"<b>{i}. {reco}</b>", styles['Normal']))
                elements.append(Paragraph(f"Priorité: {priority}", styles['Normal']))
                elements.append(Spacer(1, 0.1*inch))
        
        elements.append(Spacer(1, 0.3*inch))
        
        # Alertes détaillées
        elements.append(Paragraph("Alertes Enregistrées", heading_style))
        
        if alerts:
            alert_data = [['Date', 'Type', 'Sévérité', 'Message']]
            
            for alert in alerts[:10]:
                date_obj = datetime.fromisoformat(alert.get('timestamp', '').replace('Z', '+00:00')) if alert.get('timestamp') else datetime.now()
                alert_data.append([
                    date_obj.strftime("%d/%m/%Y %H:%M"),
                    alert.get('alert_type', 'N/A'),
                    alert.get('severity', 'N/A').upper(),
                    alert.get('message', '')[:50] + '...' if len(alert.get('message', '')) > 50 else alert.get('message', '')
                ])
            
            alert_table = Table(alert_data, colWidths=[1.5*inch, 1.2*inch, 1.2*inch, 1.8*inch])
            alert_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0A74DA')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F0F0F0')])
            ]))
            
            elements.append(alert_table)
        
        elements.append(Spacer(1, 0.5*inch))
        elements.append(Paragraph("---", styles['Normal']))
        elements.append(Paragraph(
            "<i>Ce rapport a été généré automatiquement par le système de surveillance asthmatique. "
            "Pour toute question, consultez votre médecin.</i>",
            styles['Normal']
        ))
        
        # Générer le PDF
        doc.build(elements)
        
        # Retourner le PDF
        buffer.seek(0)
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="rapport_prevention.pdf"'
        return response
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)