// Code/static/js/cardnav.js
(function () {
  const nav = document.getElementById('card-nav');
  const hamburger = document.getElementById('hamburger');
  const content = nav?.querySelector('.card-nav-content');
  const cards = Array.from(nav?.querySelectorAll('.nav-card') || []);
  let isOpen = false;

  // Nettoyage de toute hauteur inline éventuellement laissée par d'anciennes versions
  if (nav) nav.style.height = '';

  function openMenu() {
    if (!nav || !content) return;
    nav.classList.add('open');
    content.setAttribute('aria-hidden', 'false');
    hamburger?.classList.add('open');
    hamburger?.setAttribute('aria-label', 'Fermer le menu');

    // Apparition des cartes (hauteur gérée par CSS, pas par GSAP)
    if (window.gsap) {
      gsap.fromTo(cards, { y: 10, opacity: 0 }, { y: 0, opacity: 1, duration: 0.25, ease: 'power2.out', stagger: 0.04 });
    }
    isOpen = true;
  }

  function closeMenu() {
    if (!nav || !content) return;
    if (window.gsap) {
      gsap.to(cards, { y: -6, opacity: 0, duration: 0.18, ease: 'power2.in', stagger: 0.03, onComplete: finalize });
    } else {
      finalize();
    }
    function finalize(){
      nav.classList.remove('open');
      content.setAttribute('aria-hidden', 'true');
      hamburger?.classList.remove('open');
      hamburger?.setAttribute('aria-label', 'Ouvrir le menu');
      // S'assurer qu'aucune hauteur inline ne traîne
      nav.style.height = '';
      isOpen = false;
    }
  }

  function toggleMenu() { isOpen ? closeMenu() : openMenu(); }

  hamburger?.addEventListener('click', toggleMenu);
  hamburger?.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggleMenu(); }
  });

  // Au resize : on ne recalcul pas la hauteur (CSS only). On s'assure juste que rien d'inline n’apparaît.
  window.addEventListener('resize', () => {
    if (nav) nav.style.height = '';
  });
})();
