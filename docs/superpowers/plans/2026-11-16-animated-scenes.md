# Scènes animées — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Nouveau type de puzzle `scene` : minimap animée, jusqu'à 3 décisions enchaînées, fins fatales, écran de fin « ton chemin / chemin optimal » avec replays.

**Architecture:** Un modèle Pydantic `ScenePuzzle` ajouté à l'union discriminée existante, avec validation du graphe au chargement. Un service `services/scenes.py` avance dans le graphe ; la table `scene_steps` mémorise chaque nœud révélé. Côté front, des fonctions pures `lib/timeline.js` calculent l'état à l'instant t, et `ScenePlayer.svelte` les lit sur la minimap existante.

**Tech Stack:** Inchangée (FastAPI, Pydantic v2, SQLite, Svelte 5, Vitest). Aucune nouvelle dépendance.

**Spec:** `docs/superpowers/specs/2026-11-16-animated-scenes-design.md`

**À exécuter après la refonte visuelle** (`docs/superpowers/plans/2026-11-16-hextech-redesign.md`) : les composants front utilisent ses classes et tokens (`.panel`, `.btn`, `--lol-*`).

## Global Constraints

- Au plus 3 décisions par chemin ; dernier keyframe d'un clip à `t ≤ 20`.
- Exactement un choix `excellent` par nœud ; un choix `erreur` a obligatoirement un `ending` ; chaque choix a exactement un de `next` / `ending`.
- Points par étape : `POINTS[grade] * MULTIPLIER[difficulty]` (valeurs V1), additionnés ; 0 si la partie n'est pas `scored`.
- Grade de la tentative fermée = la plus basse note du chemin (`erreur` < `correct` < `excellent`) ; `attempts.choice_id` = id de la fin atteinte.
- Tolérance chrono par nœud : `settings.chrono_grace_s` (2 s), à partir de `scene_steps.started_at`.
- Jamais de `grade`, `explanation`, `consequence`, `next`, `ending`, `endings` ni d'autre nœud dans `/start` ou dans un `next` public.
- `prefers-reduced-motion` : le lecteur saute à l'état final de chaque clip.

## Review Focus

1. **Redémarrer une scène en cours** (rechargement de page au milieu) → `start` renvoie le nœud courant, son `started_at` d'origine et le même mode (Task 3, `test_restart_resumes_current_node`).
2. **Répondre à un nœud déjà répondu / après la fin** → 409, aucun point ajouté (Task 3, `test_answer_after_end_409`).
3. **Temps écoulé sur un choix `correct`** → note `erreur` mais la scène continue vers `next` (Task 3, `test_timeout_still_follows_choice`).
4. **Scène modifiée dans le YAML alors qu'une partie est en cours** (nœud courant supprimé) → `start` abandonne la tentative ouverte (fermée à 0 point) et en recommence une d'entraînement, sans 500 (Task 3, `test_current_node_removed_from_yaml`).
5. **Fuite de la suite dans la page** → aucune clé interdite dans les réponses publiques, vérifié récursivement sur tout le JSON (Task 3, `test_no_future_leaks`).

---

### Task 1: Modèle `ScenePuzzle` et validation du graphe

**Files:**
- Create: `backend/app/puzzles/types/scene.py`, `backend/tests/fixtures/puzzles/scene/scene-drake.yaml`, `backend/tests/test_scenes_model.py`
- Modify: `backend/app/puzzles/__init__.py` (ajouter aux unions), `backend/tests/test_puzzles.py` (`test_loads_fixture_puzzles` attend 3 puzzles)

