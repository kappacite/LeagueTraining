# LeagueTraining V1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Site d'entraînement LoL fermé (potes uniquement) : puzzles de décision et d'itemisation, mode chrono, comptes Discord, puzzle du jour, classement.

**Architecture:** Une image Docker. FastAPI sert l'API `/api/*`, le cache Data Dragon `/dd/*` et le front Svelte compilé `/`. SQLite pour l'état ; puzzles en YAML chargés et validés au démarrage. Back en trois couches routes → services → repositories ; types de puzzles = modèles Pydantic d'une union discriminée.

**Tech Stack:** Python 3.12+, FastAPI, Pydantic v2, pydantic-settings, PyYAML, httpx, tzdata, sqlite3 (stdlib), pytest · Node 22, Vite, Svelte 5, Vitest.

**Spec:** `docs/superpowers/specs/2026-11-16-league-training-design.md`

## Global Constraints

- Difficultés : `facile | moyen | difficile` ; notes : `excellent | correct | erreur`.
- Points : excellent 3, correct 1, erreur 0, × difficulté (facile 1, moyen 2, difficile 3).
- Seule la première tentative d'un utilisateur sur un puzzle compte (`scored`), tous modes confondus.
- Tolérance chrono : 2 s (`chrono_grace_s = 2.0`). `time_limit` par défaut 20 s.
- Fuseau du puzzle du jour : `Europe/Paris`.
- Sessions : jeton `secrets.token_urlsafe(32)`, stocké haché SHA-256, cookie `session` `HttpOnly; Secure; SameSite=Lax`, 30 jours.
- Toute requête non-GET/HEAD sans `Origin` égal à `PUBLIC_ORIGIN` → 403.
- Les réponses (`grade`, `explanation`, `lesson`) ne sortent **jamais** avant `/answer`.
- Puzzle d'itemisation marqué `stale` si `patch` a plus de 2 versions de retard dans `versions.json` de Data Dragon.
- Pas d'ORM, SQL paramétré uniquement. Pas d'interface pour la base.
- **Écart au spec (voulu) :** le cache Data Dragon est servi sous `/dd/` et non `/assets/`, car Vite publie ses fichiers dans `/assets/`. Le front utilise un routeur par hash (`#/puzzle/id`), donc pas de fallback SPA côté serveur. L'écran « Résultat » est un composant de la page Puzzle, pas une route.
- Coordonnées minimap : `x` 0→100 de gauche à droite, `y` 0→100 de haut en bas (convention SVG) ; base bleue en bas à gauche.
- Identifiants champions/objets/sorts = identifiants Data Dragon (`LeeSin`, `MonkeyKing`, `3165`, `SummonerFlash`).

## Review Focus

1. **Redémarrer un puzzle chrono pour remettre le timer à zéro** → `start` sur une tentative `scored` ouverte renvoie la même tentative avec son `started_at` et son `mode` d'origine (Task 6, `test_restart_keeps_original_timer`).
2. **Répondre deux fois / répondre sans `start`** → 2ᵉ réponse : 409, pas de points en double ; sans tentative ouverte : 409 (Task 6).
3. **Un puzzle supprimé du YAML alors qu'il est en base** (tentatives, daily) → classement et profil fonctionnent, le daily du jour est réattribué (Task 7, `test_daily_reassigned_when_puzzle_removed`, `test_leaderboard_ignores_unknown_puzzles`).
4. **Un pote retiré de l'allowlist avec une session active** → ses sessions sont supprimées, requête suivante 401 (Task 4, `test_revoke_deletes_sessions`).
5. **Premier démarrage sans cache Data Dragon et sans réseau** → l'app s'arrête avec le message « Data Dragon cache missing and sync failed: … run `python -m app.admin sync-ddragon` » ; avec un cache présent, aucun appel réseau au démarrage (Task 8, `test_startup_uses_cache_without_network`).

---

### Task 1: Squelette back, config et base de données

**Files:**
- Create: `.gitignore`, `backend/pyproject.toml`, `backend/app/__init__.py`, `backend/app/config.py`, `backend/app/db.py`, `backend/app/migrations/001_init.sql`, `backend/tests/conftest.py`, `backend/tests/test_db.py`

**Interfaces:**
- Produces:
  - `Settings(BaseSettings)` : `data_dir: Path = Path("/data")`, `puzzles_dir: Path = Path("/app/puzzles")`, `static_dir: Path = Path("/app/static")`, `discord_client_id: str`, `discord_client_secret: str`, `public_origin: str` (ex. `https://lol.example.com`), `session_days: int = 30`, `chrono_grace_s: float = 2.0`, `timezone: str = "Europe/Paris"`. Propriété `discord_redirect_uri = f"{public_origin}/api/auth/callback"`, `db_path = data_dir / "app.db"`, `ddragon_dir = data_dir / "ddragon"`.
  - `db.connect(path: Path) -> sqlite3.Connection` : `row_factory = sqlite3.Row`, `PRAGMA journal_mode=WAL`, `PRAGMA foreign_keys=ON`.
  - `db.migrate(conn) -> None` : applique `migrations/NNN_*.sql` dans l'ordre, suivi par `PRAGMA user_version`.
  - Fixture pytest `conn` (base migrée dans `tmp_path`).

