import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

// Un article = un fichier JSON produit par la pipeline OpenAI (scripts/*).
// Le slug historique WordPress est conservé à l'identique (SEO).
const articles = defineCollection({
  loader: glob({ pattern: '**/*.json', base: './src/content/articles' }),
  schema: z.object({
    title: z.string(),
    slug: z.string(),
    date: z.coerce.date(),
    updated: z.coerce.date().optional(),
    rubrique: z.string(),
    tags: z.array(z.string()).default([]),
    chapo: z.string(),
    metaDescription: z.string(),
    heroImage: z.string().nullish(),
    heroImageSm: z.string().nullish(),
    heroAlt: z.string().nullish().transform((v) => v ?? ''),
    heroGenerated: z.boolean().default(false),
    readingTime: z.number().default(4),
    keyTakeaways: z.array(z.string()).default([]),
    bodyHtml: z.string(),
    faq: z.array(z.object({ q: z.string(), a: z.string() })).default([]),
    sources: z.array(z.object({ label: z.string(), url: z.string().optional() })).default([]),
    featured: z.boolean().default(false),
  }),
});

export const collections = { articles };
