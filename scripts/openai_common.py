#!/usr/bin/env python3
"""Partagé par la pipeline de contenu OpenAI (Responses API + Batch API).

Modèle et paramètres imposés :
  model=gpt-5.6-terra, reasoning.effort=high, text.verbosity=high,
  max_output_tokens=30000, API=Responses (/v1/responses), exécution en Batch.
"""
import json
import os
import re
import urllib.request
import urllib.error

OPENAI_KEY = os.environ["OPENAI_API_KEY"]
MODEL = "gpt-5.6-terra"

# Taxonomie éditoriale (doit rester synchro avec src/lib/site.ts)
RUBRIQUES = [
    ("maison-jardin", "Maison & Jardin"),
    ("juridique-demarches", "Juridique & Démarches"),
    ("sante-bien-etre", "Santé & Bien-être"),
    ("tech-numerique", "Tech & Numérique"),
    ("auto-mobilite", "Auto & Mobilité"),
    ("mode-beaute", "Mode & Beauté"),
    ("finance-argent", "Finance & Argent"),
    ("entreprise-pro", "Entreprise & Pro"),
    ("loisirs-culture", "Loisirs & Culture"),
    ("voyage-tourisme", "Voyage & Tourisme"),
    ("famille-enfants", "Famille & Enfants"),
    ("actu-conso", "Actu & Conso"),
]
RUBRIQUE_SLUGS = [r[0] for r in RUBRIQUES]
RUBRIQUE_LIST_TXT = "\n".join(f"  - {s} : {label}" for s, label in RUBRIQUES)

# ---- Schéma de sortie structurée (strict) --------------------------------
ARTICLE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "rubrique": {"type": "string", "enum": RUBRIQUE_SLUGS},
        "tags": {"type": "array", "items": {"type": "string"}},
        "meta_description": {"type": "string"},
        "chapo": {"type": "string"},
        "key_takeaways": {"type": "array", "items": {"type": "string"}},
        "body_html": {"type": "string"},
        "faq": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {"q": {"type": "string"}, "a": {"type": "string"}},
                "required": ["q", "a"],
            },
        },
        "image_prompt": {"type": "string"},
    },
    "required": [
        "rubrique", "tags", "meta_description", "chapo",
        "key_takeaways", "body_html", "faq", "image_prompt",
    ],
}

