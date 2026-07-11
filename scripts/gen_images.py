#!/usr/bin/env python3
"""Génère une image éditoriale ultra-réaliste via l'API Images d'OpenAI pour les
articles sans image à la une exploitable (404 d'origine ou absente).

Paramètres imposés : model=gpt-image-2, size=1536x1024, quality=medium.
Sortie : public/img/heroes/{slug}.webp (+ -sm) et manifest status='generated'.

Usage:
  python3 scripts/gen_images.py --slugs slug-a,slug-b
  python3 scripts/gen_images.py --missing --limit 30      # tous ceux sans image
  python3 scripts/gen_images.py --test                    # 1 image de contrôle
"""
import argparse
import base64
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HEROES = ROOT / "public" / "img" / "heroes"
MANIFEST = ROOT / "data" / "images_manifest.json"
ART_DIR = ROOT / "src" / "content" / "articles"
OPENAI_KEY = os.environ["OPENAI_API_KEY"]
HEROES.mkdir(parents=True, exist_ok=True)

STYLE = (
    " Ultra-realistic editorial photograph, natural light, shallow depth of field, "
    "photojournalism, high detail, no text, no words, no logo, no watermark, no people staring at camera."
)


def load_manifest():
    if MANIFEST.exists():
        try:
            return json.loads(MANIFEST.read_text())
        except Exception:
            return {}
    return {}


def save_manifest(m):
    MANIFEST.write_text(json.dumps(m, indent=2))


def gen_image_b64(prompt: str) -> bytes:
    payload = json.dumps({
        "model": "gpt-image-2",
        "prompt": prompt[:3800] + STYLE,
        "size": "1536x1024",
        "quality": "medium",
        "n": 1,
    }).encode()
    req = urllib.request.Request(
        "https://api.openai.com/v1/images/generations",
        data=payload,
        headers={"Authorization": f"Bearer {OPENAI_KEY}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=300) as r:
        data = json.loads(r.read().decode())
    d0 = data["data"][0]
    if d0.get("b64_json"):
        return base64.b64decode(d0["b64_json"])
    if d0.get("url"):
        with urllib.request.urlopen(d0["url"], timeout=120) as r2:
            return r2.read()
    raise RuntimeError("no image payload")


def to_webp(raw: bytes, slug: str):
    """Redimensionne via un petit script node/sharp (PIL absent)."""
    tmp = HEROES / f"_{slug}.src"
    tmp.write_bytes(raw)
    node = f"""
    const sharp=require('sharp');
    (async()=>{{
      const b=require('fs').readFileSync({json.dumps(str(tmp))});
      const s=sharp(b).rotate();
      await s.clone().resize(1280,800,{{fit:'cover'}}).webp({{quality:80}}).toFile({json.dumps(str(HEROES / (slug + '.webp')))});
      await s.clone().resize(640,427,{{fit:'cover'}}).webp({{quality:76}}).toFile({json.dumps(str(HEROES / (slug + '-sm.webp')))});
    }})();
    """
    subprocess.run(["node", "-e", node], check=True, cwd=str(ROOT))
    tmp.unlink(missing_ok=True)


def prompt_for(slug: str, posts: dict) -> str:
    art_file = ART_DIR / f"{slug}.json"
    if art_file.exists():
        try:
            art = json.loads(art_file.read_text())
            if art.get("_imagePrompt"):
                return art["_imagePrompt"]
        except Exception:
            pass
    p = posts.get(slug, {})
    return f"Editorial illustration for an article titled '{p.get('title', slug)}'."


def process(slug, posts, manifest):
    try:
        raw = gen_image_b64(prompt_for(slug, posts))
        to_webp(raw, slug)
        manifest[slug] = {"status": "generated",
                          "hero": f"/img/heroes/{slug}.webp",
                          "sm": f"/img/heroes/{slug}-sm.webp",
                          "alt": posts.get(slug, {}).get("title", "")}
        return slug, "ok"
    except urllib.error.HTTPError as e:
        return slug, f"HTTP {e.code} {e.read().decode()[:200]}"
    except Exception as e:
        return slug, f"ERR {type(e).__name__} {e}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slugs", default="")
    ap.add_argument("--missing", action="store_true")
    ap.add_argument("--limit", type=int, default=9999)
    ap.add_argument("--concurrency", type=int, default=4)
    ap.add_argument("--test", action="store_true")
    args = ap.parse_args()

    posts = {p["slug"]: p for p in json.loads((ROOT / "data" / "posts.json").read_text())}
    manifest = load_manifest()

    if args.test:
        raw = gen_image_b64("A cozy Scandinavian living room with a modern radiant heating panel on the wall, warm winter light.")
        (ROOT / "data" / "_imgtest.png").write_bytes(raw)
        print(f"OK test image: {len(raw)} bytes -> data/_imgtest.png")
        return

    if args.slugs:
        slugs = [s for s in args.slugs.split(",") if s]
    elif args.missing:
        slugs = [s for s, v in manifest.items() if v.get("status") in ("failed", "none")]
    else:
        print("Rien à faire (utilisez --slugs / --missing / --test)")
        return
    slugs = slugs[: args.limit]

    print(f"Génération de {len(slugs)} images gpt-image-2 (concurrency={args.concurrency})…")
    ok = 0
    with ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        futs = {ex.submit(process, s, posts, manifest): s for s in slugs}
        for i, fut in enumerate(as_completed(futs), 1):
            slug, status = fut.result()
            if status == "ok":
                ok += 1
            print(f"  [{i}/{len(slugs)}] {'✓' if status=='ok' else '✗'} {slug[:50]:50} {status[:60]}")
            if i % 10 == 0:
                save_manifest(manifest)
    save_manifest(manifest)
    print(f"\nOK images générées: {ok}/{len(slugs)}")


if __name__ == "__main__":
    main()
