# Scènes animées à embranchements — Design

_Date : 2026-11-16 · Statut : à valider · S'appuie sur la V1 (`2026-11-16-league-training-design.md`)_

## 1. Intention

Rendre les puzzles **immersifs** : la situation se construit sous les yeux du joueur sur la minimap, comme un replay, puis la partie continue selon ses choix. Le joueur apprend à **lire la carte en mouvement** avant de décider, et voit **ce que ses décisions ont coûté** par rapport au chemin optimal.

Public, comptes, classement et sécurité : inchangés par rapport à la V1.

## 2. Objectifs, non-objectifs, anti-objectifs

**Objectifs**
- Un nouveau type de puzzle `scene`, à côté de `decision` et `itemization`, qui restent inchangés.
- Une scène enchaîne **jusqu'à 3 décisions**. Chaque décision est précédée d'une **animation d'intro** (≈ 5 à 10 s) : déplacements, apparitions dans le brouillard, balises, objectifs, chrono de jeu, sous-titres. Puis la scène se fige et les choix apparaissent.
- Après chaque choix, une **animation de conséquence** propre à ce choix se joue.
- **Fatalité** : un choix `erreur` mène toujours à une fin de scène. Un choix `correct` ou `excellent` mène à la décision suivante ou à une fin. Plusieurs choix peuvent mener au même nœud suivant (les branches se rejoignent).
- **Écran de fin** : bilan du chemin du joueur et bilan du chemin optimal, côte à côte (drakes, tours, or, kills, objectifs…). Boutons « Revoir mon chemin » et « Voir le chemin optimal », qui rejouent les animations enchaînées.
- **Score** : chaque décision est notée comme aujourd'hui (3/1/0 × difficulté), et les points s'additionnent sur le chemin. Seule la première partie compte.
- **Mode chrono** : le temps limite s'applique à chaque décision, à partir du moment où ses choix sont affichés.
- **Anti-triche** : le serveur n'envoie jamais un nœud, une conséquence ou une fin avant que le joueur y arrive.
- Contenu de départ : **3 scènes** écrites par Claude, relues par le propriétaire.

