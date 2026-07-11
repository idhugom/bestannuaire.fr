// Configuration centrale du site.
export const SITE = {
  name: 'Best Annuaire',
  tagline: "Le média qui décrypte le meilleur d'internet",
  description:
    "Best Annuaire décrypte, compare et sélectionne le meilleur du web : guides pratiques, comparatifs et analyses fouillées sur la maison, le droit, la tech, la santé, la finance et plus encore.",
  url: 'https://www.bestannuaire.fr',
  locale: 'fr_FR',
  lang: 'fr',
  author: 'La rédaction Best Annuaire',
  email: 'contact@bestannuaire.fr',
  founded: 2022,
};

// Taxonomie éditoriale : remplace l'unique catégorie WordPress « infos ».
// L'IA classe chaque article dans EXACTEMENT une de ces rubriques (par slug).
export type Rubrique = {
  slug: string;
  label: string;
  short: string;
  desc: string;
  hue: string; // couleur d'accent de la rubrique
  icon: string; // glyphe
};

export const RUBRIQUES: Rubrique[] = [
  { slug: 'maison-jardin', label: 'Maison & Jardin', short: 'Maison', desc: "Aménagement, déco, bricolage, jardin et équipement du foyer.", hue: '#FE9E00', icon: '⌂' },
  { slug: 'juridique-demarches', label: 'Juridique & Démarches', short: 'Juridique', desc: "Droit, contrats, administratif : vos démarches expliquées simplement.", hue: '#FE9E00', icon: '§' },
  { slug: 'sante-bien-etre', label: 'Santé & Bien-être', short: 'Santé', desc: "Prévention, soins, forme et qualité de vie au quotidien.", hue: '#FE9E00', icon: '✚' },
  { slug: 'tech-numerique', label: 'Tech & Numérique', short: 'Tech', desc: "Logiciels, matériel, web et outils numériques décryptés.", hue: '#FE9E00', icon: '⌘' },
  { slug: 'auto-mobilite', label: 'Auto & Mobilité', short: 'Auto', desc: "Automobile, deux-roues, entretien et nouvelles mobilités.", hue: '#FE9E00', icon: '⛛' },
  { slug: 'mode-beaute', label: 'Mode & Beauté', short: 'Mode', desc: "Style, vêtements, accessoires, cosmétique et tendances.", hue: '#FE9E00', icon: '❖' },
  { slug: 'finance-argent', label: 'Finance & Argent', short: 'Finance', desc: "Budget, épargne, crédit, assurance et bons plans financiers.", hue: '#FE9E00', icon: '€' },
  { slug: 'entreprise-pro', label: 'Entreprise & Pro', short: 'Pro', desc: "Création d'entreprise, gestion, marketing et vie professionnelle.", hue: '#FE9E00', icon: '▲' },
  { slug: 'loisirs-culture', label: 'Loisirs & Culture', short: 'Loisirs', desc: "Sorties, culture, jeux, sport et temps libre.", hue: '#FE9E00', icon: '♦' },
  { slug: 'voyage-tourisme', label: 'Voyage & Tourisme', short: 'Voyage', desc: "Destinations, hébergement, transport et conseils de voyage.", hue: '#FE9E00', icon: '✈' },
  { slug: 'famille-enfants', label: 'Famille & Enfants', short: 'Famille', desc: "Parentalité, éducation, enfance et vie de famille.", hue: '#FE9E00', icon: '☺' },
  { slug: 'actu-conso', label: 'Actu & Conso', short: 'Conso', desc: "Consommation, services, tendances et actualité pratique.", hue: '#FE9E00', icon: '◈' },
];

export const RUBRIQUE_SLUGS = RUBRIQUES.map((r) => r.slug);
export const rubriqueBySlug = (slug: string): Rubrique =>
  RUBRIQUES.find((r) => r.slug === slug) ?? RUBRIQUES[RUBRIQUES.length - 1];

export const NAV = [
  { label: 'Toutes les rubriques', href: '/rubriques' },
  ...RUBRIQUES.slice(0, 6).map((r) => ({ label: r.short, href: `/rubrique/${r.slug}` })),
];

export const FOOTER_LINKS = [
  { label: 'À propos', href: '/infos-societe-editrice' },
  { label: 'Mentions légales', href: '/mentions-du-site' },
  { label: 'Contact', href: '/me-contacter' },
  { label: 'Toutes les rubriques', href: '/rubriques' },
  { label: 'Tous les articles', href: '/articles' },
  { label: 'Flux RSS', href: '/rss.xml' },
];

// Helpers -------------------------------------------------------
const DF = new Intl.DateTimeFormat('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' });
export const formatDate = (d: Date | string) => DF.format(new Date(d));
export const isoDate = (d: Date | string) => new Date(d).toISOString();

// URLs canoniques SANS extension : Cloudflare Pages sert /slug (200) et
// redirige automatiquement l'ancienne URL WordPress /slug.html -> /slug (308).
// Le slug reste strictement identique à l'ancien site.
export const articleUrl = (slug: string) => `/${slug}`;
export const rubriqueUrl = (slug: string) => `/rubrique/${slug}`;
