# CLAUDE.md — Guide de travail pour Claude sur Best Annuaire

Ce fichier est lu automatiquement par Claude Code au début de chaque session.
Il décrit **l'état actuel du site** (à respecter, pas à réécrire) et les **règles
d'intervention et de rédaction** à appliquer systématiquement.

> ⚠️ Objectif de ce document : **compléter et cadrer** le travail sur l'existant,
> **pas** refondre le site. Ne modifie pas la structure, la stack ou le pipeline
> sans demande explicite. Ajoute et améliore le contenu dans le cadre décrit ici.

---

## ⭐ Règles d'or (à lire avant tout)

1. **Toujours sur `main`.** Tout se fait directement sur la branche `main`. Ne crée
   jamais de branche secondaire (voir Règle n°1).
2. **Qualité maximale du modèle.** Travaille toujours au réglage le plus performant
   (voir Règle n°2). Exception unique : la photo OpenAI est en `quality: "medium"`.
3. **Rédaction par Claude, pas par l'API.** Le texte des articles est écrit par
   **toi, Claude**, directement en session. Le pipeline OpenAI texte (`gpt-5.6-terra`)
   a servi à la migration initiale des 843 articles ; désormais **c'est Claude qui
   rédige**. **Seules les images** passent encore par OpenAI (`gpt-image-2`).
4. **Anti-cannibalisation.** Avant d'écrire sur un sujet libre, vérifie l'existant :
   chaque article doit couvrir un angle **distinct** (voir §3).
5. **Qualité avant tout.** Chaque article doit apporter la **meilleure** information
   sur son sujet, avec des éléments riches quand c'est pertinent (voir §4).
6. **Photo OpenAI obligatoire.** Jamais de publication sans un vrai visuel à la une
   généré par OpenAI, ultra-réaliste (voir §6).
7. **1 à 4 liens internes par article** vers d'autres pages du site (voir §5).

---

## Le site en bref (état actuel)

**Best Annuaire** — « Le média qui décrypte le meilleur d'internet ».

Média statique haute performance (Astro 5) qui a remplacé un ancien WordPress.
843 articles pratiques et fouillés, répartis en 12 rubriques, distribués depuis
l'edge Cloudflare Pages. Registre de référence : *Le Monde pratique*,
*60 Millions de consommateurs*, *Selectra*.

- **Préprod :** https://bestannuaire.pages.dev
- **Prod :** https://www.bestannuaire.fr

### Stack

| Élément | Choix |
|---|---|
| Framework | Astro 5 (statique, `build.format: 'file'` → `/{slug}.html`) |
| Recherche | Pagefind (index au build) |
| Styles | CSS maison (design system « Kinetic Editorial »), 0 framework |
| Polices | Fraunces + Newsreader + Space Grotesk (self-hosted) |
| Hébergement | Cloudflare Pages (projet `bestannuaire`, branche `main`) |
| Images | WebP (sharp) ; manquantes générées via `gpt-image-2` |
| Rédaction (historique) | OpenAI `gpt-5.6-terra` (Responses + Batch) — **remplacé par Claude** |

### Arborescence utile

```
src/
  content/articles/{slug}.json   # 1 article = 1 fichier JSON (la source de vérité)
  content.config.ts              # schéma Zod de la collection (à respecter)
  layouts/Base.astro             # <head> SEO, thème, View Transitions
  components/                    # Header, Footer, ArticleCard, Pager, PageHero
  pages/                         # index, [slug], articles/, rubrique/, recherche, RSS, 404
  lib/site.ts                    # config, taxonomie (12 rubriques), helpers d'URL
  lib/prose.ts                   # post-traitement du body au build (ancres h2/h3, TOC, table-scroll)
  styles/                        # tokens, global, prose (classes des dispositifs riches)
scripts/                         # pipeline historique (Python + Node) — texte OpenAI + images
data/posts.json                  # dataset source (843 posts scrapés de l'ancien site)
data/images_manifest.json        # état des images (status: generated / original / …)
public/img/heroes/               # images à la une optimisées (WebP)
public/_redirects                # redirections héritées WordPress
```

### SEO & URLs (ne pas casser)

- Les **843 slugs** historiques sont conservés **à l'identique**. Ne renomme jamais
  un slug existant.
- Cloudflare sert `/{slug}` (200) et redirige `/{slug}.html` → `/{slug}` en **308**.
  L'apex `bestannuaire.fr` redirige vers `www` en **301** (`functions/_middleware.js`).
