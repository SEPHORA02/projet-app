# Guide d'authentification Git pour GitHub

## Solution 1 : Personal Access Token (PAT) - Recommandé

### Étape 1 : Créer un token sur GitHub

1. Allez sur GitHub.com → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Cliquez sur "Generate new token (classic)"
3. Donnez un nom au token (ex: "projet-app")
4. Sélectionnez les permissions nécessaires :
   - `repo` (accès complet aux dépôts)
5. Cliquez sur "Generate token"
6. **COPIEZ LE TOKEN IMMÉDIATEMENT** (vous ne pourrez plus le voir après)

### Étape 2 : Utiliser le token

Quand Git vous demande votre mot de passe, utilisez le token à la place.

```bash
# Pour push/pull
git push origin main
# Username: SEPHORA02
# Password: [collez votre token ici]
```

### Étape 3 : Sauvegarder le token (optionnel)

Pour éviter de le retaper à chaque fois :

```bash
# Configurer Git Credential Helper
git config --global credential.helper store

# Ou utiliser le cache (15 minutes)
git config --global credential.helper cache
```

## Solution 2 : Utiliser SSH (Plus sécurisé)

### Étape 1 : Vérifier si vous avez déjà une clé SSH

```bash
ls -al ~/.ssh
```

### Étape 2 : Créer une clé SSH (si nécessaire)

```bash
ssh-keygen -t ed25519 -C "votre_email@example.com"
# Appuyez sur Entrée pour accepter l'emplacement par défaut
# Entrez un mot de passe (ou laissez vide)
```

### Étape 3 : Ajouter la clé SSH à l'agent

```bash
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519
```

### Étape 4 : Copier la clé publique

```bash
cat ~/.ssh/id_ed25519.pub
# Copiez tout le contenu affiché
```

### Étape 5 : Ajouter la clé sur GitHub

1. Allez sur GitHub.com → Settings → SSH and GPG keys
2. Cliquez sur "New SSH key"
3. Collez votre clé publique
4. Cliquez sur "Add SSH key"

### Étape 6 : Changer le remote vers SSH

```bash
git remote set-url origin git@github.com:SEPHORA02/projet-app.git
git remote -v  # Vérifier
```

### Étape 7 : Tester la connexion

```bash
ssh -T git@github.com
# Devrait afficher : Hi SEPHORA02! You've successfully authenticated...
```

## Solution rapide : Changer vers SSH maintenant

Si vous avez déjà une clé SSH configurée :

```bash
cd projet-app
git remote set-url origin git@github.com:SEPHORA02/projet-app.git
git push origin main
```
