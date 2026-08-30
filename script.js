/**
 * ==========================================================================
 * CLI MATE DATA STORYTELLING WEB SHELL — VANILLA JAVASCRIPT
 * Minimal, lightweight UI interactions & observer logic
 * ==========================================================================
 */

document.addEventListener('DOMContentLoaded', () => {
  initReadingProgressBar();
  initScrollReveal();
  initActiveSectionObserver();
});

/**
 * Updates top progress bar and reading section indicator based on window scroll.
 */
function initReadingProgressBar() {
  const progressBar = document.getElementById('reading-progress-bar');
  const readingIndicator = document.getElementById('reading-indicator');
  const currentPartEl = document.getElementById('current-part');

  if (!progressBar) return;

  function updateProgress() {
    const scrollTop = window.scrollY || document.documentElement.scrollTop;
    const scrollHeight = document.documentElement.scrollHeight - document.documentElement.clientHeight;
    
    if (scrollHeight > 0) {
      const progressPercent = Math.min(100, Math.max(0, (scrollTop / scrollHeight) * 100));
      progressBar.style.width = `${progressPercent}%`;
    }
  }

  window.addEventListener('scroll', updateProgress, { passive: true });
  updateProgress();
}

/**
 * Initializes IntersectionObserver for reveal elements on scroll.
 */
function initScrollReveal() {
  // Check reduced motion preference
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  
  const revealElements = document.querySelectorAll('.reveal-element');
  if (revealElements.length === 0) return;

  if (prefersReducedMotion || !('IntersectionObserver' in window)) {
    revealElements.forEach(el => el.classList.add('is-visible'));
    return;
  }

  const observerOptions = {
    root: null,
    rootMargin: '0px 0px -80px 0px',
    threshold: 0.1
  };

  const observer = new IntersectionObserver((entries, obs) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('is-visible');
        obs.unobserve(entry.target);
      }
    });
  }, observerOptions);

  revealElements.forEach(el => observer.observe(el));
}

/**
 * Observes sections 01, 02, 03 to update the floating part counter (01/03, 02/03, 03/03).
 */
function initActiveSectionObserver() {
  const sections = [
    { id: 'section-01', part: '01', isImpact: false },
    { id: 'section-02', part: '02', isImpact: false },
    { id: 'section-03', part: '03', isImpact: true }
  ];

  const currentPartEl = document.getElementById('current-part');
  const readingIndicator = document.getElementById('reading-indicator');
  const progressBar = document.getElementById('reading-progress-bar');

  if (!('IntersectionObserver' in window)) return;

  const observerOptions = {
    root: null,
    rootMargin: '-30% 0px -40% 0px',
    threshold: 0
  };

  const sectionObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const matchingSec = sections.find(s => s.id === entry.target.id);
        if (matchingSec && currentPartEl) {
          currentPartEl.textContent = matchingSec.part;

          if (matchingSec.isImpact) {
            readingIndicator?.classList.add('is-impact');
            progressBar?.classList.add('is-impact');
          } else {
            readingIndicator?.classList.remove('is-impact');
            progressBar?.classList.remove('is-impact');
          }
        }
      }
    });
  }, observerOptions);

  sections.forEach(sec => {
    const el = document.getElementById(sec.id);
    if (el) sectionObserver.observe(el);
  });
}


