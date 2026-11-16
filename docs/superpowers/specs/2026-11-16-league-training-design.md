# LeagueTraining — Design V1

_Date : 2026-11-16 · Statut : à valider_

## 1. Intention

Un site d'entraînement à la **prise de décision** dans League of Legends, sur le modèle des puzzles d'échecs : une situation de jeu figée, « à toi de jouer », puis une explication.

**Pour qui :** le propriétaire du site (Platine/Émeraude) et un petit groupe de potes (Bronze/Silver). Quelques dizaines de comptes au maximum.

**Pourquoi :** les outils existants (op.gg, Mobalytics…) font des stats, presque aucun n'entraîne la décision. L'itemisation est en particulier trop négligée dans l'apprentissage du jeu.

**Ce qui fait le fun :** se comparer entre potes (puzzle du jour, voir ce que les autres ont répondu, classement).

## 2. Objectifs, non-objectifs, anti-objectifs

**Objectifs V1**
- Puzzles de **décision macro** (minimap + contexte → choix) et d'**itemisation** (compo + golds → achat).
- Trois difficultés : facile (Bronze/Silver), moyen (Silver/Gold), difficile (Plat/Émeraude). Les 5 rôles sont couverts.
- Mode normal et **mode chrono** (temps limité, mesuré par le serveur).
- Comptes via Discord, profil avec stats par rôle/difficulté, classement, **puzzle du jour** avec les réponses du groupe visibles après avoir répondu.
- Environ 30 puzzles de départ écrits par Claude, relus par le propriétaire.

**Non-objectifs V1** (roadmap, §10)
- Minimap interactive (poser des wards, tracer un pathing), simulateur de vagues, clips vidéo, flashcards de timers.
- Éditeur de puzzles dans le site, génération par IA, puzzles tirés de vraies parties via l'API Riot.
- Tout ce qui sert un site public : inscription ouverte, modération, classement par elo.

**Anti-objectifs** (ce qui serait un échec même si ça marche)
- Enseigner des choses fausses : un puzzle douteux vaut moins que pas de puzzle. D'où la relecture humaine et le marquage du patch.
- Une réponse unique « vraie/faux » sur des situations ambiguës : on note **Excellent / Correct / Erreur**, toujours avec une explication.
- Un serveur domestique qui devient une porte d'entrée vers le réseau de la maison.
- Une sur-architecture qui rend le projet pénible à faire évoluer.

## 3. Contraintes

- **Déploiement hors périmètre** : le propriétaire a déjà son tunnel Cloudflare, son nom de domaine et son déploiement Docker. Le projet livre **une image Docker** qui écoute sur un port HTTP, rien de plus.
- Back en **Python**, front en **JavaScript**.
- Sécurisé, performant, respect des principes SOLID.
- Assets Riot (icônes, objets) : usage non commercial, conformément à la politique de Riot pour les projets de fans.

## 4. Approches envisagées

| Approche | Pour | Contre |
|---|---|---|
| Next.js + Supabase + Vercel | Rapide, gratuit, zéro infra | Dépend de services externes, ne respecte pas les contraintes de stack et d'hébergement |
| Site statique + Firebase | Très simple au départ | Mal adapté aux classements/statistiques |
| **Auto-hébergé : FastAPI + SQLite + front JS, une image Docker** | Contrôle total, aucune dépendance payante, correspond à la stack voulue | Sécurité et sauvegardes à notre charge |

**Retenue : auto-hébergée**, choisie par le propriétaire (serveur domestique, Python/JS).

## 5. Architecture

```
            Image Docker unique (écoute sur :8000)
┌────────────────────────────────────────────────────────────┐
│  FastAPI / uvicorn                                         │
│   ├── /api/*     → routes JSON                             │
│   ├── /assets/*  → cache local Data Dragon                 │
│   ├── /*         → front Svelte compilé (statique, SPA)    │
│   ├── puzzles/*.yaml  (chargés + validés au démarrage)     │
│   └── /data/app.db    (SQLite, mode WAL, volume)           │
└────────────────────────────────────────────────────────────┘
```