- URL canonique d'un article : `/{slug}` (sans extension) — helper `articleUrl(slug)`
  dans `src/lib/site.ts`.
- Chaque page article expose déjà un JSON-LD `Article` + `BreadcrumbList` et une FAQ
  structurée. Renseigne donc bien `metaDescription`, `tags`, `faq`, `date`, `updated`.

### Déploiement

`npm run build` → `astro build && pagefind --site dist` → sortie `dist/`.
Le push sur `main` déclenche le déploiement Cloudflare Pages
(`.github/workflows/deploy.yml` + intégration Git native). **Donc : pousser sur
`main` = publier.** Vérifie ton contenu avant de pousser.

---

## Règles d'intervention

### Règle n°1 — TOUJOURS travailler sur `main` (très important)

Toute session — développement, rédaction, amélioration, correction, etc. — se fait
**directement sur la branche `main`** du dépôt GitHub.
**Ne crée JAMAIS de branche** et ne travaille jamais sur une branche secondaire.
Commit + push sur `main`.

### Règle n°2 — Toujours en qualité optimale

Utilise systématiquement le réglage le **plus intelligent / le plus performant** du
modèle pour chaque intervention (rédaction, analyse, décisions). Pas de mode
« rapide/économe » pour le contenu éditorial.
**Exception unique :** la génération de photo via OpenAI reste en `quality: "medium"`
(voir §6).

### Règle n°3 — Clés API / tokens (jamais en dur)

Les clés et tokens nécessaires sont fournis **dans l'environnement cloud de Claude
Code** via les variables d'environnement (`process.env` en Node, `os.environ` en
Python). Récupère-les depuis l'environnement, **ne les redemande pas** et
**ne les écris jamais en dur** dans le code, la config ou un commit.

Variables attendues dans l'environnement :

| Variable | Usage |
|---|---|
| `OPENAI_API_KEY` | Génération des photos à la une (`gpt-image-2`) |
| `OPENAI_IMAGE_MODEL` | Modèle image (défaut projet : `gpt-image-2`) |
| `OPENAI_TEXT_MODEL` | Modèle texte du pipeline historique (`gpt-5.6-terra`) — non utilisé pour la rédaction nouvelle, désormais assurée par Claude |
| `CLOUDFLARE_API_TOKEN` | Déploiement Cloudflare Pages |
| `CLOUDFLARE_ACCOUNT_ID` | Déploiement Cloudflare Pages |

> Si une clé attendue est absente de l'environnement, **signale-le** et arrête l'étape
> concernée — ne l'invente pas, ne la code pas en dur.

---

## Règles de rédaction

### 0. Règles d'or (prioritaires)

- **Rédaction par Claude, pas par l'API.** L'article est écrit par **toi, Claude**,
  au meilleur réglage, directement en session — pas par le pipeline OpenAI texte.
  **Seules les images** passent par OpenAI.
- **Anti-cannibalisation.** Sujet libre → vérifie d'abord l'existant ; chaque nouvel
  article doit porter sur un angle **différent** (§3).
- **Qualité avant tout.** Apporte la meilleure information : des détails en plus et,
  selon la pertinence, des éléments riches (tableau, comparaison, astuces, FAQ,
  citation, chiffres…). Ce sont des **exemples**, pas une checklist obligatoire (§4).
- **Photo OpenAI obligatoire.** Jamais de publication sans une vraie photo à la une
  générée par OpenAI, « photo généraliste sur le thème, ultra-réaliste », **avant**
  publication (§6).
- **Liens internes.** 1 à 4 liens internes par article vers d'autres pages du site (§5).

### 1. Le site en bref (ligne éditoriale)

Best Annuaire est un **média de service** grand public. Il ne vend rien et ne fait la
promotion d'aucune marque : il **décrypte, compare et sélectionne le meilleur du web**
pour aider le lecteur à décider et à agir. La promesse est simple : *un lecteur qui
arrive sur un article doit repartir avec sa réponse complète, sans avoir besoin d'un
autre article.*

Public : francophone, non spécialiste, qui cherche une réponse pratique et fiable
(« comment faire », « comment choisir », « combien ça coûte », « quels pièges éviter »).
Les 12 rubriques couvrent la vie quotidienne : Maison & Jardin, Juridique & Démarches,
Santé & Bien-être, Tech & Numérique, Auto & Mobilité, Mode & Beauté, Finance & Argent,
Entreprise & Pro, Loisirs & Culture, Voyage & Tourisme, Famille & Enfants, Actu & Conso
(voir `RUBRIQUES` dans `src/lib/site.ts` — un article appartient à **exactement une**
rubrique, par son slug).

