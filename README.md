# Best Annuaire — moteur média

Média statique haute performance (Astro 5) qui remplace l'ancien WordPress.
Contenu réécrit et enrichi via l'API OpenAI, images optimisées / générées,
distribué depuis l'edge Cloudflare Pages.

- **Préprod :** https://bestannuaire.pages.dev
- **Prod (à venir) :** https://www.bestannuaire.fr (après bascule DNS)

## Stack

| Élément | Choix |
|---|---|
| Framework | Astro 5 (statique, `build.format: 'file'`) |
| Recherche | Pagefind (index au build) |
| Styles | CSS maison (design system « Kinetic Editorial »), 0 framework |
| Polices | Fraunces + Newsreader + Space Grotesk (self-hosted) |
| Hébergement | Cloudflare Pages (projet `bestannuaire`, branche `main`) |
| Contenu | OpenAI `gpt-5.6-terra` (Responses + Batch API) |
| Images | WebP (sharp) ; manquantes générées via `gpt-image-2` |

## URLs & SEO

Les **843 slugs** de l'ancien site sont conservés à l'identique. Cloudflare Pages
sert les URLs propres `/{slug}` (200) et **redirige `/{slug}.html` → `/{slug}` en 308**,
donc aucun ancien permalien WordPress ne renvoie 404. Voir `public/_redirects` pour
les redirections héritées (catégories, flux).

## Structure

```
src/
  content/articles/*.json   # 1 article = 1 fichier (produit par la pipeline)
  content.config.ts         # schéma de la collection
  layouts/Base.astro        # <head> SEO, thème, View Transitions
  components/                # Header, Footer, ArticleCard, Pager, PageHero
  pages/                     # index, [slug], articles/, rubrique/, recherche, RSS, 404…
  lib/site.ts               # config, taxonomie (12 rubriques), helpers
  styles/                   # tokens, global, prose (contenu riche)
scripts/                    # pipeline de contenu (Python + Node)
data/posts.json             # dataset source (843 posts scrapés)
public/img/heroes/          # images à la une optimisées (WebP)
```

## Pipeline de contenu

```bash
# 1. Scraper l'ancien WordPress (déjà fait -> data/posts.json)
python3 scripts/scrape.py

# 2. Images à la une existantes -> WebP (déjà fait)
node scripts/optimize_images.mjs

# 3a. Génération synchrone d'un lot (préprod)
python3 scripts/generate_sync.py --limit 20

# 3b. Génération de masse via Batch API (tous les restants)
python3 scripts/batch.py build      # -> data/batch_input.jsonl
python3 scripts/batch.py submit     # upload + création du batch
python3 scripts/batch.py status     # suivi
python3 scripts/batch.py ingest     # récupère les sorties -> data/openai/
python3 scripts/ingest.py           # écrit src/content/articles/*.json

# 4. Images manquantes (404 d'origine) -> gpt-image-2 ultra-réaliste
python3 scripts/gen_images.py --missing
python3 scripts/ingest.py           # relie les nouvelles images

# 5. Build + déploiement
npm run build
npx wrangler pages deploy dist --project-name=bestannuaire --branch=main
```

Paramètres OpenAI imposés (dans `scripts/openai_common.py`) : `gpt-5.6-terra`,
`reasoning.effort=high`, `text.verbosity=high`, `max_output_tokens=30000`,
API Responses, exécution en Batch.

## Déploiement

`npm run build` → `astro build && pagefind --site dist` → sortie dans `dist/`.

### Option A — Intégration Git native Cloudflare (recommandée)
Dans le dashboard Cloudflare → Workers & Pages → `bestannuaire` → *Settings → Builds &
deployments → Connect to Git* (autorisation unique de l'app GitHub). Réglages :
branche `main`, commande `npm run build`, sortie `dist`, racine vide,
*Build comments* activés.

### Option B — GitHub Actions (déjà en place)
`.github/workflows/deploy.yml` déploie à chaque push sur `main`. Ajouter dans
GitHub → Settings → Secrets → Actions :
- `CLOUDFLARE_API_TOKEN`
- `CLOUDFLARE_ACCOUNT_ID`

## Bascule du domaine (après validation de la préprod)

1. Cloudflare → `bestannuaire` → *Custom domains* : ajouter `www.bestannuaire.fr`
   (et `bestannuaire.fr`).
2. Activer la zone `bestannuaire.fr` : pointer les **nameservers** du registrar vers
   Cloudflare.
3. Redirection **apex → www** : DNS `bestannuaire.fr` proxifié + *Redirect Rule*
   `bestannuaire.fr/* → https://www.bestannuaire.fr/$1` (301).
4. Mettre à jour `site.url` si besoin (déjà `https://www.bestannuaire.fr`).
