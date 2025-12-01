from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def tableau_bord(request):
    context = {
        'user': request.user,
        'page_title': 'Tableau de Bord'
    }
    return render(request, 'frontend/dashboard/tableau_bord.html', context)

@login_required
def historique(request):
    context = {
        'user': request.user,
        'page_title': 'Historique'
    }
    return render(request, 'frontend/dashboard/historique.html', context)

@login_required
def rapports(request):
    context = {
        'user': request.user,
        'page_title': 'Rapports'
    }
    return render(request, 'frontend/dashboard/rapports.html', context)

@login_required
def alertes(request):
    context = {
        'user': request.user,
        'page_title': 'Alertes'
    }
    return render(request, 'frontend/dashboard/alertes.html', context)

@login_required
def parametres(request):
    context = {
        'user': request.user,
        'page_title': 'Paramètres'
    }
    return render(request, 'frontend/dashboard/parametres.html', context)