- **Même origine** pour le front et l'API : pas de CORS, cookies simples. FastAPI sert le front avec `StaticFiles`.
- **Back :** FastAPI + Pydantic v2, SQLite via le module standard `sqlite3` (requêtes SQL écrites à la main, pas d'ORM pour 5 tables). Auth Discord avec `httpx` (OAuth2 en quelques fonctions, sans lib dédiée).
- **Front :** Vite + Svelte, SPA avec un routeur léger. Minimap en SVG.
- **Livrable :** un `Dockerfile` multi-étapes (build du front avec Node, puis image Python slim). Volumes attendus : `/data` (base + cache Data Dragon). Configuration par variables d'environnement, documentées dans `.env.example`.

### Organisation du dépôt

```
LeagueTraining/
  backend/         # app Python (détail ci-dessous)
  frontend/        # app Svelte (détail ci-dessous)
  puzzles/         # contenu YAML, un fichier par puzzle, rangé par rôle
  Dockerfile
  .env.example
```

Le contenu (`puzzles/`) est séparé du code. Relire ou ajouter un puzzle ne touche jamais au back ni au front.

### Structure du code back (SOLID là où ça sert)

```
backend/app/
  main.py            # création de l'app, montage des routes et du statique
  config.py          # paramètres lus depuis l'environnement (pydantic-settings)
  db.py              # connexion SQLite + migrations (fichiers .sql numérotés)
  routes/            # couche HTTP : parse, appelle un service, répond
  services/          # logique : score, chrono, puzzle du jour, classement
  repositories/      # SQL uniquement
  puzzles/
    loader.py        # lit les YAML, valide, construit le catalogue en mémoire
    types/
      base.py        # contrat PuzzleType
      decision.py
      itemization.py
  ddragon.py         # synchro et lecture du cache Data Dragon
  admin.py           # CLI : allow/revoke d'un identifiant Discord, sync ddragon
```

- **Responsabilité unique :** routes → services → repositories. Les services se testent sans serveur HTTP.
- **Ouvert/fermé + substitution :** chaque type de puzzle implémente le même contrat (`schema`, `public_view()` qui retire les réponses, `grade(choice)`). Ajouter la minimap ou le simulateur de vagues = ajouter une classe et l'enregistrer, sans toucher aux services.
- **Inversion de dépendances :** les services reçoivent leurs repositories et le catalogue par injection (`Depends` de FastAPI), ce qui permet de passer des faux objets dans les tests.
- **Pas d'abstraction spéculative :** pas d'interface pour la base tant qu'il n'y a que SQLite.
- **Ségrégation des interfaces :** la vue publique d'un puzzle (envoyée au navigateur) et sa vue complète (avec les réponses) sont deux modèles Pydantic distincts. Il est structurellement impossible de sérialiser une réponse par erreur dans `/start`.

**Cycle de vie d'une réponse :**
`POST /answer` → `routes/puzzles.py` (valide le corps) → `services/attempts.py` (retrouve la tentative ouverte, vérifie le chrono, demande la note au `PuzzleType`, calcule les points, enregistre via `repositories/attempts.py`) → renvoie la correction + la répartition du groupe.

### Structure du code front

```
frontend/src/
  main.js
  App.svelte          # routeur + garde « connecté ? »
  lib/
    api.js            # seul module qui appelle fetch : erreurs et 401 gérés en un seul endroit
    stores.js         # utilisateur courant
  pages/              # Accueil, Liste, Puzzle, Résultat, Classement, Profil, Connexion
  components/
    Minimap.svelte    # rendu SVG d'une scène
    ChoiceList.svelte
    Countdown.svelte
    puzzles/          # un composant de rendu par type de puzzle
      DecisionView.svelte
      ItemizationView.svelte
      index.js        # table type → composant (miroir du registre back)
```

Le même principe ouvert/fermé s'applique au front : un nouveau type de puzzle = un nouveau composant ajouté à `puzzles/index.js`.

## 6. Format des puzzles

Un fichier YAML par puzzle dans `puzzles/`. Exemple de décision :

```yaml
id: mid-drake-roam-01
type: decision
role: mid
difficulty: moyen          # facile | moyen | difficile
patch: "15.22.1"           # version Data Dragon au moment de l'écriture
title: "Drake dans 45 secondes"
context: >
  14:20. Ton bot lane vient de back. Le jungler adverse a été vu top il y a 10 s.
me: { champion: Ahri, hp: 70, mana: 55, gold: 850, summoners: [Flash, Ignite], items: [3165, 1056] }
time_limit: 20             # secondes, utilisé en mode chrono
scene:                     # coordonnées 0-100 sur la minimap
  champions:
    - { champion: Ahri,  team: ally,  x: 50, y: 50, me: true }
    - { champion: LeeSin, team: enemy, x: 20, y: 18, last_seen: 10 }
  wards: [ { team: ally, x: 62, y: 60 } ]
  objectives: [ { type: dragon, spawn_in: 45 } ]
choices:
  - id: a
    text: "Prendre les plates mid puis aller au drake"
    grade: erreur
    explanation: "..."
  - id: b
    text: "Push la vague et aller warder la rivière bot"
    grade: excellent
    explanation: "..."
lesson: "Préparer un objectif, c'est arriver avec la prio et la vision 30 à 60 s avant."
```

Les puzzles d'**itemisation** ont la même structure : `scene` est remplacé par la compo alliée/adverse, et les choix pointent vers des identifiants d'objets Data Dragon.

**Validation au chargement :** schéma Pydantic par type, identifiants uniques, champions et objets existant dans Data Dragon, au moins un choix `excellent`. Un puzzle invalide **empêche le démarrage**, avec un message clair. Un test pytest charge tous les YAML.

**Obsolescence :** si `patch` a plus de 2 patchs de retard sur la dernière version Data Dragon, le puzzle d'itemisation affiche un badge « peut être obsolète ».

## 7. Données (SQLite)

```
users        (id, discord_id UNIQUE, name, avatar, created_at)
allowlist    (discord_id PRIMARY KEY, added_at)
sessions     (token_hash PRIMARY KEY, user_id, expires_at)
attempts     (id, user_id, puzzle_id, mode, started_at, answered_at NULL,
              choice_id NULL, grade NULL, points NULL, scored BOOL)
              -- index unique partiel : UNIQUE(user_id, puzzle_id) WHERE scored
daily        (date PRIMARY KEY, puzzle_id)
```

- **Seule la première tentative compte** (`scored`, quel que soit le mode). On peut rejouer un puzzle pour s'entraîner, sans points. La répartition des réponses du groupe n'utilise que les tentatives `scored`.
- **Points :** excellent 3, correct 1, erreur 0, multipliés par la difficulté (facile ×1, moyen ×2, difficile ×3). Le classement agrège `points`. Un classement « puzzle du jour » séparé ne compte que les dailies.
- **Puzzle du jour :** attribué à la première requête de la journée (heure de Paris), tiré au hasard parmi les puzzles jamais sortis en daily (s'ils sont tous sortis : le plus ancien), puis figé dans `daily`. Tous les niveaux y passent, et le multiplicateur de difficulté compense.
- **Chrono :** `started_at` est fixé par le serveur au `start`. Au `answer`, si `answered_at - started_at > time_limit + 2 s` de tolérance réseau, la note devient `erreur` (temps écoulé).

## 8. API

| Méthode | Route | Rôle |
|---|---|---|
| GET | `/api/auth/login` | Redirige vers Discord (OAuth2 avec `state` et PKCE) |
| GET | `/api/auth/callback` | Vérifie `state`, contrôle l'allowlist, crée l'utilisateur et la session |
| POST | `/api/auth/logout` | Supprime la session |
| GET | `/api/me` | Profil et stats |
| GET | `/api/puzzles?role=&difficulty=&type=` | Liste (vue publique, sans réponses) + statut fait/pas fait |
| POST | `/api/puzzles/{id}/start` | `{mode}` : ouvre la tentative, renvoie la vue publique |
| POST | `/api/puzzles/{id}/answer` | `{choice}` : note, explications, répartition des réponses du groupe |
| GET | `/api/daily` | Puzzle du jour + qui l'a déjà fait |
| GET | `/api/leaderboard` | Classement général et daily |
| GET | `/api/users/{id}` | Profil d'un pote |

La répartition des réponses et les explications ne sont renvoyées **qu'après** la réponse de l'utilisateur.

## 9. Sécurité

L'exposition réseau (tunnel, TLS, HSTS) est gérée par l'infra existante du propriétaire. Côté application :

- **Accès fermé :** connexion uniquement via Discord **et** présence dans l'`allowlist`, gérée par la CLI `admin.py`. Tout autre compte Discord est refusé.
- **Sessions :** jeton aléatoire de 32 octets (`secrets`), stocké **haché** en base. Cookie `HttpOnly`, `Secure`, `SameSite=Lax`, expiration après 30 jours.
- **CSRF :** `SameSite=Lax` + vérification de l'en-tête `Origin` sur toutes les requêtes non-GET.
- **Validation :** tout ce qui entre passe par un modèle Pydantic. Le SQL est toujours paramétré.
- **Anti-triche :** les réponses ne quittent jamais le serveur avant la réponse du joueur. Score et chrono sont calculés côté serveur.
- **En-têtes :** CSP stricte (`default-src 'self'`, avec une exception pour les images `cdn.discordapp.com`), `X-Content-Type-Options`, `Referrer-Policy`, `frame-ancestors 'none'`.
- **Limitation de débit :** limite simple en mémoire sur `/api/auth/*`.
- **Image :** utilisateur non-root, compatible avec un système de fichiers en lecture seule (seul `/data` est écrit).
- **Secrets :** variables d'environnement (secret Discord, clé de session), jamais commitées, avec un `.env.example` fourni.
- **Dépendances :** versions épinglées.
- **Sauvegarde :** commande CLI `admin.py backup` (`sqlite3 .backup`, copie cohérente même pendant que le site tourne), à brancher sur ton cron.

## 10. Performance

À cette échelle, le sujet est le temps de chargement, pas la charge serveur.
- Puzzles en mémoire, aucune lecture disque par requête.
- Front compilé et minifié. Fichiers avec hash dans le nom, servis avec un cache de longue durée (`Cache-Control: immutable`), donc mis en cache aussi par Cloudflare.
- Images Data Dragon téléchargées une fois par patch et servies localement (pas de hotlinking).
- SQLite en mode WAL, index sur `attempts(user_id)` et `attempts(puzzle_id)`.

## 11. Front (écrans)

- **Connexion :** un bouton « Se connecter avec Discord ».
- **Accueil :** puzzle du jour (avec les avatars de ceux qui l'ont fait), progression personnelle, accès rapide par rôle.
- **Liste des puzzles :** filtres rôle / difficulté / type, statut fait ou pas fait.
- **Puzzle :** minimap SVG (ou compo pour l'itemisation), bloc contexte, choix, compte à rebours en mode chrono.
- **Résultat :** note, explication de chaque choix, leçon, ce qu'a répondu chaque pote.
- **Classement** et **profil** (stats par rôle et par difficulté).

Le style visuel est laissé au constructeur : sombre, lisible, dans l'esprit LoL sans copier l'interface du client.

## 12. Contenu de départ

Environ 30 puzzles : 10 par difficulté, répartis sur les 5 rôles, environ 70 % décision et 30 % itemisation. Ils sont écrits par Claude et **relus par le propriétaire avant publication**. Les puzzles d'itemisation sont à vérifier en priorité, car la connaissance du patch actuel par Claude peut être en retard.

## 13. Roadmap après la V1

1. Minimap interactive (wards, pathing, deviner la position du jungler).
2. Simulateur de vagues.
3. Flashcards de timers et de power spikes.
4. Génération de brouillons de puzzles par un LLM à partir des données du patch, avec validation humaine.
5. Puzzles tirés de vos vraies parties via l'API Riot.
6. Éditeur de puzzles dans le site, pour que les potes en créent.
7. Clips vidéo avec pause.

## 14. Laissé au constructeur

- Le design visuel et la conversion des coordonnées 0-100 vers l'image de la minimap.
- Le choix précis du routeur Svelte et de la lib OAuth.
- Le format exact des messages d'erreur de validation.
- Le découpage précis des migrations SQL.

## Choix faits par Claude (à vérifier)

- Svelte plutôt que React (plus léger ; à changer si tu préfères React).
- SQLite sans ORM.
- FastAPI sert aussi le front : une seule image, une seule origine.
- OAuth Discord écrit avec `httpx`, sans lib dédiée.
- Allowlist en base gérée par CLI, plutôt qu'en variable d'environnement (permet d'ajouter un pote sans redémarrer).
- Barème 3/1/0 × difficulté, et seule la première tentative compte.
- Puzzle du jour tiré au hasard puis figé, à l'heure de Paris.
- Tolérance de 2 s sur le chrono.