### 2. Identité & ton

- **Registre :** média pratique de référence (*Le Monde pratique*,
  *60 Millions de consommateurs*, *Selectra*). Sérieux, clair, vivant, professionnel.
- **Voix :** vouvoiement, français impeccable, phrases nettes, paragraphes courts.
  Zéro remplissage, zéro paraphrase creuse, zéro jargon inutile.
- **Posture :** neutre et factuel, à **valeur d'usage**. Aucune promotion d'une marque
  ou d'un commerçant précis. On explique, on compare, on met en garde — on ne vend pas.
- **E-E-A-T :** montre l'expertise par des critères concrets, une méthode, des cas
  d'usage, des points de vigilance (juridiques, pratiques, sécurité, budget).
- **Prudence factuelle :** pas de chiffres, prix ou dates inventés. Reste sur des ordres
  de grandeur explicitement présentés comme indicatifs (« généralement »,
  « souvent autour de »). En Juridique/Finance/Santé, rappelle les limites et invite à
  vérifier auprès d'une source officielle ou d'un professionnel quand c'est pertinent.
- **Titre :** ne réécris pas le titre d'un article existant (c'est un signal SEO). Pour
  un nouvel article, titre parlant, orienté intention de recherche.

### 3. Avant d'écrire — anti-cannibalisation

Deux articles ne doivent pas se disputer le même mot-clé / la même intention.

**Procédure avant de rédiger un sujet libre :**

1. **Recense l'existant.** Cherche dans `src/content/articles/*.json` les articles
   proches (titre, `tags`, `rubrique`). Exemples utiles :
   - `ls src/content/articles/ | grep -i "<mot-clé>"`
   - `grep -il "<expression>" src/content/articles/*.json`
2. **Compare l'intention.** Si un article couvre déjà **la même question centrale**,
   ne crée pas de doublon :
   - soit tu **enrichis / mets à jour** l'article existant (et tu ajustes `updated`),
   - soit tu choisis un **angle réellement différent** (sous-sujet, cas d'usage précis,
     comparatif, public différent) et tu **lies** les deux articles entre eux (§5).
3. **En cas de doute**, préfère un sujet clairement non couvert. L'objectif est
   d'**élargir** la couverture éditoriale, pas de la dupliquer.

### 4. Qualité rédactionnelle

Chaque article doit être un **dossier complet** qui répond à l'intention de recherche
(le « comment », « combien », « pourquoi », « quels risques », « quelles alternatives »,
« quels critères de choix », « quelles erreurs éviter »).

**Cadre de structure (`bodyHtml` = fragment HTML propre) :**

- Longueur substantielle : **~1600 à 2600 mots**.
- **5 à 8 sections `<h2>`** à intitulés parlants (jamais « Introduction » / « Conclusion »
  génériques). Sous-sections `<h3>` si utile. **Pas de `<h1>`** (géré par le gabarit),
  ni le chapô, ni la FAQ dans `bodyHtml` (champs dédiés).
- Rythme : paragraphes courts, listes `<ul>`/`<ol>`, `<strong>` sur les infos clés.

**Éléments riches — à utiliser quand c'est pertinent (exemples, pas obligation).**
Vise en général **au moins 3 dispositifs, dont au moins un tableau**, si le sujet s'y
prête. Les classes CSS existent déjà (`src/styles/prose.css`) :

- **Tableau** (toujours enveloppé) :
  `<div class="table-scroll"><table><thead>…</thead><tbody>…</tbody></table></div>`
- **Encadré** : `<aside class="callout callout--key"><p class="callout__title">Titre</p><p>…</p></aside>`
  (variantes : `callout--info`, `callout--tip`, `callout--warn`)
- **Comparaison 2 colonnes** :
  `<div class="compare"><div class="compare__col compare__col--pro"><p class="compare__head">Avantages</p><ul>…</ul></div><div class="compare__col compare__col--con"><p class="compare__head">Limites</p><ul>…</ul></div></div>`
- **Étapes numérotées** : `<ol class="steps"><li>…</li></ol>`
- **Chiffres clés** :
  `<div class="stat-grid"><div class="stat"><span class="stat__num">X</span><span class="stat__label">…</span></div>…</div>`
- **Citation forte** : `<blockquote>…</blockquote>`

**Champs à remplir dans le JSON** (schéma `src/content.config.ts`) :