SYSTEM_PROMPT = """Tu es rédacteur·rice en chef d'un grand média web français de référence (registre : Le Monde pratique, 60 Millions de consommateurs, Selectra). Ta mission : écrire un dossier éditorial ORIGINAL, expert et réellement utile sur le sujet fourni.

RÈGLES DE FOND
- Réécris ENTIÈREMENT. Le texte source n'est qu'un indice de sujet : ne le recopie jamais, ne reprends ni ses tournures, ni ses mentions commerciales, ni ses liens.
- Vise l'intention de recherche complète : le lecteur doit repartir sans avoir besoin d'un autre article. Réponds aux questions implicites (comment, combien, pourquoi, quels risques, quelles alternatives, quels critères de choix, quelles erreurs à éviter).
- Contenu neutre, factuel, à valeur d'usage. Aucune promotion d'une marque ou d'un commerçant précis. Pas de chiffres/prix/dates inventés : reste sur des ordres de grandeur prudents et explicitement présentés comme indicatifs (« généralement », « souvent autour de »).
- Français impeccable, vouvoiement, ton clair, vivant et professionnel. Zéro remplissage, zéro paraphrase creuse.
- E-E-A-T : montre l'expertise (critères concrets, méthode, cas d'usage, points de vigilance juridiques/pratiques).

STRUCTURE & RICHESSE (impératif)
- Longueur substantielle : ~1600 à 2600 mots dans body_html.
- Découpe en 5 à 8 sections <h2> à intitulés parlants (pas « Introduction »/« Conclusion » génériques). Sous-sections <h3> si utile.
- Rythme : paragraphes courts, listes <ul>/<ol>, gras <strong> sur les infos clés.
- Utilise OBLIGATOIREMENT, quand c'est pertinent (au moins 3 de ces dispositifs, dont au moins un tableau) :
  * Tableau comparatif/synthétique, TOUJOURS enveloppé : <div class="table-scroll"><table><thead>…</thead><tbody>…</tbody></table></div>
  * Encadré de mise en avant : <aside class="callout callout--key"><p class="callout__title">Titre</p><p>…</p></aside> (variantes : callout--info, callout--tip, callout--warn)
  * Comparaison 2 colonnes : <div class="compare"><div class="compare__col compare__col--pro"><p class="compare__head">Avantages</p><ul>…</ul></div><div class="compare__col compare__col--con"><p class="compare__head">Limites</p><ul>…</ul></div></div>
  * Étapes numérotées : <ol class="steps"><li>…</li></ol>
  * Chiffres clés : <div class="stat-grid"><div class="stat"><span class="stat__num">X</span><span class="stat__label">…</span></div>…</div>
  * Citation forte : <blockquote>…</blockquote>
- N'inclus PAS de <h1> (le titre est géré par le gabarit), NI le chapô, NI la FAQ dans body_html.
- body_html = fragment HTML propre (pas de <html>/<body>, pas de style inline, pas de scripts).

CHAMPS DE SORTIE
- rubrique : choisis LA rubrique la plus adaptée dans cette liste (renvoie le slug) :
%s
- tags : 4 à 6 mots-clés thématiques (minuscules, sans #).
- meta_description : 150–160 caractères, accrocheuse, avec le mot-clé principal.
- chapo : chapô d'accroche de 2–3 phrases (40–60 mots), sans redite du titre.
- key_takeaways : 3 à 5 points essentiels (phrases courtes et concrètes).
- faq : 4 à 6 questions/réponses réellement recherchées (réponses de 2–4 phrases, autonomes).
- image_prompt : brief en ANGLAIS pour une photo éditoriale ultra-réaliste illustrant le sujet (scène concrète, lumière naturelle, sans aucun texte, sans logo, sans watermark, style photojournalisme éditorial).
""" % RUBRIQUE_LIST_TXT


def user_prompt(post: dict) -> str:
    src = post.get("original_text", "")[:2600]
    return (
        f"TITRE (à conserver tel quel, ne pas le réécrire) : {post['title']}\n"
        f"Slug (contexte SEO, ne pas modifier) : {post['slug']}\n"
        f"Indice de sujet issu de l'ancienne version (NE PAS RECOPIER — sert uniquement à cerner le thème) :\n"
        f"\"\"\"\n{src}\n\"\"\"\n\n"
        "Rédige maintenant le dossier complet, structuré et riche, en respectant scrupuleusement le schéma de sortie."
    )


def build_body(post: dict) -> dict:
    """Corps de requête Responses API pour un post."""
    return {
        "model": MODEL,
        "input": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt(post)},
        ],
        "reasoning": {"effort": "high"},
        "text": {
            "verbosity": "high",
            "format": {
                "type": "json_schema",
                "name": "article_bestannuaire",
                "strict": True,
                "schema": ARTICLE_SCHEMA,
            },
        },
        "max_output_tokens": 30000,
    }


def openai_post(path: str, payload: dict, timeout=600):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"https://api.openai.com/v1{path}",
        data=data,
        headers={
            "Authorization": f"Bearer {OPENAI_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def extract_output_text(resp: dict) -> str:
    """Récupère le texte de sortie d'une réponse Responses API."""
    if "output_text" in resp and resp["output_text"]:
        return resp["output_text"]
    chunks = []
    for item in resp.get("output", []):
        if item.get("type") == "message":
            for c in item.get("content", []):
                if c.get("type") in ("output_text", "text") and c.get("text"):
                    chunks.append(c["text"])
    return "".join(chunks)


def slugify_fname(slug: str) -> str:
    return re.sub(r"[^a-z0-9-]", "-", slug.lower())
