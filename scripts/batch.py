#!/usr/bin/env python3
"""Pipeline Batch API OpenAI pour régénérer TOUS les articles restants.

Sous-commandes :
  build    -> data/batch_input.jsonl  (posts non encore générés)
  submit   -> upload + création du batch, id dans data/batch_state.json
  status   -> état d'avancement du batch
  ingest   -> télécharge la sortie et écrit les articles + relance ingest global

Modèle/params imposés : gpt-5.6-terra, reasoning=high, verbosity=high,
max_output_tokens=30000, endpoint=/v1/responses.
"""
import json
import subprocess
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import openai_common as oc
import ingest as ing

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
INPUT = DATA / "batch_input.jsonl"
STATE = DATA / "batch_state.json"
OUTPUT = DATA / "batch_output.jsonl"
KEY = os.environ["OPENAI_API_KEY"]


def curl_json(args):
    r = subprocess.run(args, capture_output=True, text=True)
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        print("Réponse non-JSON:", r.stdout[:500], r.stderr[:300])
        raise


def cmd_build():
    posts = json.loads((DATA / "posts.json").read_text())
    done = {p.stem for p in (ROOT / "src" / "content" / "articles").glob("*.json")}
    todo = [p for p in posts if p["slug"] not in done]
    with INPUT.open("w", encoding="utf-8") as f:
        for p in todo:
            f.write(json.dumps({
                "custom_id": p["slug"],
                "method": "POST",
                "url": "/v1/responses",
                "body": oc.build_body(p),
            }, ensure_ascii=False) + "\n")
    print(f"build: {len(todo)} requêtes -> {INPUT}  (déjà générés: {len(done)})")


def cmd_submit():
    up = curl_json([
        "curl", "-sS", "https://api.openai.com/v1/files",
        "-H", f"Authorization: Bearer {KEY}",
        "-F", "purpose=batch",
        "-F", f"file=@{INPUT}",
    ])
    file_id = up.get("id")
    if not file_id:
        print("Échec upload:", json.dumps(up)[:600]); return
    print("file:", file_id)
    b = curl_json([
        "curl", "-sS", "https://api.openai.com/v1/batches",
        "-H", f"Authorization: Bearer {KEY}",
        "-H", "Content-Type: application/json",
        "-d", json.dumps({
            "input_file_id": file_id,
            "endpoint": "/v1/responses",
            "completion_window": "24h",
            "metadata": {"project": "bestannuaire-rebuild"},
        }),
    ])
    if not b.get("id"):
        print("Échec création batch:", json.dumps(b)[:600]); return
    STATE.write_text(json.dumps({"batch_id": b["id"], "input_file": file_id}, indent=2))
    print(f"batch créé: {b['id']}  status={b.get('status')}")


def cmd_status():
    st = json.loads(STATE.read_text())
    b = curl_json(["curl", "-sS", f"https://api.openai.com/v1/batches/{st['batch_id']}",
                   "-H", f"Authorization: Bearer {KEY}"])
    print(f"status: {b.get('status')}")
    print("counts:", json.dumps(b.get("request_counts", {})))
    for k in ("output_file_id", "error_file_id", "created_at", "completed_at"):
        if b.get(k):
            print(f"  {k}: {b[k]}")
    STATE.write_text(json.dumps({**st, **{k: b.get(k) for k in ("status", "output_file_id", "error_file_id")}}, indent=2))
    return b


def cmd_ingest():
    st = json.loads(STATE.read_text())
    b = cmd_status()
    out_id = b.get("output_file_id")
    if not out_id:
        print("Pas de fichier de sortie (batch pas terminé ?)."); return
    subprocess.run(["curl", "-sS", f"https://api.openai.com/v1/files/{out_id}/content",
                    "-H", f"Authorization: Bearer {KEY}", "-o", str(OUTPUT)], check=True)
    posts = {p["slug"]: p for p in json.loads((DATA / "posts.json").read_text())}
    (DATA / "openai").mkdir(exist_ok=True)
    n = 0
    for line in OUTPUT.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        slug = rec.get("custom_id")
        resp = (rec.get("response") or {}).get("body") or {}
        if slug not in posts or resp.get("status") != "completed":
            continue
        try:
            txt = oc.extract_output_text(resp)
            art = json.loads(txt)
        except Exception:
            continue
        (DATA / "openai" / f"{slug}.json").write_text(json.dumps(art, ensure_ascii=False, indent=2), encoding="utf-8")
        n += 1
    print(f"ingest batch: {n} sorties écrites dans data/openai/. Lancez: python3 scripts/ingest.py")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    {"build": cmd_build, "submit": cmd_submit, "status": cmd_status, "ingest": cmd_ingest}.get(cmd, cmd_status)()