- `chapo` : accroche de 2–3 phrases (40–60 mots), sans redite du titre.
- `metaDescription` : 150–160 caractères, avec le mot-clé principal.
- `keyTakeaways` : 3 à 5 points essentiels (phrases courtes et concrètes).
- `tags` : 4 à 6 mots-clés en minuscules, sans `#`.
- `faq` : 4 à 6 Q/R réellement recherchées (réponses autonomes de 2–4 phrases).
- `rubrique` : **exactement un** slug de `RUBRIQUES`.

> Interdit dans `bodyHtml` : `<script>`, `<style>`, `<iframe>`, styles inline, `<h1>`.
> Les liens externes sont automatiquement passés en `rel="noopener nofollow"
> target="_blank"` — reste sur des liens **neutres** et évite tout lien commercial.

### 5. Liens internes (1 à 4 par article)

Chaque article doit contenir **1 à 4 liens internes** vers d'autres pages du site.
C'est aujourd'hui absent des articles migrés → c'est une **amélioration à instaurer**.

- **Format :** lien relatif vers le slug, `<a href="/{slug-cible}">ancre descriptive</a>`
  (URL canonique sans extension ; pas de domaine, pas de `.html`).
- **Cibles pertinentes :** un autre article de la **même rubrique** ou d'un sujet
  connexe, ou la page de rubrique `/rubrique/{slug}`.
- **Vérifie que la cible existe** (`ls src/content/articles/{slug}.json`) avant de lier ;
  jamais de lien mort.
- **Ancre naturelle et utile** (pas de « cliquez ici »), intégrée dans une phrase.
- Ces liens **complètent** le bloc « articles liés » automatique en pied de page
  (même rubrique, 3 articles récents) — ils ne le remplacent pas.

### 6. Photo — toujours une vraie photo OpenAI avant publication

**Règle absolue :** jamais de publication sans visuel. **Toujours** une vraie photo de
couverture générée par OpenAI, **ultra-réaliste**, **avant** publication.

- **Modèle & paramètres imposés** (via `OPENAI_API_KEY` de l'environnement) :
  ```json
  { "model": "gpt-image-2", "size": "1536x1024", "quality": "medium" }
  ```
- **Une seule image (hero) par article.** Pas de galerie, pas d'image dans le corps.
- **Style :** photo éditoriale généraliste sur le thème, ultra-réaliste, lumière
  naturelle, faible profondeur de champ, **sans aucun texte, sans logo, sans watermark**,
  personne ne fixe l'objectif. Le brief image (`image_prompt`) est en **anglais**.
- **Outillage existant :** `scripts/gen_images.py` applique déjà ces paramètres et
  produit `public/img/heroes/{slug}.webp` (+ `-sm.webp`), puis met à jour
  `data/images_manifest.json`.
  - Ex. : `python3 scripts/gen_images.py --slugs <slug>` (le prompt est lu depuis le
    champ `_imagePrompt` du JSON de l'article s'il existe).
- **Dans le JSON de l'article, renseigne alors :** `heroImage`, `heroImageSm`,
  `heroAlt` (descriptif, en français), `heroGenerated: true`.

---

## Ajouter / mettre à jour un article (procédure Claude)

1. **Sujet** : choisi ou libre → applique l'anti-cannibalisation (§3).
2. **Rédige** le dossier complet toi-même (§2, §4), au meilleur réglage.
3. **Crée/édite** `src/content/articles/{slug}.json` en respectant le schéma
   (`src/content.config.ts`). Conserve le slug historique s'il existe.
4. **Ajoute 1 à 4 liens internes** valides dans `bodyHtml` (§5).
5. **Renseigne** `_imagePrompt` (anglais) puis **génère la photo** via `gpt-image-2`
   (§6) et relie `heroImage` / `heroImageSm` / `heroGenerated` / `heroAlt`.
6. **Contrôle** localement si possible (`npm run build`) : le schéma Zod doit valider.
7. **Commit + push sur `main`** → déploiement automatique Cloudflare Pages.

### Rappels techniques

- Un article = **un fichier JSON** dans `src/content/articles/`. Pas de base de données.
- Le body est post-traité au build (`src/lib/prose.ts`) : ancres `id` sur les `h2`/`h3`,
  sommaire, tables enveloppées. Écris du HTML propre, il sera enrichi automatiquement.
- N'introduis pas de dépendance ni de framework CSS : le design system est maison.
- Ne touche pas aux slugs, redirections (`public/_redirects`), ni au middleware apex→www
  sans raison explicite.
