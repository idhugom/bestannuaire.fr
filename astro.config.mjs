// @ts-check
import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

// Best Annuaire — moteur média statique haute performance.
// build.format: 'file' => chaque route est émise en /{slug}.html,
// ce qui reproduit à l'identique les permaliens WordPress historiques.
export default defineConfig({
  site: 'https://www.bestannuaire.fr',
  trailingSlash: 'ignore',
  build: {
    format: 'file',
    inlineStylesheets: 'auto',
  },
  prefetch: {
    prefetchAll: true,
    defaultStrategy: 'viewport',
  },
  image: {
    // Les images sont pré-optimisées hors-build (scripts/images.py) et servies
    // depuis /public/img : on évite de faire tourner sharp sur 843 fichiers.
    responsiveStyles: true,
  },
  integrations: [
    sitemap({
      changefreq: 'weekly',
      priority: 0.7,
    }),
  ],
  devToolbar: { enabled: false },
});
