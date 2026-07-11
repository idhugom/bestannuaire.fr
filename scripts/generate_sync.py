#!/usr/bin/env python3
"""Génère un lot d'articles en synchrone via la Responses API (pour la préprod).
Sauvegarde la sortie brute dans data/openai/{slug}.json puis ingère.

Usage:
  python3 scripts/generate_sync.py --limit 20
  python3 scripts/generate_sync.py --slugs slug-a,slug-b
"""
import argparse
import json
import sys
import time
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import openai_common as oc
import ingest as ing

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "openai"
RAW.mkdir(parents=True, exist_ok=True)


def gen_one(post):
    slug = post["slug"]
    out = RAW / f"{slug}.json"
    if out.exists():
        return slug, "cached", json.loads(out.read_text())
    for attempt in range(3):
        try:
            resp = oc.openai_post("/responses", oc.build_body(post), timeout=600)
            if resp.get("status") != "completed":
                raise RuntimeError(f"status={resp.get('status')} {resp.get('incomplete_details')}")
            txt = oc.extract_output_text(resp)
            art = json.loads(txt)
            out.write_text(json.dumps(art, ensure_ascii=False, indent=2), encoding="utf-8")
            return slug, "ok", art
        except (urllib.error.HTTPError, urllib.error.URLError, RuntimeError, json.JSONDecodeError) as e:
            detail = ""
            if isinstance(e, urllib.error.HTTPError):
                try:
                    detail = e.read().decode()[:300]
                except Exception:
                    pass
            if attempt == 2:
                return slug, f"ERR {type(e).__name__} {e} {detail}", None
            time.sleep(2 ** attempt * 3)
    return slug, "ERR", None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--slugs", type=str, default="")
    ap.add_argument("--concurrency", type=int, default=6)
    ap.add_argument("--with-images-only", action="store_true", default=True)
    ap.add_argument("--all", action="store_true", help="ignore le filtre image")
    args = ap.parse_args()

    posts = json.loads((ROOT / "data" / "posts.json").read_text())
    posts_by_slug = {p["slug"]: p for p in posts}
    manifest = ing.load_manifest()

    if args.slugs:
        want = [posts_by_slug[s] for s in args.slugs.split(",") if s in posts_by_slug]
    else:
        pool = posts
        if args.with_images_only and not args.all:
            pool = [p for p in posts if p.get("featured_image")]
        want = pool[: args.limit]

    print(f"Génération synchrone de {len(want)} articles (concurrency={args.concurrency})…")
    results = {}
    with ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        futs = {ex.submit(gen_one, p): p for p in want}
        for fut in as_completed(futs):
            slug, status, art = fut.result()
            results[slug] = (status, art)
            flag = "✓" if status in ("ok", "cached") else "✗"
            print(f"  {flag} {slug[:60]:60} {status[:50]}")

    # Ingestion
    manifest = ing.load_manifest()  # relire (les images ont pu finir)
    n = 0
    for i, p in enumerate(want):
        slug = p["slug"]
        status, art = results.get(slug, ("missing", None))
        if art:
            featured = i < 5  # les 5 premiers en une
            ing.write_article(ing.build_article(p, art, manifest, featured=featured))
            n += 1
    ok = sum(1 for s, _ in results.values() if s in ("ok", "cached"))
    print(f"\nOK: {ok}/{len(want)} générés — {n} articles ingérés.")


if __name__ == "__main__":
    main()
