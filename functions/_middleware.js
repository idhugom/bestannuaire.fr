// Redirection 301 du domaine apex (sans www) vers www, côté edge Cloudflare.
// bestannuaire.fr/... -> https://www.bestannuaire.fr/...  (chemin + query conservés)
export async function onRequest(context) {
  const url = new URL(context.request.url);
  if (url.hostname === 'bestannuaire.fr') {
    url.hostname = 'www.bestannuaire.fr';
    return Response.redirect(url.toString(), 301);
  }
  return context.next();
}
