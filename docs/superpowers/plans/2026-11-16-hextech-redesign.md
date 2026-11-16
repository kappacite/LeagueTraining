# Refonte visuelle Hextech — Design et plan

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:executing-plans. Travail visuel : la vérification se fait par captures d'écran à chaque page, plus `npx vitest run && npm run build` et la suite back (aucune régression fonctionnelle).

**Goal:** Donner au front l'apparence d'une extension du client League of Legends (or métallique, panneaux bleu nuit, effets Hextech) sur 100 % des pages, sans toucher aux fonctionnalités, à la logique ni aux API.

**Spec:** le brief du propriétaire (message du 2026-11-16, « REFONTE UI/UX — DIRECTION ARTISTIQUE LEAGUE OF LEGENDS / HEXTECH »). Les décisions ci-dessous l'appliquent ; en cas de doute, le brief fait foi.

## Décisions

- **Palette :** exactement les variables `--lol-*` du brief, dans `frontend/src/app.css`. Les anciennes variables (`--river`, `--bank`…) sont supprimées, et toutes leurs utilisations sont remplacées.
- **Polices (validé par le propriétaire) :** équivalents libres, annoncés comme tels. **Cinzel** (OFL) pour `--font-display`, à la place de Beaufort for LoL. **Source Sans 3** (OFL) pour `--font-body`, à la place de Spiegel. Les deux sont auto-hébergées via `@fontsource`, ce qui respecte la CSP. Barlow est retirée. Pour passer aux vraies polices, il suffit de remplacer les deux variables.
- **Composants partagés** (classes globales dans `app.css`, aucun nouveau framework) :
  - `.panel` : dégradé vertical bleu nuit, bordure or sombre de 1 px, coins coupés (`clip-path`) et ornements de coin en pseudo-éléments, ombre noire profonde, lumière venant du haut. `.panel.interactive:hover` : bordure plus claire, légère lueur cyan, élévation de 2 px, 250 ms.
  - `.btn` (primaire) : fond bleu noir, cadre or métallique en dégradé (`--lol-gold-dark` → `--lol-gold` → `--lol-gold-dark`), texte ivoire en capitales, coins géométriques, illumination au survol et enfoncement à l'appui. `.btn.secondary` : bordure bronze, texte or désaturé. `.btn.hextech` : accent cyan avec un reflet animé lent.
  - `.ornament` : ligne horizontale dorée avec un losange central, pour séparer les sections.
  - `.diamond` : petit losange Hextech utilisé comme puce.
  - Champs et `select` : fond noir bleuté, bordure bronze, focus cyan.
- **Navigation :** barre supérieure sombre, onglets en capitales séparés par de fins filets dorés, onglet actif souligné par une ligne dorée lumineuse avec une transition de 250 ms.
- **Fond global :** `components/HextechBackground.svelte`, un canvas 2D en `position: fixed` : dégradé radial bleu nuit, vignettage, halos turquoise qui dérivent lentement, particules cyan (≈ 60 sur desktop, 20 sur mobile), grain en CSS. Il se met en pause quand l'onglet est caché, et il est statique (sans particules) avec `prefers-reduced-motion`. Pas de WebGL : aucune bibliothèque n'est présente et le gain ne vaut pas la dépendance.
- **Feedback :** sur une note « Excellent », bref flash Hextech et gerbe de particules dorées et turquoise (canvas éphémère, 800 ms). Sur « Erreur », un assombrissement rouge sombre contenu, sans flash. Le chrono passe de l'or au rouge sombre sous 5 s.
- **Progression (données réelles uniquement) :** sur le profil, un médaillon par rôle avec un anneau de maîtrise SVG (taux de réponses « Excellent » parmi les puzzles faits) et le total de points. Barres Hextech par difficulté. Sur l'accueil, les mêmes chiffres en cadre doré. Pas de graphique ni de rang inventé.
- **Pages :** toutes (Connexion, Accueil, Puzzles, Puzzle avec ses vues décision et itemisation, Résultat, Classement, Profil, en-tête, pied de page) passent sur ces composants. La minimap est sertie dans un cadre doré.
- **Animations :** apparition des panneaux en 300 ms (un seul enchaînement par page), transition de page en fondu de 350 ms, survols de 200 ms. Tout est coupé avec `prefers-reduced-motion`.
- **Mentions :** le pied de page garde « Projet de fans, non affilié à Riot Games ». Aucun logo Riot.

## Tâches

1. **Fondations** : tokens, polices, composants globaux (`.panel`, `.btn`, `.ornament`, champs), `HextechBackground`, en-tête, pied de page, transition de page. Vérif : build, tests, capture de l'accueil.
2. **Connexion et Accueil** : écran de connexion majestueux, puzzle du jour en panneau principal, statistiques en cadre doré, raccourcis par rôle en tuiles. Vérif : captures.
3. **Liste, Classement, Profil** : liste en lignes-panneaux avec un badge de difficulté distinctif, classement façon écran Ranked (podium de 3 avec bordures or), profil avec médaillons de maîtrise. Vérif : captures.
4. **Page Puzzle** : briefing, minimap sertie, choix en boutons-panneaux, chrono, correction avec flash et particules, vue itemisation. Vérif : captures de bout en bout (normal, chrono, Excellent, Erreur).
5. **Responsive et accessibilité** : 375 px sans débordement horizontal, focus visible, contraste, réduction des animations. Vérif : captures mobiles, suite de tests complète.

Un commit par tâche.
