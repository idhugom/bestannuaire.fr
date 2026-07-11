// Interactions globales — légères, sans dépendance.
// Ré-exécutées à chaque navigation (View Transitions => astro:page-load).

function initReveal() {
  const els = document.querySelectorAll('[data-reveal]:not(.is-in)');
  if (!('IntersectionObserver' in window) || matchMedia('(prefers-reduced-motion: reduce)').matches) {
    els.forEach((el) => el.classList.add('is-in'));
    return;
  }
  const io = new IntersectionObserver(
    (entries) => {
      entries.forEach((e) => {
        if (e.isIntersecting) { e.target.classList.add('is-in'); io.unobserve(e.target); }
      });
    },
    { rootMargin: '0px 0px -8% 0px', threshold: 0.08 }
  );
  els.forEach((el) => io.observe(el));
}

function initHeader() {
  const header = document.querySelector('[data-header]');
  if (!header || (header as any)._bound) return;
  (header as any)._bound = true;
  let last = window.scrollY;
  let ticking = false;
  const onScroll = () => {
    const y = window.scrollY;
    header.classList.toggle('is-scrolled', y > 10);
    if (y > last && y > 300) header.classList.add('is-hidden');
    else header.classList.remove('is-hidden');
    last = y;
    ticking = false;
  };
  window.addEventListener('scroll', () => {
    if (!ticking) { requestAnimationFrame(onScroll); ticking = true; }
  }, { passive: true });
}

function initBurger() {
  const burger = document.querySelector('[data-burger]');
  const menu = document.querySelector('[data-mobile-nav]');
  if (!burger || !menu || (burger as any)._bound) return;
  (burger as any)._bound = true;
  burger.addEventListener('click', () => {
    const open = menu.classList.toggle('is-open');
    burger.setAttribute('aria-expanded', String(open));
  });
  menu.querySelectorAll('a').forEach((a) =>
    a.addEventListener('click', () => {
      menu.classList.remove('is-open');
      burger.setAttribute('aria-expanded', 'false');
    })
  );
}

function initScrollTop() {
  document.querySelectorAll('[data-scroll-top]').forEach((btn) => {
    if ((btn as any)._bound) return;
    (btn as any)._bound = true;
    btn.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));
  });
}

function initReadingProgress() {
  const bar = document.querySelector('[data-progress]') as HTMLElement | null;
  const article = document.querySelector('[data-article-body]') as HTMLElement | null;
  if (!bar || !article) return;
  const update = () => {
    const rect = article.getBoundingClientRect();
    const total = rect.height - window.innerHeight;
    const scrolled = Math.min(Math.max(-rect.top, 0), Math.max(total, 1));
    bar.style.transform = `scaleX(${total > 0 ? scrolled / total : 0})`;
  };
  update();
  window.addEventListener('scroll', update, { passive: true });
  window.addEventListener('resize', update, { passive: true });
}

function initTOC() {
  const links = document.querySelectorAll('[data-toc] a');
  if (!links.length) return;
  const map = new Map<string, Element>();
  links.forEach((l) => {
    const id = (l.getAttribute('href') || '').replace('#', '');
    if (id) map.set(id, l);
  });
  const headings = document.querySelectorAll('[data-article-body] h2[id]');
  const io = new IntersectionObserver(
    (entries) => {
      entries.forEach((e) => {
        if (e.isIntersecting) {
          links.forEach((l) => l.classList.remove('is-active'));
          map.get(e.target.id)?.classList.add('is-active');
        }
      });
    },
    { rootMargin: '-20% 0px -70% 0px' }
  );
  headings.forEach((h) => io.observe(h));
}

function initShare() {
  document.querySelectorAll('[data-copy-link]').forEach((btn) => {
    if ((btn as any)._bound) return;
    (btn as any)._bound = true;
    btn.addEventListener('click', async () => {
      const url = location.href;
      try {
        if (navigator.share && matchMedia('(max-width: 720px)').matches) {
          await navigator.share({ title: document.title, url });
          return;
        }
        await navigator.clipboard.writeText(url);
      } catch { /* clipboard indisponible */ }
      const prev = btn.textContent;
      btn.textContent = '✓';
      (btn as HTMLElement).setAttribute('title', 'Lien copié !');
      setTimeout(() => { btn.textContent = prev; }, 1400);
    });
  });
}

function initAll() {
  initReveal();
  initHeader();
  initBurger();
  initScrollTop();
  initReadingProgress();
  initTOC();
  initShare();
}

document.addEventListener('astro:page-load', initAll);
if (document.readyState !== 'loading') initAll();
else document.addEventListener('DOMContentLoaded', initAll);