- [ ] **Step 1:** `git init`, `.gitignore` (`.env`, `__pycache__/`, `.venv/`, `node_modules/`, `frontend/dist/`, `data/`). `pyproject.toml` avec les dépendances épinglées (fastapi, uvicorn[standard], pydantic-settings, pyyaml, httpx, tzdata ; dev : pytest) et `[tool.pytest.ini_options] pythonpath = ["."]`.
- [ ] **Step 2: Test qui échoue** — `test_db.py` :

```python
def test_migrate_creates_tables_and_is_idempotent(tmp_path):
    conn = connect(tmp_path / "a.db"); migrate(conn); migrate(conn)
    names = {r["name"] for r in conn.execute("select name from sqlite_master where type='table'")}
    assert {"users", "allowlist", "sessions", "attempts", "daily"} <= names
    assert conn.execute("pragma user_version").fetchone()[0] == 1

def test_only_one_scored_attempt_per_user_puzzle(conn):
    # insérer un user, puis 2 attempts scored=1 sur le même puzzle → sqlite3.IntegrityError
```

- [ ] **Step 3:** Lancer `cd backend && pytest tests/test_db.py -v` → FAIL (import).
- [ ] **Step 4: `001_init.sql`** —

```sql
create table users (id integer primary key, discord_id text unique not null, name text not null,
  avatar text, created_at text not null);
create table allowlist (discord_id text primary key, added_at text not null);
create table sessions (token_hash text primary key, user_id integer not null references users(id) on delete cascade,
  expires_at text not null);
create table attempts (id integer primary key, user_id integer not null references users(id) on delete cascade,
  puzzle_id text not null, mode text not null check (mode in ('normal','chrono')),
  started_at text not null, answered_at text, answered_day text, choice_id text, grade text, points integer,
  timed_out integer not null default 0, scored integer not null);
create unique index attempts_one_scored on attempts(user_id, puzzle_id) where scored = 1;
create index attempts_puzzle on attempts(puzzle_id);
create table daily (date text primary key, puzzle_id text not null);
```

Dates stockées en ISO 8601 UTC (`datetime.isoformat()`). Implémenter `config.py` et `db.py`.
- [ ] **Step 5:** `pytest tests/test_db.py -v` → PASS.
- [ ] **Step 6:** Commit `feat: backend skeleton, settings, sqlite migrations`.

---

### Task 2: Data Dragon (synchro + chargement du cache)

**Files:**
- Create: `backend/app/ddragon.py`, `backend/tests/test_ddragon.py`, `backend/tests/fixtures/ddragon/` (cache minimal factice)

