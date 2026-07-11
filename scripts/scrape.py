#!/usr/bin/env python3
"""Scrape all posts from the legacy WordPress bestannuaire.fr via REST API.

Extracts: id, slug (kept 100% identical), title, dates, excerpt, original
content (as source material for the rewrite), featured image URL, category.
Writes data/posts.json
"""
import json
import sys
import time
import urllib.request
import urllib.error
import html
import re
from pathlib import Path

BASE = "https://www.bestannuaire.fr/wp-json/wp/v2"
OUT = Path(__file__).resolve().parent.parent / "data" / "posts.json"
PER_PAGE = 100


def fetch(url, retries=5):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "bestannuaire-migration/1.0"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode("utf-8")), dict(r.headers)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            wait = 2 ** attempt
            print(f"  ! {e} — retry in {wait}s ({attempt+1}/{retries})", file=sys.stderr)
            time.sleep(wait)
    raise RuntimeError(f"Failed to fetch {url}")


def strip_html(s):
    s = re.sub(r"<[^>]+>", " ", s or "")
    s = html.unescape(s)
    return re.sub(r"\s+", " ", s).strip()


def clean_title(s):
    return html.unescape(strip_html(s))


def main():
    # discover total pages
    _, headers = fetch(f"{BASE}/posts?per_page=1")
    total = int(headers.get("X-WP-Total", "0"))
    total_pages = (total + PER_PAGE - 1) // PER_PAGE
    print(f"Total posts: {total} across {total_pages} pages of {PER_PAGE}")

    posts = []
    for page in range(1, total_pages + 1):
        url = (f"{BASE}/posts?per_page={PER_PAGE}&page={page}"
               "&_embed=wp:featuredmedia,wp:term"
               "&_fields=id,slug,link,date,modified,title,excerpt,content,_links,_embedded")
        data, _ = fetch(url)
        for p in data:
            fm = p.get("_embedded", {}).get("wp:featuredmedia", [])
            featured = None
            featured_alt = None
            if fm and isinstance(fm, list) and fm[0] and isinstance(fm[0], dict):
                featured = fm[0].get("source_url")
                featured_alt = fm[0].get("alt_text") or None
            terms = p.get("_embedded", {}).get("wp:term", [])
            cats = [t["name"] for grp in terms for t in grp if t.get("taxonomy") == "category"]
            slug = p["slug"]
            link = p.get("link", "")
            # canonical path exactly as WP serves it
            path = link.replace("https://www.bestannuaire.fr", "").replace("http://www.bestannuaire.fr", "")
            posts.append({
                "id": p["id"],
                "slug": slug,
                "path": path,                       # e.g. /foo.html
                "title": clean_title(p.get("title", {}).get("rendered", "")),
                "date": p.get("date"),
                "modified": p.get("modified"),
                "excerpt_text": strip_html(p.get("excerpt", {}).get("rendered", "")),
                "original_text": strip_html(p.get("content", {}).get("rendered", "")),
                "original_wordcount": len(strip_html(p.get("content", {}).get("rendered", "")).split()),
                "featured_image": featured,
                "featured_alt": featured_alt,
                "categories": cats or ["infos"],
            })
        print(f"  page {page}/{total_pages} — {len(posts)} posts so far")

    # de-dup by slug (keep first), warn on collisions
    seen = {}
    out = []
    for p in posts:
        if p["slug"] in seen:
            print(f"  ! duplicate slug {p['slug']} (ids {seen[p['slug']]} & {p['id']})", file=sys.stderr)
            continue
        seen[p["slug"]] = p["id"]
        out.append(p)

    out.sort(key=lambda x: x["date"] or "", reverse=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    with_img = sum(1 for p in out if p["featured_image"])
    print(f"\nDONE: {len(out)} unique posts written to {OUT}")
    print(f"  with featured image: {with_img}  |  without: {len(out)-with_img}")
    print(f"  avg original wordcount: {sum(p['original_wordcount'] for p in out)//max(len(out),1)}")


if __name__ == "__main__":
    main()
