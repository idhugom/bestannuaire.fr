// Récupère l'image à la une existante de chaque post, la redimensionne en 2
// tailles WebP (hero 1280w, card 640w) dans public/img/heroes/{slug}.webp.
// Streaming (curl -> buffer -> sharp) : on ne conserve que les WebP finaux.
// Écrit data/images_manifest.json (slug -> statut/chemins) pour l'ingestion.
import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'node:fs';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import sharp from 'sharp';

const execFileP = promisify(execFile);
const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const OUT = join(ROOT, 'public', 'img', 'heroes');
const MANIFEST = join(ROOT, 'data', 'images_manifest.json');
mkdirSync(OUT, { recursive: true });

const posts = JSON.parse(readFileSync(join(ROOT, 'data', 'posts.json'), 'utf8'));
const args = process.argv.slice(2);
const onlyArg = args.find((a) => a.startsWith('--only='));
const only = onlyArg ? new Set(onlyArg.slice(7).split(',')) : null;
const force = args.includes('--force');

let manifest = {};
if (existsSync(MANIFEST)) { try { manifest = JSON.parse(readFileSync(MANIFEST, 'utf8')); } catch {} }

const CONCURRENCY = 10;
let done = 0, ok = 0, failed = 0, skipped = 0;

async function curlBuffer(url) {
  const { stdout } = await execFileP('curl', ['-sSL', '--max-time', '60', url], {
    encoding: 'buffer', maxBuffer: 40 * 1024 * 1024,
  });
  return stdout;
}

async function processOne(post) {
  const slug = post.slug;
  const heroRel = `/img/heroes/${slug}.webp`;
  const smRel = `/img/heroes/${slug}-sm.webp`;
  const heroAbs = join(OUT, `${slug}.webp`);
  const smAbs = join(OUT, `${slug}-sm.webp`);

  if (!post.featured_image) {
    manifest[slug] = { status: 'none' };
    return;
  }
  if (!force && existsSync(heroAbs) && existsSync(smAbs)) {
    manifest[slug] = { status: manifest[slug]?.status === 'generated' ? 'generated' : 'downloaded', hero: heroRel, sm: smRel, alt: post.featured_alt || '' };
    skipped++; return;
  }
  try {
    const buf = await curlBuffer(post.featured_image);
    if (!buf || buf.length < 512) throw new Error('empty/small');
    const base = sharp(buf, { failOn: 'none' }).rotate();
    await base.clone().resize(1280, 800, { fit: 'cover', position: 'attention' })
      .webp({ quality: 78 }).toFile(heroAbs);
    await base.clone().resize(640, 427, { fit: 'cover', position: 'attention' })
      .webp({ quality: 74 }).toFile(smAbs);
    manifest[slug] = { status: 'downloaded', hero: heroRel, sm: smRel, alt: post.featured_alt || '' };
    ok++;
  } catch (e) {
    manifest[slug] = { status: 'failed', reason: String(e).slice(0, 120) };
    failed++;
  }
}

let queue = posts.filter((p) => !only || only.has(p.slug));
async function run() {
  const workers = Array.from({ length: CONCURRENCY }, async () => {
    while (queue.length) {
      const post = queue.shift();
      await processOne(post);
      done++;
      if (done % 25 === 0) {
        process.stdout.write(`  ${done} traités (ok:${ok} skip:${skipped} fail:${failed})\n`);
        writeFileSync(MANIFEST, JSON.stringify(manifest, null, 2));
      }
    }
  });
  await Promise.all(workers);
  writeFileSync(MANIFEST, JSON.stringify(manifest, null, 2));
  const none = Object.values(manifest).filter((m) => m.status === 'none').length;
  const failedC = Object.values(manifest).filter((m) => m.status === 'failed').length;
  console.log(`\nDONE images: ok:${ok} skip:${skipped} fail:${failed} | sans image:${none} echec:${failedC} total manifest:${Object.keys(manifest).length}`);
}
run();