**Interfaces:**
- Produces:
  - `@dataclass(frozen=True) class DDragon: version: str; versions: list[str]; champions: dict[str, str]` (id → nom) `; items: dict[int, str]; summoners: dict[str, str]`
  - `class DDragonMissing(Exception)`
  - `load(cache_dir: Path) -> DDragon` : lit `versions.json`, `champion.json`, `item.json`, `summoner.json` du cache ; lève `DDragonMissing` si absent.
  - `sync(cache_dir: Path, client: httpx.Client) -> str` : récupère `https://ddragon.leagueoflegends.com/api/versions.json`, puis pour `versions[0]` les JSON `cdn/{v}/data/fr_FR/{champion,item,summoner}.json` et les images `img/champion/{id}.png`, `img/item/{id}.png`, `img/spell/{id}.png`, `img/map/map11.png` vers `cache_dir/img/...`. Écrit les JSON en dernier (un cache partiel n'est jamais pris pour complet). Retourne la version.
  - `patches_behind(patch: str, dd: DDragon) -> int` : index de `patch` dans `dd.versions` ; version inconnue → `len(dd.versions)`.
  - Fixture pytest `dd` (charge `tests/fixtures/ddragon/`) : champions `Ahri, LeeSin, Jinx, Malphite, Zed, Soraka` ; items `1056, 3165, 3033, 3123` ; sorts `SummonerFlash, SummonerDot` ; versions `["15.23.1","15.22.1","15.21.1","15.20.1"]`.

- [ ] **Step 1: Tests qui échouent** —

```python
def test_load_reads_fixture(dd): assert dd.version == "15.23.1" and "LeeSin" in dd.champions and 3165 in dd.items
def test_load_missing_raises(tmp_path): with pytest.raises(DDragonMissing): load(tmp_path)
def test_patches_behind(dd):
    assert patches_behind("15.23.1", dd) == 0 and patches_behind("15.20.1", dd) == 3
    assert patches_behind("14.1.1", dd) == 4
def test_sync_writes_loadable_cache(tmp_path):
    # httpx.Client(transport=httpx.MockTransport(handler)) qui sert des JSON minimaux et des PNG b"x"
    v = sync(tmp_path, client); assert load(tmp_path).version == v
```

- [ ] **Step 2:** `pytest tests/test_ddragon.py -v` → FAIL.
- [ ] **Step 3:** Implémenter `ddragon.py`. Items : les clés de `item.json` sont des chaînes, à convertir en `int`.
- [ ] **Step 4:** `pytest tests/test_ddragon.py -v` → PASS.
- [ ] **Step 5:** Commit `feat: data dragon sync and cache loader`.

---

### Task 3: Types de puzzles et chargeur YAML

**Files:**
- Create: `backend/app/puzzles/__init__.py`, `backend/app/puzzles/types/base.py`, `backend/app/puzzles/types/decision.py`, `backend/app/puzzles/types/itemization.py`, `backend/app/puzzles/loader.py`, `backend/tests/test_puzzles.py`, `backend/tests/fixtures/puzzles/` (1 décision + 1 itemisation valides)

**Interfaces:**
- Consumes: `DDragon`, `patches_behind` (Task 2).
- Produces:
  - `base.py` : `Grade = Literal["excellent","correct","erreur"]`, `Role = Literal["top","jungle","mid","adc","support"]`, `Difficulty = Literal["facile","moyen","difficile"]`.
    `class Choice(BaseModel): id: str; text: str; grade: Grade; explanation: str; items: list[int] = []`
    `class PublicChoice(BaseModel): id: str; text: str; items: list[int] = []`
    `class PuzzleBase(BaseModel, extra="forbid")` : `id, type, role, difficulty, patch, title, context: str`, `time_limit: int = Field(20, ge=5, le=120)`, `choices: list[Choice] = Field(min_length=2, max_length=5)`, `lesson: str`. Validateur : ids de choix uniques, au moins un `excellent`.
    Méthodes : `grade(choice_id: str) -> Choice | None` ; `champion_refs() -> set[str]` ; `item_refs() -> set[int]` (inclut les `items` des choix) ; `summoner_refs() -> set[str]` ; `public(stale: bool) -> PublicPuzzle` ; `summary() -> PuzzleSummary`.
    `class PuzzleSummary(BaseModel): id, type, role, difficulty, title`.
    `class PublicPuzzleBase(PuzzleSummary): patch, context, time_limit, choices: list[PublicChoice], stale: bool`.
  - `decision.py` : `DecisionPuzzle(PuzzleBase)` avec `type: Literal["decision"]`, `me: Me` (`champion: str; hp: int 0-100; mana: int | None 0-100; gold: int ≥0; summoners: list[str]; items: list[int]`), `scene: Scene` (`champions: list[ScenePlacement]` avec `champion, team: Literal["ally","enemy"], x, y: float 0-100, me: bool = False, last_seen: int | None` ; `wards: list[Ward]` `team, x, y` ; `objectives: list[Objective]` `type: str, spawn_in: int | None`). Validateur : exactement un `me: true`, et son champion = `me.champion`. `PublicDecision(PublicPuzzleBase)` ajoute `me`, `scene`.
  - `itemization.py` : `ItemizationPuzzle(PuzzleBase)` avec `type: Literal["itemization"]`, `me: ItemMe` (`champion, level: int 1-18, gold, items: list[int]`), `allies: list[str]`, `enemies: list[Enemy]` (`champion, items: list[int] = []`). `PublicItemization` ajoute `me, allies, enemies`.
  - `__init__.py` : `Puzzle = Annotated[DecisionPuzzle | ItemizationPuzzle, Field(discriminator="type")]`, `PublicPuzzle = PublicDecision | PublicItemization`. **Ajouter un type = ajouter une classe à ces deux unions.**
  - `loader.py` : `class PuzzleLoadError(Exception)` (message = toutes les erreurs, une ligne `fichier: erreur` chacune). `class Catalog` : `get(id) -> Puzzle | None`, `all() -> list[Puzzle]`, `filter(role=None, difficulty=None, type=None) -> list[Puzzle]`, `is_stale(p) -> bool` (`type == "itemization" and patches_behind(p.patch, dd) > 2`), `ids() -> set[str]`. `load_catalog(puzzles_dir: Path, dd: DDragon) -> Catalog` : lit `**/*.yaml` récursivement, `TypeAdapter(Puzzle)`, vérifie refs champions/objets/sorts dans `dd`, ids uniques entre fichiers ; collecte **toutes** les erreurs puis lève une seule `PuzzleLoadError`.

- [ ] **Step 1: Tests qui échouent** —

```python
def test_loads_fixture_puzzles(dd): cat = load_catalog(FIXTURES, dd); assert len(cat.all()) == 2
def test_public_view_has_no_answers(dd):
    for p in load_catalog(FIXTURES, dd).all():
        dumped = json.dumps(p.public(stale=False).model_dump())
        assert "grade" not in dumped and "explanation" not in dumped and "lesson" not in dumped
def test_grade_returns_choice(dd): ... p.grade("b").grade == "excellent"; p.grade("zz") is None
def test_errors_collected(tmp_path, dd):
    # 2 fichiers invalides : champion inconnu "Teemoo" + aucun choix excellent
    with pytest.raises(PuzzleLoadError) as e: load_catalog(tmp_path, dd)
    assert "Teemoo" in str(e.value) and "excellent" in str(e.value)
def test_duplicate_ids_rejected(tmp_path, dd): ...
def test_unknown_field_rejected(tmp_path, dd): ...  # extra="forbid" attrape les fautes de frappe
def test_stale_only_for_itemization(dd): ...  # patch "15.20.1" → stale pour itemization, pas pour decision
def test_repo_puzzles_are_valid(dd_real_or_skip):
    # charge ../puzzles/ avec le cache réel si DATA_DIR/ddragon existe, sinon pytest.skip
```

- [ ] **Step 2:** `pytest tests/test_puzzles.py -v` → FAIL.
- [ ] **Step 3:** Implémenter les modèles et le chargeur.
- [ ] **Step 4:** `pytest tests/test_puzzles.py -v` → PASS.
- [ ] **Step 5:** Commit `feat: puzzle types and validated yaml catalog`.

---

### Task 4: Repositories

**Files:**
- Create: `backend/app/repositories/{__init__,users,allowlist,sessions,attempts,daily}.py`, `backend/tests/test_repositories.py`

**Interfaces:**
- Produces (fonctions de module, premier argument `conn: sqlite3.Connection`, `now`/dates en `datetime` aware UTC) :
  - `users` : `upsert(conn, discord_id: str, name: str, avatar: str | None, now) -> int` ; `get(conn, user_id) -> sqlite3.Row | None` ; `all(conn) -> list[Row]`.
  - `allowlist` : `is_allowed(conn, discord_id) -> bool` ; `add(conn, discord_id, now)` ; `remove(conn, discord_id)` (supprime aussi les sessions de l'utilisateur correspondant) ; `all(conn) -> list[str]`.
  - `sessions` : `create(conn, token_hash, user_id, expires_at)` ; `user_id_for(conn, token_hash, now) -> int | None` (ignore les expirées) ; `delete(conn, token_hash)`.
  - `attempts` : `open_scored(conn, user_id, puzzle_id) -> Row | None` (scored, non répondue) ; `open_practice(conn, user_id, puzzle_id) -> Row | None` (dernière non scored non répondue) ; `has_scored(conn, user_id, puzzle_id) -> bool` ; `create(conn, user_id, puzzle_id, mode, started_at, scored: bool) -> int` ; `close(conn, attempt_id, choice_id, grade, points, timed_out: bool, answered_at, answered_day: str)` ; `get(conn, attempt_id) -> Row` ; `distribution(conn, puzzle_id) -> list[Row]` (`user_id, name, avatar, choice_id, grade` des scored répondues) ; `scored_answered(conn, user_id=None) -> list[Row]` (`user_id, puzzle_id, grade, points, answered_day`) ; `done_by(conn, puzzle_id) -> list[Row]` (users ayant une scored répondue).
  - `daily` : `get(conn, date: str) -> str | None` ; `set(conn, date, puzzle_id)` (upsert) ; `history(conn) -> dict[str, str]` (date → puzzle_id).

- [ ] **Step 1: Tests qui échouent** — un test par fonction non triviale, dont :

```python
def test_revoke_deletes_sessions(conn):
    uid = users.upsert(conn, "42", "a", None, NOW); allowlist.add(conn, "42", NOW)
    sessions.create(conn, "h", uid, NOW + timedelta(days=1))
    allowlist.remove(conn, "42")
    assert sessions.user_id_for(conn, "h", NOW) is None and not allowlist.is_allowed(conn, "42")
def test_expired_session_ignored(conn): ...
def test_upsert_updates_name_and_avatar(conn): ...  # même discord_id → même id, nouveau nom
def test_distribution_only_scored_answered(conn): ...
```

- [ ] **Step 2:** `pytest tests/test_repositories.py -v` → FAIL.
- [ ] **Step 3:** Implémenter (chaque écriture se termine par `conn.commit()`).
- [ ] **Step 4:** `pytest tests/test_repositories.py -v` → PASS.
- [ ] **Step 5:** Commit `feat: sqlite repositories`.

---

### Task 5: Authentification Discord, sessions, protections HTTP

**Files:**
- Create: `backend/app/services/__init__.py`, `backend/app/services/auth.py`, `backend/app/deps.py`, `backend/app/security.py`, `backend/app/routes/__init__.py`, `backend/app/routes/auth.py`, `backend/app/main.py` (version minimale, complétée en Task 8), `backend/tests/test_auth.py`
- Modify: `backend/tests/conftest.py` (fixtures `app`, `client`, `login(client, discord_id) -> int`)

**Interfaces:**
- Consumes: repositories `users`, `allowlist`, `sessions` (Task 4), `Settings` (Task 1).
- Produces:
  - `services/auth.py` : `hash_token(token: str) -> str` (sha256 hex) ; `new_session(conn, user_id, now, days) -> str` (renvoie le jeton en clair) ; `authorize_url(settings, state: str, code_challenge: str) -> str` (`https://discord.com/oauth2/authorize`, `response_type=code`, `scope=identify`, `code_challenge_method=S256`) ; `@dataclass DiscordUser(id: str, name: str, avatar: str | None)` (`name` = `global_name` sinon `username`) ; `fetch_discord_user(client: httpx.Client, settings, code, verifier) -> DiscordUser` (POST `https://discord.com/api/oauth2/token` puis GET `https://discord.com/api/users/@me`) ; `class NotAllowed(Exception)` ; `login(conn, du: DiscordUser, now, days) -> str` (lève `NotAllowed` si absent de l'allowlist, sinon upsert + session).
  - `deps.py` : `get_settings()`, `get_conn()` (une connexion par requête, fermée à la fin), `get_catalog(request)`, `get_dd(request)`, `get_http()` (httpx.Client, surchargé dans les tests), `get_now()` (`datetime.now(UTC)`, surchargé dans les tests), `current_user(...) -> sqlite3.Row` (cookie `session` → user, sinon 401).
  - `security.py` : middleware `origin_check` (non-GET/HEAD/OPTIONS : `Origin` doit valoir `settings.public_origin`, sinon 403 `{"detail":"bad origin"}`) ; middleware `security_headers` (`Content-Security-Policy: default-src 'self'; img-src 'self' https://cdn.discordapp.com; frame-ancestors 'none'`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: same-origin`) ; `RateLimiter(limit=20, window_s=60)` appliqué à `/api/auth/*`, clé = en-tête `CF-Connecting-IP` sinon `request.client.host`, 429 au-delà. `# ponytail: limite en mémoire, par process ; suffisant pour un seul worker`.
  - Routes : `GET /api/auth/login` (génère `state` + `verifier`, cookie `oauth` = `state.verifier` HttpOnly Secure Lax max-age 600, redirige) ; `GET /api/auth/callback?code&state` (state ≠ cookie → 400 ; `NotAllowed` → redirection `/#/login?error=not-allowed` ; succès → cookie `session` + redirection `/#/`) ; `POST /api/auth/logout` (supprime la session, efface le cookie, 204) ; `GET /api/me` → `{id, name, avatar_url}` (`https://cdn.discordapp.com/avatars/{discord_id}/{avatar}.png` ou `null`).
  - `main.py` : `create_app(settings: Settings | None = None, dd: DDragon | None = None, catalog: Catalog | None = None) -> FastAPI`.

- [ ] **Step 1: Tests qui échouent** — `fetch_discord_user` surchargé via `httpx.MockTransport` :

```python
def test_me_requires_session(client): assert client.get("/api/me").status_code == 401
def test_callback_rejects_bad_state(client): ...  # 400
def test_callback_not_allowed_redirects(client): ...  # location contient "not-allowed", pas de cookie session
def test_callback_allowed_sets_session(client, conn): ...  # puis GET /api/me → 200 avec le nom Discord
def test_post_without_origin_forbidden(client): assert client.post("/api/auth/logout").status_code == 403
def test_post_with_origin_ok(client): ...  # Origin = public_origin → 204
def test_security_headers_present(client): ...
def test_auth_rate_limited(client): ...  # 21e GET /api/auth/login en < 60 s → 429
def test_session_token_stored_hashed(client, conn): ...  # la valeur du cookie n'apparaît pas dans sessions
```

- [ ] **Step 2:** `pytest tests/test_auth.py -v` → FAIL.
- [ ] **Step 3:** Implémenter. PKCE : `verifier = secrets.token_urlsafe(48)`, `challenge = base64url(sha256(verifier))` sans `=`.
- [ ] **Step 4:** `pytest -v` → tout PASS.
- [ ] **Step 5:** Commit `feat: discord oauth login, sessions, origin check, security headers`.

---

### Task 6: Tentatives — start / answer, chrono, score

**Files:**
- Create: `backend/app/services/attempts.py`, `backend/app/routes/puzzles.py`, `backend/tests/test_attempts.py`
- Modify: `backend/app/main.py` (inclure le routeur)

**Interfaces:**
- Consumes: `Catalog`, `Puzzle.grade/public/summary` (Task 3) ; repository `attempts` (Task 4) ; `current_user`, `get_now` (Task 5).
- Produces:
  - `POINTS = {"excellent": 3, "correct": 1, "erreur": 0}`, `MULTIPLIER = {"facile": 1, "moyen": 2, "difficile": 3}`.
  - `class PuzzleNotFound(Exception)`, `class NoOpenAttempt(Exception)`, `class UnknownChoice(Exception)` → 404, 409, 422 dans les routes.
  - `start(conn, catalog, user_id, puzzle_id, mode: Literal["normal","chrono"], now) -> StartResult` (`puzzle: PublicPuzzle, mode, started_at: datetime, scored: bool`). Règles : si une scored ouverte existe → la renvoyer **telle quelle** (mode et `started_at` d'origine) ; sinon si pas encore de scored → en créer une ; sinon → tentative d'entraînement (`scored=False`) : réutiliser l'ouverte s'il y en a une, sinon en créer une.
  - `answer(conn, catalog, user_id, puzzle_id, choice_id, now, grace_s: float, tz: ZoneInfo) -> AnswerResult` (`grade, points: int, timed_out: bool, scored: bool, choices: list[Choice], lesson: str, distribution: list[{user_id, name, avatar_url, choice_id, grade}]`). Ferme la tentative ouverte (scored en priorité). Chrono : `now - started_at > time_limit + grace_s` → `grade="erreur"`, `timed_out=True`. Points = `POINTS[grade] * MULTIPLIER[difficulty]` si `scored`, sinon 0. `answered_day = now.astimezone(tz).date().isoformat()`.
  - Routes : `GET /api/puzzles?role&difficulty&type` → `[{...summary, done: bool, grade: Grade | None, stale: bool}]` ; `POST /api/puzzles/{id}/start` body `{mode}` → `StartResult` ; `POST /api/puzzles/{id}/answer` body `{choice}` → `AnswerResult`. Bodies validés par Pydantic (`mode` hors liste → 422).

- [ ] **Step 1: Tests qui échouent** (`now` injecté via la dépendance `get_now`) :

```python
def test_start_returns_public_view_only(client_logged): ...  # pas de "grade"/"explanation" dans le JSON
def test_answer_scores_with_multiplier(...): # puzzle "moyen", choix excellent → points == 6
def test_second_answer_is_409(...): ...
def test_answer_without_start_is_409(...): ...
def test_restart_keeps_original_timer(...):
    # start chrono à T, start normal à T+10 → même mode "chrono", même started_at
def test_chrono_timeout(...): # time_limit 20 ; réponse à T+22.5 → erreur, timed_out ; à T+21.5 → note normale
def test_replay_gives_no_points(...): # après une scored répondue : start + answer → scored False, points 0
def test_unknown_choice_422(...): ...
def test_unknown_puzzle_404(...): ...
def test_distribution_after_answer(...): # 2 users répondent, le 2e voit les 2 choix
def test_list_marks_done(...): ...
```

- [ ] **Step 2:** `pytest tests/test_attempts.py -v` → FAIL.
- [ ] **Step 3:** Implémenter `services/attempts.py` puis `routes/puzzles.py`.
- [ ] **Step 4:** `pytest -v` → PASS.
- [ ] **Step 5:** Commit `feat: puzzle attempts with chrono and scoring`.

---

### Task 7: Puzzle du jour, classement, profils

**Files:**
- Create: `backend/app/services/daily.py`, `backend/app/services/stats.py`, `backend/app/routes/community.py`, `backend/tests/test_community.py`
- Modify: `backend/app/main.py`

**Interfaces:**
- Consumes: repositories `daily`, `attempts`, `users` ; `Catalog`.
- Produces:
  - `daily.today(conn, catalog, now, tz, rng: random.Random) -> Puzzle` : date locale ; si `daily.get` renvoie un id présent dans le catalogue → ce puzzle ; sinon tirer `rng.choice` parmi `catalog.ids() - history.values()` (triés pour être déterministes avec la seed) ; si tous sont sortis → le puzzle dont la dernière sortie est la plus ancienne ; `daily.set`.
  - `stats.leaderboard(conn, catalog, daily_history: dict[str, str]) -> {"general": [...], "daily": [...]}`, chaque ligne `{user_id, name, avatar_url, points, answered}`, triée par points décroissants. Ignore les tentatives dont `puzzle_id` n'est plus dans le catalogue. « daily » = tentatives scored où `daily_history.get(answered_day) == puzzle_id`.
  - `stats.profile(conn, catalog, user_id) -> {user, total_points, by_role: {role: {answered, excellent, points}}, by_difficulty: {...}}`.
  - Routes : `GET /api/daily` → `{date, puzzle: summary, done_by: [{user_id, name, avatar_url}]}` ; `GET /api/leaderboard` ; `GET /api/users/{id}` (404 si inconnu).

- [ ] **Step 1: Tests qui échouent** —

```python
def test_daily_stable_within_day(...): # 2 appels le même jour → même puzzle
def test_daily_changes_at_paris_midnight(...): # 22:59 UTC et 23:01 UTC en hiver → deux dates différentes
def test_daily_no_repeat_until_exhausted(...): # catalogue de 2 → jours 1 et 2 distincts, jour 3 = celui du jour 1
def test_daily_reassigned_when_puzzle_removed(...):
def test_leaderboard_ignores_unknown_puzzles(...):
def test_leaderboard_daily_counts_only_same_day(...):
def test_profile_by_role(...):
def test_unknown_user_404(...):
```

- [ ] **Step 2:** `pytest tests/test_community.py -v` → FAIL.
- [ ] **Step 3:** Implémenter.
- [ ] **Step 4:** `pytest -v` → PASS.
- [ ] **Step 5:** Commit `feat: daily puzzle, leaderboard, profiles`.

---

### Task 8: Assemblage de l'app, fichiers statiques, CLI admin

**Files:**
- Create: `backend/app/admin.py`, `backend/tests/test_app.py`, `backend/tests/test_admin.py`
- Modify: `backend/app/main.py`

**Interfaces:**
- Consumes: tout ce qui précède.
- Produces:
  - `create_app` complet : lifespan → `connect` + `migrate` ; `dd` = paramètre ou `load(settings.ddragon_dir)` ; si `DDragonMissing` → tenter `sync` puis `load` ; si la synchro échoue → `RuntimeError("Data Dragon cache missing and sync failed: <cause>. Run `python -m app.admin sync-ddragon`")`. `catalog` = paramètre ou `load_catalog(settings.puzzles_dir, dd)` (une `PuzzleLoadError` empêche le démarrage). Montages : `/dd` → `settings.ddragon_dir / "img"`, `/` → `settings.static_dir` (`html=True`), si le dossier existe. Réponses sous `/assets/` : `Cache-Control: public, max-age=31536000, immutable`.
  - `GET /api/meta` → `{"ddragon_version": dd.version}` (affiché dans le pied de page du front).
  - `admin.py` (argparse, `python -m app.admin`) : `allow <discord_id>`, `revoke <discord_id>`, `list`, `sync-ddragon`, `backup <dest_path>` (`conn.backup(sqlite3.connect(dest))`).

- [ ] **Step 1: Tests qui échouent** —

```python
def test_startup_uses_cache_without_network(tmp_path, monkeypatch):
    # cache fixture copié dans data_dir ; httpx bloqué (monkeypatch qui lève) → l'app démarre, /api/meta OK
def test_startup_fails_clearly_without_cache_and_network(...): # RuntimeError dont le message contient "sync-ddragon"
def test_invalid_puzzle_blocks_startup(...):
def test_static_index_served(...): # static_dir avec index.html → GET / renvoie son contenu
def test_assets_immutable_cache(...):
def test_admin_allow_list_revoke(tmp_path): ...  # main(["allow","42"]) puis main(["list"]) affiche 42
def test_admin_backup_creates_readable_copy(tmp_path): ...
```

- [ ] **Step 2:** `pytest tests/test_app.py tests/test_admin.py -v` → FAIL.
- [ ] **Step 3:** Implémenter. `admin.main(argv: list[str] | None = None) -> int`.
- [ ] **Step 4:** `pytest -v` → tout PASS.
- [ ] **Step 5:** Commit `feat: app assembly, static serving, admin cli`.

---

### Task 9: Front — squelette, client API, routeur, connexion

**Files:**
- Create: `frontend/package.json`, `frontend/vite.config.js`, `frontend/index.html`, `frontend/src/main.js`, `frontend/src/App.svelte`, `frontend/src/app.css`, `frontend/src/lib/api.js`, `frontend/src/lib/router.js`, `frontend/src/lib/stores.js`, `frontend/src/pages/Login.svelte`, `frontend/src/lib/api.test.js`, `frontend/src/lib/router.test.js`

**Interfaces:**
- Consumes: routes `/api/me`, `/api/auth/*`, `/api/meta`.
- Produces:
  - `api.js` : `class ApiError extends Error { status }` ; `request(method, path, body?) -> Promise<any>` (`credentials: "same-origin"`, JSON ; 401 → `user.set(null)` et throw ; non-2xx → throw `ApiError`) ; `api = { me, logout, meta, puzzles(filters), start(id, mode), answer(id, choice), daily, leaderboard, profile(id) }`.
  - `router.js` : `parse(hash: string) -> { page: string, params: object, query: object }` (`""`/`"#/"` → `home` ; `#/puzzles` → `list` ; `#/puzzle/:id` → `puzzle` ; `#/leaderboard` ; `#/user/:id` → `profile` ; `#/login?error=…` → `login` ; inconnu → `home`) ; store `route` mis à jour sur `hashchange`.
  - `stores.js` : `user` (writable, `undefined` = chargement, `null` = déconnecté), `meta`.
  - `App.svelte` : charge `api.me()` au démarrage ; si `user === null` → `Login` ; sinon barre de navigation (Accueil, Puzzles, Classement, avatar → profil, déconnexion) + page courante. Helper `ddImg(kind, id)` → `/dd/{kind}/{id}.png` dans `lib/dd.js`.
  - `Login.svelte` : bouton « Se connecter avec Discord » → `location.href = "/api/auth/login"` ; message si `query.error === "not-allowed"` : « Ton compte Discord n'est pas sur la liste. Demande à l'admin de t'ajouter. »
  - `vite.config.js` : proxy dev `/api` et `/dd` → `http://localhost:8000`.

- [ ] **Step 1:** `npm create vite@latest frontend -- --template svelte`, retirer le contenu démo, ajouter `vitest`.
- [ ] **Step 2: Tests qui échouent** — `router.test.js` (chaque route ci-dessus, dont l'inconnue → `home`) ; `api.test.js` (`fetch` mocké : 401 → `user` vaut `null` et rejet `ApiError` status 401 ; 200 → JSON renvoyé).
- [ ] **Step 3:** `cd frontend && npx vitest run` → FAIL.
- [ ] **Step 4:** Implémenter.
- [ ] **Step 5:** `npx vitest run` → PASS ; `npm run build` → OK.
- [ ] **Step 6:** Commit `feat: frontend skeleton, api client, router, login`.

---

### Task 10: Front — page Puzzle (minimap, itemisation, chrono, résultat)

**Files:**
- Create: `frontend/src/lib/minimap.js`, `frontend/src/lib/minimap.test.js`, `frontend/src/components/Minimap.svelte`, `frontend/src/components/ChoiceList.svelte`, `frontend/src/components/Countdown.svelte`, `frontend/src/components/Result.svelte`, `frontend/src/components/puzzles/DecisionView.svelte`, `frontend/src/components/puzzles/ItemizationView.svelte`, `frontend/src/components/puzzles/index.js`, `frontend/src/pages/Puzzle.svelte`

**Interfaces:**
- Consumes: `api.start`, `api.answer` ; formes `PublicDecision`, `PublicItemization`, `AnswerResult` (Tasks 3, 6).
- Produces:
  - `minimap.js` : `toSvg(x, y, size) -> {cx, cy}` (`cx = x / 100 * size`, idem y), borné à `[0, size]`.
  - `Minimap.svelte` (props `scene`, `size = 400`) : image `/dd/map/map11.png`, icônes de champions rondes (bord bleu allié / rouge ennemi, halo pour `me`, opacité réduite + « vu il y a Ns » si `last_seen`), wards (petits losanges), objectifs listés sous la carte avec leur timer.
  - `puzzles/index.js` : `export const views = { decision: DecisionView, itemization: ItemizationView }`.
  - `Puzzle.svelte` : choix du mode (Normal / Chrono) → `api.start` ; rendu `views[puzzle.type]` + contexte + `ChoiceList` ; en chrono, `Countdown` depuis `started_at` du serveur (pas depuis l'horloge du clic) ; au clic → `api.answer` → `Result`. Badge « peut être obsolète (patch X) » si `stale`. Si `start` renvoie `scored: false` → bandeau « Déjà fait : entraînement, sans points ».
  - `Result.svelte` : note (couleur par grade), points, « Temps écoulé » si `timed_out`, chaque choix avec sa note et son explication, `lesson`, et pour chaque choix les avatars des potes qui l'ont pris. Mention « entraînement, pas de points » si `!scored`.

- [ ] **Step 1: Test qui échoue** — `minimap.test.js` : `toSvg(50, 50, 400)` → `{cx: 200, cy: 200}` ; `toSvg(120, -5, 400)` → `{cx: 400, cy: 0}`.
- [ ] **Step 2:** `npx vitest run` → FAIL. **Step 3:** Implémenter. **Step 4:** `npx vitest run` → PASS.
- [ ] **Step 5: Vérification manuelle** — back lancé avec les puzzles de `tests/fixtures/puzzles`, front `npm run dev` : jouer un puzzle décision et un puzzle d'itemisation en normal et en chrono, laisser expirer un chrono, vérifier dans l'onglet réseau que `/start` ne contient ni `grade` ni `explanation`.
- [ ] **Step 6:** Commit `feat: puzzle page with minimap, itemization view, chrono, result`.

---

### Task 11: Front — accueil, liste, classement, profil

**Files:**
- Create: `frontend/src/pages/Home.svelte`, `frontend/src/pages/List.svelte`, `frontend/src/pages/Leaderboard.svelte`, `frontend/src/pages/Profile.svelte`

**Interfaces:**
- Consumes: `api.daily`, `api.puzzles`, `api.leaderboard`, `api.profile` (Tasks 6, 7).
- Produces:
  - `Home` : carte « Puzzle du jour » (titre, rôle, difficulté, avatars de `done_by`, bouton Jouer), résumé perso (points, nombre de puzzles faits), raccourcis par rôle → `#/puzzles?role=…`.
  - `List` : filtres rôle / difficulté / type (synchronisés avec la query du hash), lignes avec statut fait (et note) ou à faire.
  - `Leaderboard` : onglets Général / Puzzles du jour.
  - `Profile` : totaux, tableau par rôle et par difficulté.

- [ ] **Step 1: Vérification manuelle** avec 2 utilisateurs (deux sessions créées par `login` en dev, ou deux navigateurs) : le daily affiche l'avatar de celui qui l'a fait, le classement se met à jour, les filtres de la liste fonctionnent après un rechargement de page.
- [ ] **Step 2:** `npm run build` → OK. Commit `feat: home, puzzle list, leaderboard, profile pages`.

---

### Task 12: Image Docker et documentation d'exploitation

**Files:**
- Create: `Dockerfile`, `.dockerignore`, `.env.example`, `README.md`

**Interfaces:**
- Produces: image qui écoute sur `8000`, volume `/data`.

- [ ] **Step 1:** `Dockerfile` multi-étapes : `node:22-alpine` (`npm ci && npm run build`) → `python:3.12-slim` ; copier `backend/app`, `puzzles/` vers `/app/puzzles`, `frontend/dist` vers `/app/static` ; utilisateur non-root `app` (uid 10001) propriétaire de `/data` ; `CMD ["uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]`. Un seul worker (SQLite + limiteur en mémoire).
- [ ] **Step 2:** `.env.example` : `DISCORD_CLIENT_ID`, `DISCORD_CLIENT_SECRET`, `PUBLIC_ORIGIN`. `README.md` : créer l'app Discord (redirect `PUBLIC_ORIGIN/api/auth/callback`), `docker run` avec `-v …:/data --read-only --tmpfs /tmp`, ajouter un pote (`docker exec … python -m app.admin allow <id>`), sauvegarde (`… backup /data/backup.db` dans un cron), resynchro Data Dragon après un patch, lancer les tests.
- [ ] **Step 3: Vérification** — `docker build -t leaguetraining .` puis `docker run --rm -p 8000:8000 --read-only --tmpfs /tmp -v "$PWD/data:/data" --env-file .env leaguetraining` : `curl -s localhost:8000/api/meta` renvoie une version, `curl -I localhost:8000/` → 200 avec l'en-tête CSP, `docker exec <id> id -u` → `10001`.
- [ ] **Step 4:** Commit `build: docker image and operations readme`.

---

### Task 13: Contenu de départ (30 puzzles)

**Files:**
- Create: `puzzles/{top,jungle,mid,adc,support}/*.yaml`

**Interfaces:**
- Consumes: schémas de la Task 3 ; identifiants du cache Data Dragon synchronisé (`python -m app.admin sync-ddragon`).

- [ ] **Step 1:** Écrire 30 puzzles : 10 par difficulté, au moins 5 par rôle, 21 décisions et 9 itemisations. `patch` = version Data Dragon synchronisée. Chaque choix a une explication qui dit **pourquoi**, pas seulement quoi ; chaque puzzle a une `lesson` d'une phrase. Facile = fondamentaux (vision, objectifs après un fight gagné, ne pas chase) ; moyen = timings de back, gestion simple des vagues, réaction à la compo ; difficile = préparation d'objectif, slow push avant un roam, itemisation situationnelle fine.
- [ ] **Step 2:** `cd backend && pytest tests/test_puzzles.py::test_repo_puzzles_are_valid -v` → PASS (pas SKIP : le cache doit être présent).
- [ ] **Step 3:** Commit `content: 30 starter puzzles` et **signaler au propriétaire** que les puzzles d'itemisation sont à relire en priorité (méta du patch actuel).

---

## Self-review (fait)

- Couverture du spec : comptes Discord + allowlist (T4, T5), décision + itemisation (T3, T10), difficultés + multiplicateur (T3, T6), chrono côté serveur (T6), daily à l'heure de Paris (T7), classement + profil (T7, T11), anti-triche (T3 `public`, T6), en-têtes/CSRF/rate limit (T5), obsolescence (T3, T10), sauvegarde (T8), Data Dragon local (T2, T8), image Docker non-root (T12), contenu (T13).
- Types : `PublicPuzzle`, `Choice`, `StartResult`, `AnswerResult`, `Catalog.ids/get/filter/is_stale` utilisés avec les mêmes noms en T6, T7, T10.