**Non-objectifs (plus tard)**
- Éditeur visuel de scènes (à faire si l'écriture à la main devient pénible).
- Continuer la partie après une erreur grave pour apprendre à se rattraper.
- Son, caméra hors minimap, 3D.

**Anti-objectifs**
- Une animation qui ralentit le joueur : on doit pouvoir passer l'intro, la rejouer et la mettre en pause.
- Un format si verbeux que personne n'écrit de scène.
- Révéler la suite d'une scène dans le code de la page.

## 3. Contraintes

- Même stack que la V1 : FastAPI, SQLite, Svelte 5. **Aucune nouvelle dépendance** : l'animation utilise `svelte/motion` et `requestAnimationFrame`.
- Réutiliser la minimap SVG existante.
- Respecter `prefers-reduced-motion` : les animations sautent directement à leur état final.
- Un puzzle invalide empêche toujours le démarrage.

## 4. Approches

| Approche | Pour | Contre |
|---|---|---|
| **Étapes-clés interpolées en SVG (retenue)** | Réutilise la minimap, léger, aucune dépendance, suit les choix | Positions à écrire à la main |
| Moteur de jeu (Canvas, PixiJS) | Effets riches | Lourd, nouvelle dépendance, inutile pour des icônes qui se déplacent |
| Clips vidéo | Très immersif | Ne peut pas suivre les choix, gros travail par clip, hébergement |

## 5. Format YAML

```yaml
id: scene-drake-1400
type: scene
role: mid
difficulty: moyen
patch: "16.22.1"
title: "Le drake de 14 minutes"
context: "Ton bot vient de back. Le drake apparaît à 14:00."
me: { champion: Ahri, hp: 75, mana: 60, gold: 850, summoners: [SummonerFlash, SummonerDot], items: [1056] }
start: n1
lesson: "Prépare l'objectif : prio, vision, puis le nombre."

nodes:
  n1:
    intro:                       # animation avant la décision
      - t: 0                     # secondes depuis le début du clip
        clock: "13:10"           # chrono de jeu affiché
        champions:               # état complet au premier keyframe d'une scène
          - { champion: Ahri, team: ally, x: 50, y: 50, me: true }
          - { champion: LeeSin, team: enemy, x: 30, y: 30 }
        wards: [ { id: w1, team: ally, x: 62, y: 60 } ]
        objectives: [ { type: dragon, spawn_in: 50 } ]
        caption: "Lee Sin farm son camp du haut."
      - t: 4
        clock: "13:14"
        champions:               # keyframes suivants : seulement ce qui change
          - { champion: LeeSin, x: 22, y: 18, hidden: true }   # entre dans le brouillard
        caption: "Il disparaît vers le top."
    question: "Que fais-tu ?"
    time_limit: 15
    choices:
      - id: a
        text: "Prendre les plates mid"
        grade: erreur
        explanation: "…"
        consequence: [ …keyframes… ]
        ending: dead_plates      # erreur ⇒ ending obligatoire
      - id: b
        text: "Push et warder la rivière bot"
        grade: excellent
        explanation: "…"
        consequence: [ …keyframes… ]
        next: n2                 # nœud suivant (ou ending)
  n2: { … }

endings:
  dead_plates:
    title: "Mort à 13:52, drake perdu"
    outcome: { drakes: -1, towers: 0, gold: -1100, kills: -1 }
    note: "Lee Sin et Syndra prennent le drake à 4 contre 3."
  best:
    title: "Drake + 2 tours"
    outcome: { drakes: 1, towers: 2, gold: 2400, kills: 2 }
```

**Keyframes**
- Le **premier keyframe du premier clip** d'une scène donne l'état complet. Chaque keyframe suivant (dans un clip, ou au début du clip suivant) ne contient que **ce qui change**. Le moteur fusionne les états.
- Champions identifiés par leur id Data Dragon. Champs : `team`, `x`, `y` (0-100), `me`, `hidden` (dans le brouillard, affiché en fantôme à sa dernière position connue), `dead`.
- Balises identifiées par `id`. `removed: true` pour les retirer.
- `events` (optionnel) : `{ type: ping | kill | objective, x, y, label }`, affiché brièvement à l'instant du keyframe.
- Les positions sont **interpolées linéairement** entre deux keyframes. `clock`, `caption`, `objectives` et `events` changent par paliers.

**Outcome** : champs entiers optionnels `drakes`, `towers`, `gold`, `kills`, `barons`, `heralds`, `grubs`, plus `note` en texte libre. Les valeurs sont **relatives à la situation de départ** de la scène.

**Validation au chargement** (en plus des règles V1 : refs Data Dragon, ids uniques, champs inconnus refusés)
- `start` et chaque `next` pointent vers un nœud existant ; chaque `ending` vers une fin existante.
- Chaque choix a **exactement un** de `next` / `ending`. Un choix `erreur` a obligatoirement un `ending`.
- Chaque nœud a **exactement un** choix `excellent` : le chemin optimal est unique.
- Le graphe est **acyclique**, et tout chemin depuis `start` fait **au plus 3 décisions**.
- Tous les nœuds et toutes les fins sont atteignables.
- Les `t` sont croissants dans un clip, et `t` du dernier keyframe ≤ 20 s.
- Le premier keyframe de `start.intro` contient exactement un champion `me: true`, égal à `me.champion`.

## 6. Données

Nouvelle table (migration `002_scene_steps.sql`) :

```
scene_steps (id, attempt_id → attempts, node_id, started_at, answered_at NULL,
             choice_id NULL, grade NULL, points NULL, timed_out,
             UNIQUE(attempt_id, node_id))
```

- La ligne `attempts` existante représente la partie entière : `started_at` = début de la scène, `mode`, `scored`. Elle est fermée quand une fin est atteinte, avec `points` = somme des étapes, `grade` = **la plus basse** note du chemin (pour les stats « excellent » du profil), `choice_id` = id de la fin atteinte.
- Une `scene_steps` est créée quand un nœud est révélé ; `started_at` sert au chrono de ce nœud.
- La règle « une seule tentative scored ouverte » de la V1 s'applique : redémarrer une scène en cours renvoie le nœud courant avec son `started_at` d'origine.

## 7. API

Mêmes routes, réponses étendues pour `type: scene` :

- `POST /api/puzzles/{id}/start` → `{ puzzle: <vue publique : titre, contexte, me>, mode, scored, step: <nœud courant public> }`. Nœud public = `id`, `intro` (keyframes), `question`, `time_limit`, choix (`id`, `text`), `started_at`. Jamais `grade`, `explanation`, `consequence`, `next`, `ending`.
- `POST /api/puzzles/{id}/answer` `{ choice }` → note de l'étape (`grade`, `points`, `timed_out`, `explanation` de chaque choix du nœud), `consequence` du choix fait (en cas de temps écoulé : la conséquence du choix fait est jouée quand même, la note devient `erreur`, et la scène se termine sur la fin de ce choix si c'est une `erreur`, sinon elle continue), répartition des potes sur ce nœud, puis **soit** `next: <nœud public suivant>`, **soit** `end` :
  ```
  end: { reached: <fin atteinte>, optimal: <fin du chemin optimal>,
         path: [ {node_id, choice_id, grade, points} ],
         optimal_path: [ {node_id, choice_id} ],
         replay: { mine: [clips enchaînés], optimal: [clips enchaînés] },
         total_points, lesson }
  ```
  Le chemin optimal et ses clips ne sont révélés qu'à la fin.
