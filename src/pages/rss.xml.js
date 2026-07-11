import rss from '@astrojs/rss';
import { getCollection } from 'astro:content';
import { SITE, rubriqueBySlug } from '../lib/site';

export async function GET(context) {
  const articles = (await getCollection('articles')).sort((a, b) => +b.data.date - +a.data.date);
  return rss({
    title: `${SITE.name} — ${SITE.tagline}`,
    description: SITE.description,
    site: context.site ?? SITE.url,
    xmlns: { atom: 'http://www.w3.org/2005/Atom' },
    items: articles.slice(0, 60).map((a) => ({
      title: a.data.title,
      description: a.data.metaDescription || a.data.chapo,
      link: `/${a.data.slug}`,
      pubDate: new Date(a.data.date),
      categories: [rubriqueBySlug(a.data.rubrique).label, ...a.data.tags],
    })),
    customData: `<language>fr-fr</language><copyright>© ${new Date().getFullYear()} ${SITE.name}</copyright>`,
  });
}
