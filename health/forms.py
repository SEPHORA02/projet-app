from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import Patient

Utilisateur = get_user_model()


def _nettoyer_valeur(data, cle):
    return (data.get(cle) or '').strip()


def valider_inscription(data):
    erreurs = {}
    nettoye = {
        'username': _nettoyer_valeur(data, 'username'),
        'email': _nettoyer_valeur(data, 'email'),
        'first_name': _nettoyer_valeur(data, 'first_name'),
        'last_name': _nettoyer_valeur(data, 'last_name'),
        'sex': _nettoyer_valeur(data, 'sex'),
        'phone_number': _nettoyer_valeur(data, 'phone_number'),
        'age': _nettoyer_valeur(data, 'age'),
        'location': _nettoyer_valeur(data, 'location'),
        'password1': data.get('password1') or '',
        'password2': data.get('password2') or '',
    }

    champs_obligatoires = [
        'username',
        'email',
        'first_name',
        'last_name',
        'sex',
        'phone_number',
        'age',
        'location',
        'password1',
        'password2',
    ]
    for champ in champs_obligatoires:
        if not nettoye[champ]:
            erreurs[champ] = "Ce champ est obligatoire."

    if nettoye.get('password1') != nettoye.get('password2'):
        erreurs['password2'] = "Les mots de passe doivent être identiques."

    try:
        nettoye['age'] = int(nettoye['age'])
        if nettoye['age'] <= 0:
            raise ValueError
    except (TypeError, ValueError):
        erreurs['age'] = "Âge invalide."

    if nettoye['sex'] and nettoye['sex'] not in dict(Patient.SEXE_CHOIX):
        erreurs['sex'] = "Valeur non reconnue."

    if nettoye['username'] and Utilisateur.objects.filter(username=nettoye['username']).exists():
        erreurs['username'] = "Cet identifiant est déjà utilisé."

    if nettoye['email'] and Utilisateur.objects.filter(email=nettoye['email']).exists():
        erreurs['email'] = "Cette adresse e-mail est déjà utilisée."

    return nettoye, erreurs


def valider_compte(utilisateur, data):
    erreurs = {}
    nettoye = {
        'first_name': _nettoyer_valeur(data, 'first_name'),
        'last_name': _nettoyer_valeur(data, 'last_name'),
        'email': _nettoyer_valeur(data, 'email'),
        'username': _nettoyer_valeur(data, 'username'),
    }
    for champ, valeur in nettoye.items():
        if not valeur:
            erreurs[champ] = "Ce champ est obligatoire."

    if nettoye['username'] and Utilisateur.objects.exclude(pk=utilisateur.pk).filter(username=nettoye['username']).exists():
        erreurs['username'] = "Cet identifiant est déjà pris."

    if nettoye['email'] and Utilisateur.objects.exclude(pk=utilisateur.pk).filter(email=nettoye['email']).exists():
        erreurs['email'] = "Cette adresse e-mail est déjà utilisée."

    return nettoye, erreurs


def valider_profil_patient(data):
    erreurs = {}
    nettoye = {
        'age': _nettoyer_valeur(data, 'age'),
        'location': _nettoyer_valeur(data, 'location'),
        'health_profile': _nettoyer_valeur(data, 'health_profile'),
        'phone_number': _nettoyer_valeur(data, 'phone_number'),
        'sex': _nettoyer_valeur(data, 'sex'),
    }

    try:
        nettoye['age'] = int(nettoye['age'])
        if nettoye['age'] <= 0:
            raise ValueError
    except (TypeError, ValueError):
        erreurs['age'] = "Âge invalide."

    if nettoye['sex'] and nettoye['sex'] not in dict(Patient.SEXE_CHOIX):
        erreurs['sex'] = "Valeur non reconnue."

    if not nettoye['location']:
        erreurs['location'] = "Ce champ est obligatoire."

    return nettoye, erreurs


def valider_mot_de_passe(utilisateur, data):
    erreurs = {}
    nettoye = {
        'old_password': data.get('old_password') or '',
        'new_password1': data.get('new_password1') or '',
        'new_password2': data.get('new_password2') or '',
    }

    if not nettoye['old_password']:
        erreurs['old_password'] = "Champ obligatoire."
    elif not utilisateur.check_password(nettoye['old_password']):
        erreurs['old_password'] = "Mot de passe actuel incorrect."

    if not nettoye['new_password1']:
        erreurs['new_password1'] = "Champ obligatoire."

    if nettoye['new_password1'] != nettoye['new_password2']:
        erreurs['new_password2'] = "Les nouveaux mots de passe ne correspondent pas."

    if 'new_password1' not in erreurs and nettoye['new_password1']:
        try:
            validate_password(nettoye['new_password1'], user=utilisateur)
        except ValidationError as exc:
            erreurs['new_password1'] = " ".join(exc.messages)

    return nettoye, erreurs