- Liste, daily, classement et profil : inchangés (une scène est un puzzle comme un autre).

## 8. Back (organisation)

- `puzzles/types/scene.py` : modèles (`Keyframe`, `Clip`, `Choice` étendu avec `consequence/next/ending`, `Node`, `Ending`, `Outcome`, `ScenePuzzle`), validation du graphe, `public()` (vue du début), `public_node(node_id)`, `optimal_path()`, `clips_for(path)`.
- `ScenePuzzle` ajouté aux unions `Puzzle` / `PublicPuzzle`.
- `services/scenes.py` : `start` et `answer` pour les scènes (avancer dans le graphe, chrono par nœud, fermer la tentative à la fin). `routes/puzzles.py` aiguille vers ce service quand `type == "scene"`, les autres types gardent `services/attempts.py`.
- `repositories/scene_steps.py` : SQL de la nouvelle table.

## 9. Front

- `lib/timeline.js` : fonctions pures et testées. `stateAt(keyframes, t)` (fusion des états + interpolation), `chain(clips)` (enchaîne plusieurs clips en une seule timeline).
- `components/ScenePlayer.svelte` : lit une timeline sur la minimap (`requestAnimationFrame`), avec lecture/pause, rejouer, passer. Sous-titres sous la carte, chrono de jeu en haut. Les champions `hidden` apparaissent en fantôme. Les `events` s'affichent brièvement (ping, croix de kill). Avec `prefers-reduced-motion`, saut direct à l'état final.
- `Minimap.svelte` accepte un état (champions, balises, objectifs) au lieu d'une scène figée. `DecisionView` continue de l'utiliser tel quel.
- `components/puzzles/SceneView.svelte` : enchaîne intro → choix (avec `Countdown` en chrono) → conséquence → choix suivant ou fin. Affiché à la place de la page Puzzle classique pour `type: scene`.
- `components/SceneEnd.svelte` : bilan côte à côte (ton chemin / chemin optimal), différences mises en couleur, points totaux, leçon, boutons « Revoir mon chemin » et « Voir le chemin optimal ».

## 10. Contenu de départ

3 scènes de 2 à 3 décisions, sur des rôles différents (jungle, mid, support), de difficulté moyenne à difficile, sur des thèmes macro déjà validés par les puzzles V1 (préparation du drake, appel Baron, contrôle de vision). Relues par le propriétaire.

## 11. Laissé au constructeur

- Style exact des fantômes, pings et croix de kill.
- Vitesse de lecture par défaut et présence d'un bouton ×2.
- Mise en page exacte de l'écran de fin, dans le style de la V1.

## Choix faits par Claude (à vérifier)

- Keyframes en **différences** après le premier (moins d'écriture), interpolation linéaire.
- **Un seul choix `excellent` par nœud** pour que le chemin optimal soit unique.
- Note de la partie entière = la plus basse note du chemin (utilisée seulement pour les stats du profil).
- En chrono, temps écoulé = `erreur`, mais la scène suit quand même le choix cliqué.
- Valeurs du bilan **relatives** au début de la scène.
- 3 scènes de départ.
