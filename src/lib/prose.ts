// Post-traitement du HTML d'article au build :
//  - ajoute un id d'ancre sur chaque <h2> (et <h3>) pour le sommaire
//  - extrait la table des matières (h2)
//  - enveloppe tout <table> nu dans .table-scroll (sécurité responsive)

export type TocItem = { id: string; text: string };

function slugify(s: string): string {
  return s
    .normalize('NFD').replace(/[̀-ͯ]/g, '')
    .toLowerCase()
    .replace(/<[^>]+>/g, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 60) || 'section';
}

function stripTags(s: string): string {
  return s.replace(/<[^>]+>/g, '').replace(/&[a-z]+;/gi, ' ').trim();
}

export function enrichBody(html: string): { html: string; toc: TocItem[] } {
  const toc: TocItem[] = [];
  const used = new Set<string>();

  let out = html.replace(/<h2\b([^>]*)>([\s\S]*?)<\/h2>/gi, (_m, attrs, inner) => {
    const text = stripTags(inner);
    let id = slugify(text);
    let n = 2;
    while (used.has(id)) id = `${slugify(text)}-${n++}`;
    used.add(id);
    toc.push({ id, text });
    const cleaned = String(attrs).replace(/\sid=("|')[^"']*\1/i, '');
    return `<h2${cleaned} id="${id}">${inner}</h2>`;
  });

  out = out.replace(/<h3\b([^>]*)>([\s\S]*?)<\/h3>/gi, (_m, attrs, inner) => {
    const text = stripTags(inner);
    let id = slugify(text);
    let n = 2;
    while (used.has(id)) id = `${slugify(text)}-${n++}`;
    used.add(id);
    const cleaned = String(attrs).replace(/\sid=("|')[^"']*\1/i, '');
    return `<h3${cleaned} id="${id}">${inner}</h3>`;
  });

  // Enveloppe les tables non déjà encapsulées
  out = out.replace(/(<table\b[\s\S]*?<\/table>)/gi, (m, tbl, offset, full) => {
    const before = full.slice(Math.max(0, offset - 40), offset);
    if (/table-scroll/.test(before)) return m;
    return `<div class="table-scroll">${tbl}</div>`;
  });

  return { html: out, toc };
}
