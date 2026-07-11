#!/usr/bin/env python3
"""Transforme une sortie OpenAI + les métadonnées d'un post en fichier de la
collection de contenu Astro : src/content/articles/{slug}.json
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ART_DIR = ROOT / "src" / "content" / "articles"
MANIFEST = ROOT / "data" / "images_manifest.json"

_SCRIPTISH = re.compile(r"<(script|style|iframe|object|embed|form|link|meta|noscript)\b[^>]*>.*?</\1>",
                        re.IGNORECASE | re.DOTALL)
_SELFCLOSE = re.compile(r"<(link|meta)\b[^>]*/?>", re.IGNORECASE)
_ON_ATTR = re.compile(r"\son\w+\s*=\s*(\"[^\"]*\"|'[^']*'|[^\s>]+)", re.IGNORECASE)
_JS_URL = re.compile(r"(href|src)\s*=\s*(\"|')\s*javascript:[^\"']*(\"|')", re.IGNORECASE)
_H1 = re.compile(r"</?h1\b[^>]*>", re.IGNORECASE)
_A_EXT = re.compile(r"<a\s+([^>]*?)href=(\"|')(https?://[^\"']+)(\"|')([^>]*)>", re.IGNORECASE)
_CODEFENCE = re.compile(r"^```[a-z]*\s*|\s*```$", re.IGNORECASE)


def sanitize_html(html: str) -> str:
    if not html:
        return ""
    html = _CODEFENCE.sub("", html.strip())
    html = _SCRIPTISH.sub("", html)
    html = _SELFCLOSE.sub("", html)
    html = _ON_ATTR.sub("", html)
    html = _JS_URL.sub(r'\1=\2#\3', html)
    html = _H1.sub("", html)  # h1 réservé au gabarit

    def _ext(m):
        return f'<a {m.group(1)}href={m.group(2)}{m.group(3)}{m.group(4)} rel="noopener nofollow" target="_blank"{m.group(5)}>'
    html = _A_EXT.sub(_ext, html)
    return html.strip()


def reading_time(text_html: str) -> int:
    words = len(re.sub(r"<[^>]+>", " ", text_html).split())
    return max(2, round(words / 200))


def load_manifest() -> dict:
    if MANIFEST.exists():
        try:
            return json.loads(MANIFEST.read_text())
        except Exception:
            return {}
    return {}


def build_article(post: dict, gen: dict, manifest: dict, featured: bool = False) -> dict:
    slug = post["slug"]
    body = sanitize_html(gen.get("body_html", ""))
    img = manifest.get(slug, {})
    hero = img.get("hero")
    hero_sm = img.get("sm")
    hero_generated = img.get("status") == "generated"

    faq = [
        {"q": (f.get("q") or "").strip(), "a": (f.get("a") or "").strip()}
        for f in gen.get("faq", []) if f.get("q") and f.get("a")
    ]
    tags = [t.strip().lower() for t in gen.get("tags", []) if t and t.strip()][:6]

    return {
        "title": post["title"],
        "slug": slug,
        "date": post["date"],
        "updated": post.get("modified") or post["date"],
        "rubrique": gen.get("rubrique", "actu-conso"),
        "tags": tags,
        "chapo": (gen.get("chapo") or "").strip(),
        "metaDescription": (gen.get("meta_description") or "").strip()[:165],
        "heroImage": hero,
        "heroImageSm": hero_sm,
        "heroAlt": img.get("alt") or post.get("featured_alt") or post["title"],
        "heroGenerated": hero_generated,
        "readingTime": reading_time(body),
        "keyTakeaways": [k.strip() for k in gen.get("key_takeaways", []) if k and k.strip()][:5],
        "bodyHtml": body,
        "faq": faq,
        "sources": [],
        "featured": featured,
        "_imagePrompt": gen.get("image_prompt", ""),  # conservé pour la génération d'image
    }


def write_article(art: dict):
    ART_DIR.mkdir(parents=True, exist_ok=True)
    (ART_DIR / f"{art['slug']}.json").write_text(
        json.dumps(art, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    # Ingestion depuis data/openai/*.json (sorties synchrones) — usage direct.
    posts = {p["slug"]: p for p in json.loads((ROOT / "data" / "posts.json").read_text())}
    manifest = load_manifest()
    gen_dir = ROOT / "data" / "openai"
    built = []
    for f in sorted(gen_dir.glob("*.json")):
        slug = f.stem
        if slug not in posts:
            continue
        gen = json.loads(f.read_text())
        built.append(build_article(posts[slug], gen, manifest))

    # « À la une » : les plus récents disposant d'une image exploitable.
    built.sort(key=lambda a: a["date"], reverse=True)
    featured_set = 0
    for a in built:
        if a.get("heroImage") and featured_set < 6:
            a["featured"] = True
            featured_set += 1
    for a in built:
        write_article(a)

    with_img = sum(1 for a in built if a.get("heroImage"))
    print(f"Ingested {len(built)} articles ({with_img} avec image, {featured_set} à la une) -> {ART_DIR}")