**Interfaces:**
- Consumes: `PuzzleBase`, `PublicPuzzleBase`, `Strict`, `Grade` (V1 `types/base.py`) ; `Me` (V1 `types/decision.py`).
- Produces:
  - `ChampState(Strict)`: `champion: str`, `team: Literal["ally","enemy"] | None = None`, `x, y: float | None` (0-100), `me: bool | None`, `hidden: bool | None`, `dead: bool | None`.
  - `WardState(Strict)`: `id: str`, `team: ... | None`, `x, y: float | None`, `removed: bool = False`.
  - `Event(Strict)`: `type: Literal["ping","kill","objective"]`, `x, y: float`, `label: str = ""`.
  - `Keyframe(Strict)`: `t: float = Field(ge=0, le=20)`, `clock: str | None`, `champions: list[ChampState] = []`, `wards: list[WardState] = []`, `objectives: list[Objective] | None`, `caption: str | None`, `events: list[Event] = []`.
  - `Clip = list[Keyframe]` (validé : `t` strictement croissants, au moins 1 keyframe).
  - `SceneChoice(Strict)`: `id, text, grade, explanation`, `consequence: Clip`, `next: str | None`, `ending: str | None`.
  - `Node(Strict)`: `intro: Clip`, `question: str = "Que fais-tu ?"`, `time_limit: int = Field(15, ge=5, le=120)`, `choices: list[SceneChoice]` (2-4).
  - `Outcome(Strict)`: `drakes, towers, gold, kills, barons, heralds, grubs: int | None`.
  - `Ending(Strict)`: `title: str`, `outcome: Outcome`, `note: str = ""`.
  - `ScenePuzzle(PuzzleBase)` : `type: Literal["scene"]`, `me: Me`, `start: str`, `nodes: dict[str, Node]`, `endings: dict[str, Ending]`. Surcharge `choices` : le champ hérité n'existe pas pour une scène → `ScenePuzzle` redéfinit `choices: list = []` et désactive `_check_choices` de la base (la validation des choix est faite par nœud).
  - Méthodes : `public(stale) -> PublicScene` (vue du début : champs de `PublicPuzzleBase` avec `choices=[]`, + `me`) ; `public_node(node_id) -> PublicNode` (`id, intro, question, time_limit, choices: [{id, text}]`) ; `optimal_path() -> list[tuple[str, str]]` ((node_id, choice_id) en suivant les `excellent`) ; `ending_of(path) -> str` ; `clips_for(path: list[tuple[str,str]]) -> list[Clip]` (intro de chaque nœud puis conséquence du choix, dans l'ordre) ; `champion_refs()` (tous les `ChampState.champion` + `me.champion`).
- Validateur de graphe (`model_validator(mode="after")`), messages exacts :
  - `"start 'x' is not a node"`, `"choice n1.a: next 'x' is not a node"`, `"choice n1.a: ending 'x' is not an ending"`
  - `"choice n1.a: needs exactly one of next / ending"`, `"choice n1.a: an 'erreur' choice must end the scene"`
  - `"node n1: needs exactly one 'excellent' choice"`, `"scene graph has a cycle"`, `"a path has more than 3 decisions"`
  - `"node 'x' is unreachable"`, `"ending 'x' is unreachable"`
  - `"first keyframe of the start node must place exactly one 'me' champion, equal to me.champion"`

- [ ] **Step 1: Fixture** `scene-drake.yaml` : 2 nœuds (`n1` → b `excellent` → `n2` ; c `correct` → `n2` ; a `erreur` → `dead`), `n2` (a `erreur` → `lost` ; b `excellent` → `best`), 3 fins. Champions limités au cache fixture (Ahri, LeeSin, Jinx, Malphite, Zed, Soraka).
- [ ] **Step 2: Tests qui échouent** —

```python
def test_fixture_scene_loads(dd): p = load_catalog(FIXTURES / "puzzles", dd).get("scene-drake"); assert p.type == "scene"
def test_optimal_path(dd): assert scene(dd).optimal_path() == [("n1", "b"), ("n2", "b")]
def test_clips_for_path_order(dd): # intro n1, conséquence n1.b, intro n2, conséquence n2.b → 4 clips
def test_public_node_hides_future(dd): # json de public_node("n1") sans "grade","explanation","consequence","next","ending"
@pytest.mark.parametrize("mutation, message", [
    (lambda d: d["nodes"]["n1"]["choices"][0].update(ending=None, next="n2"), "must end the scene"),
    (lambda d: d["nodes"]["n2"]["choices"][1].update(next="n1", ending=None), "cycle"),
    (lambda d: d["nodes"]["n1"]["choices"][2].update(grade="excellent"), "exactly one 'excellent'"),
    (lambda d: d.update(start="zz"), "is not a node"),
    (lambda d: d["endings"].update(orphan={"title": "x", "outcome": {}}), "unreachable"),
    (lambda d: d["nodes"]["n1"]["intro"][1].update(t=0), "increasing"),
])
def test_graph_errors(tmp_path, dd, mutation, message): ...  # écrit le YAML muté, PuzzleLoadError contenant message
def test_more_than_three_decisions_rejected(tmp_path, dd): ...  # chaîne n1→n2→n3→n4
```

- [ ] **Step 3:** `cd backend && .venv/Scripts/python -m pytest tests/test_scenes_model.py -q` → FAIL.
- [ ] **Step 4:** Implémenter `scene.py` et l'ajouter aux unions. Détection de cycle et profondeur : DFS depuis `start` sur les arêtes `next`.
- [ ] **Step 5:** `pytest -q` → tout PASS.
- [ ] **Step 6:** Commit `feat: scene puzzle model with graph validation`.

---

### Task 2: Table `scene_steps` et repository

**Files:**
- Create: `backend/app/migrations/002_scene_steps.sql`, `backend/app/repositories/scene_steps.py`, `backend/tests/test_scene_steps_repo.py`
- Modify: `backend/tests/test_db.py` (`user_version == 2`)

**Interfaces:**
- Produces:
  - SQL : `create table scene_steps (id integer primary key, attempt_id integer not null references attempts(id) on delete cascade, node_id text not null, started_at text not null, answered_at text, choice_id text, grade text, points integer, timed_out integer not null default 0, unique(attempt_id, node_id));`
  - `create(conn, attempt_id, node_id, started_at) -> int` ; `current(conn, attempt_id) -> Row | None` (dernière non répondue) ; `close(conn, step_id, choice_id, grade, points, timed_out, answered_at) -> bool` (`... where id = ? and answered_at is null`, renvoie `rowcount == 1`) ; `path(conn, attempt_id) -> list[Row]` (répondues, par id) ; `distribution(conn, puzzle_id, node_id) -> list[Row]` (`user_id, discord_id, name, avatar, choice_id, grade` des étapes de tentatives `scored`).

- [ ] **Step 1: Tests qui échouent** : cycle create → current → close (renvoie True, puis False au 2e appel) → path ; unicité `(attempt_id, node_id)` ; distribution limitée aux tentatives scored.
- [ ] **Step 2:** `pytest tests/test_scene_steps_repo.py -q` → FAIL. **Step 3:** Implémenter. **Step 4:** `pytest -q` → PASS.
- [ ] **Step 5:** Commit `feat: scene_steps table and repository`.

---

### Task 3: Service et routes des scènes

**Files:**
- Create: `backend/app/services/scenes.py`, `backend/tests/test_scenes_api.py`
- Modify: `backend/app/routes/puzzles.py` (aiguillage `if p.type == "scene"`), `backend/app/services/attempts.py` (exporter `_puzzle` sous le nom `get_puzzle` pour réutilisation)

**Interfaces:**
- Consumes: `ScenePuzzle` (Task 1), `scene_steps` (Task 2), `attempts` repository et `POINTS`/`MULTIPLIER` (V1).
- Produces:
  - `scenes.start(conn, catalog, user_id, puzzle_id, mode, now) -> dict` : `{puzzle, mode, scored, started_at, step: {...public_node, started_at}}`. Reprend la tentative ouverte (scored d'abord, sinon la dernière d'entraînement **du même mode**) et son nœud courant ; si le nœud courant n'existe plus dans le YAML → ferme la tentative (`points=0`, `grade="erreur"`, `choice_id=None`) et en crée une nouvelle d'entraînement. Sinon crée la tentative (même gestion `IntegrityError` que la V1) et l'étape `start`.
  - `scenes.answer(conn, catalog, user_id, puzzle_id, choice_id, now, grace_s, tz) -> dict` : `{grade, points, timed_out, choices: [{id, text, grade, explanation}], consequence, distribution, next | end}`. Chrono : `mode == "chrono" and now - step.started_at > node.time_limit + grace_s` → `grade="erreur"`. Le choix cliqué détermine la suite dans tous les cas. Si `next` : crée l'étape suivante avec `started_at = now`. Si fin : ferme la tentative (somme des points, grade le plus bas, `choice_id = ending_id`, `answered_day`) et renvoie `end = {reached: {id, ...Ending}, optimal: {id, ...Ending}, path: [{node_id, choice_id, grade, points}], optimal_path: [{node_id, choice_id}], replay: {mine: [Clip], optimal: [Clip]}, total_points, lesson}`.
  - Erreurs : `NoOpenAttempt` (409) si aucune étape ouverte ; `UnknownChoice` (422) ; `close()` renvoyant False → 409.

- [ ] **Step 1: Tests qui échouent** (client HTTP, `clock` comme en V1) :

```python
def test_start_returns_first_node_only(...)          # step.id == "n1", pas de "n2" ni d'"endings" dans le JSON
def test_excellent_path_reaches_best_end(...)         # b puis b → end.reached.id == "best", total_points == 6 + 6 (moyen ×2)
def test_erreur_ends_immediately(...)                 # a sur n1 → end.reached.id == "dead", optimal.id == "best"
def test_end_payload_has_both_replays(...)            # len(replay.mine) == 2, len(replay.optimal) == 4
def test_restart_resumes_current_node(...)            # start, answer b, start → step.id == "n2", même started_at
def test_answer_after_end_409(...)
def test_timeout_still_follows_choice(...)            # chrono, n1 time_limit 15, réponse à +17.5 s sur c → grade erreur, next.id == "n2"
def test_current_node_removed_from_yaml(...)          # tentative ouverte sur n2, catalogue rechargé sans n2 → start 200, scored False
def test_no_future_leaks(...)                         # parcours récursif du JSON de /start et du next public : aucune clé interdite
def test_scene_counts_in_leaderboard_and_profile(...) # stats V1 inchangées, la scène compte avec ses points cumulés
def test_distribution_per_node(...)
```

- [ ] **Step 2:** `pytest tests/test_scenes_api.py -q` → FAIL. **Step 3:** Implémenter. **Step 4:** `pytest -q` → tout PASS.
- [ ] **Step 5:** Commit `feat: scene progression service and routes`.

---

### Task 4: Timeline (fonctions pures)

**Files:**
- Create: `frontend/src/lib/timeline.js`, `frontend/src/lib/timeline.test.js`

**Interfaces:**
- Produces:
  - `initialState()` → `{clock: "", caption: "", champions: {}, wards: {}, objectives: [], events: []}`.
  - `applyKeyframe(state, kf) -> state` : fusion (un champion ou une balise absents gardent leur état ; `removed` supprime la balise ; `objectives` remplace la liste s'il est fourni ; `events` = ceux du keyframe).
  - `stateAt(base, clip, t) -> state` : applique les keyframes `≤ t` ; positions `x, y` interpolées linéairement entre le dernier keyframe `≤ t` et le suivant **où ce champion a une position** ; `clock`/`caption`/`objectives` par paliers ; `events` visibles 1,5 s après leur keyframe.
  - `endState(base, clip) -> state` ; `duration(clip) -> number` (t du dernier keyframe).
  - `chain(clips) -> {clip, cuts}` : décale les `t` pour enchaîner plusieurs clips (0,6 s de pause entre deux), `cuts` = instants de début de chaque clip.

- [ ] **Step 1: Tests qui échouent** : interpolation à mi-chemin (`x` 10 → 30 à t=2 sur [0,4] → 20) ; champion absent d'un keyframe conserve sa position ; `hidden` appliqué au palier ; balise `removed` ; `chain` de deux clips de 4 s → durée 8,6 et `cuts == [0, 4.6]` ; event expiré après 1,5 s.
- [ ] **Step 2:** `npx vitest run src/lib/timeline.test.js` → FAIL. **Step 3:** Implémenter. **Step 4:** `npx vitest run` → PASS.
- [ ] **Step 5:** Commit `feat: scene timeline interpolation`.

---

### Task 5: Lecteur et vue des scènes

**Files:**
- Create: `frontend/src/components/ScenePlayer.svelte`, `frontend/src/components/puzzles/SceneView.svelte`, `frontend/src/components/SceneEnd.svelte`
- Modify: `frontend/src/components/Minimap.svelte` (prop `state` en alternative à `scene` : champions/balises/objectifs déjà résolus, fantômes `hidden`, croix `dead`, events), `frontend/src/components/puzzles/index.js` (`scene: SceneView`), `frontend/src/pages/Puzzle.svelte` (pour `type === "scene"`, déléguer tout le déroulé à `SceneView` après `start`)

**Interfaces:**
- Consumes: `timeline.js` (Task 4), `api.start` / `api.answer` (forme Task 3), `Countdown`, `ChoiceList`, `Avatar` (V1).
- Produces:
  - `ScenePlayer` props : `base` (état de départ), `clip`, `autoplay = true`, `onend`. Contrôles : lecture/pause, rejouer, passer (saute à `endState`). `requestAnimationFrame`, arrêt au démontage. `prefers-reduced-motion` → `endState` immédiat puis `onend`.
  - `SceneView` : machine à états `intro → choose → consequence → (intro du suivant | end)`. L'état de la carte est conservé d'un clip à l'autre (`endState` du clip précédent = `base` du suivant). Le chrono démarre à `step.started_at` du serveur, affiché seulement pendant `choose`. Après chaque réponse : note, explications du nœud, avatars des potes, puis « Continuer ».
  - `SceneEnd` : deux colonnes (ton chemin / chemin optimal) : titre de la fin, valeurs d'`outcome` signées (`+1 drake`, `−1500 PO`), différences en couleur (succès / échec de la palette), `note`, `total_points`, `lesson`. Boutons « Revoir mon chemin » / « Voir le chemin optimal » → `ScenePlayer` sur `chain(replay.mine | replay.optimal)`.

- [ ] **Step 1: Vérification manuelle** (back local + `scene-drake` en fixture) : intro animée puis figée, chrono visible seulement pendant le choix, conséquence jouée, 2e décision, fin ; chemin erreur → fin immédiate ; les deux replays jouent en entier ; rechargement au milieu → reprise au même nœud ; avec « réduire les animations » activé dans l'OS, aucun mouvement.
- [ ] **Step 2:** `npx vitest run && npm run build` → OK.
- [ ] **Step 3:** Commit `feat: scene player, scene view and end screen`.

---

### Task 6: Trois scènes de départ

**Files:**
- Create: `puzzles/jungle/scene-baron-call.yaml`, `puzzles/mid/scene-drake-1400.yaml`, `puzzles/support/scene-vision-baron.yaml`

- [ ] **Step 1:** Écrire les 3 scènes (2 à 3 décisions chacune, difficulté moyen à difficile), patch = version Data Dragon synchronisée. Chaque fin a un `outcome` chiffré et une `note`.
- [ ] **Step 2:** `cd backend && .venv/Scripts/python -m pytest tests/test_puzzles.py::test_repo_puzzles_are_valid -q` → PASS.
- [ ] **Step 3: Vérification manuelle** : jouer chaque scène jusqu'au chemin optimal et jusqu'à une fin fatale.
- [ ] **Step 4:** Commit `content: three starter animated scenes`.
