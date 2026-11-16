# LeagueTraining

Site d'entraînement à la prise de décision dans League of Legends, entre potes : puzzles de macro et d'itemisation, mode chrono, puzzle du jour et classement. Projet de fans non commercial, non affilié à Riot Games.

- Conception : `docs/superpowers/specs/2026-11-16-league-training-design.md`
- Puzzles : `puzzles/<rôle>/*.yaml` (format décrit dans le document de conception, §6)

## Lancer avec Docker

1. Crée une application sur <https://discord.com/developers/applications>. Dans **OAuth2**, ajoute la redirection `https://<ton-domaine>/api/auth/callback`.
2. Copie `.env.example` vers `.env` et remplis-le.
3. Construis et lance :

```sh
docker build -t leaguetraining .
docker run -d --name leaguetraining --restart unless-stopped \
  --env-file .env -p 8000:8000 \
  -v leaguetraining-data:/data \
  --read-only --tmpfs /tmp --cap-drop ALL --security-opt no-new-privileges \
  leaguetraining
```

Au premier démarrage, l'app télécharge Data Dragon (images et données du patch) dans `/data/ddragon`. Ça prend environ une minute. Branche ensuite ton tunnel Cloudflare sur le port 8000.

## Administration

```sh
# Autoriser un pote (son identifiant Discord : Paramètres > Avancés > Mode développeur, puis clic droit sur son profil > Copier l'identifiant)
docker exec leaguetraining python -m app.admin allow 123456789012345678
docker exec leaguetraining python -m app.admin revoke 123456789012345678   # coupe aussi ses sessions
docker exec leaguetraining python -m app.admin list

# Après un nouveau patch : nouvelles icônes et nouveaux objets (puis redémarrer le conteneur)
docker exec leaguetraining python -m app.admin sync-ddragon

# Sauvegarde cohérente de la base, même pendant que le site tourne (à mettre dans un cron)
docker exec leaguetraining python -m app.admin backup /data/backups/app-$(date +%F).db
```

## Développer

```sh
# Back
cd backend
python -m venv .venv && .venv/Scripts/pip install -e ".[dev]"   # ou .venv/bin/pip sous Linux
.venv/Scripts/python -m pytest

# Synchroniser Data Dragon en local (aussi utilisé pour valider les vrais puzzles dans les tests)
DATA_DIR=../data .venv/Scripts/python -m app.admin sync-ddragon

# Lancer l'API (PUBLIC_ORIGIN doit être l'origine du front en dev)
DATA_DIR=../data PUZZLES_DIR=../puzzles STATIC_DIR=../frontend/dist PUBLIC_ORIGIN=http://localhost:5173 \
  DISCORD_CLIENT_ID=... DISCORD_CLIENT_SECRET=... .venv/Scripts/python -m uvicorn app.main:create_app --factory

# Front (proxy /api et /dd vers :8000)
cd frontend && npm install && npm run dev
npm test
```

## Écrire un puzzle

Ajoute un fichier YAML dans `puzzles/<rôle>/`. Les identifiants de champions, d'objets et de sorts sont ceux de Data Dragon (`LeeSin`, `MonkeyKing`, `3165`, `SummonerFlash`). Sur la minimap, `x` va de 0 (gauche) à 100 (droite) et `y` de 0 (haut) à 100 (bas). La base bleue est en bas à gauche.

Un puzzle invalide empêche l'app de démarrer, avec un message qui indique le fichier et l'erreur. Pour le vérifier avant de déployer : `pytest tests/test_puzzles.py::test_repo_puzzles_are_valid`.
