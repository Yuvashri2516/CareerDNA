/**
 * Career DNA — Vite frontend entry point
 *
 * VITE_API_BASE_URL must be set in Vercel environment variables
 * pointing to your Render Flask backend, e.g.:
 *   https://your-app.onrender.com
 *
 * If the variable is not set (e.g. local dev), defaults to empty
 * string so relative links still work when running Flask locally.
 */

const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

// ── Wire navbar links to Flask backend ──────────────────────────
document.getElementById('nav-login-link').href     = `${API_BASE}/login`;
document.getElementById('nav-register-link').href  = `${API_BASE}/signup`;
document.getElementById('nav-career-paths').href   = `${API_BASE}/career-paths`;
document.getElementById('nav-resources').href      = `${API_BASE}/resources`;
document.getElementById('nav-contact').href        = `${API_BASE}/contact`;

// Assessment CTA — send to login then redirect to assessment
document.getElementById('assessment-cta-btn').href = `${API_BASE}/login?next=/assessment`;

// ── Smooth scrolling for anchor links ───────────────────────────
document.addEventListener('click', function (e) {
  const target = e.target.closest('a[href^="#"]');
  if (target) {
    const hash = target.getAttribute('href');
    if (hash === '#') return; // skip bare # links
    const element = document.querySelector(hash);
    if (element) {
      e.preventDefault();
      element.scrollIntoView({ behavior: 'smooth' });
      history.pushState(null, null, hash);
    }
  }
});

// ── Fade-in animation on scroll ─────────────────────────────────
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('fade-in');
      observer.unobserve(entry.target);
    }
  });
}, { threshold: 0.15 });

document.querySelectorAll('.glass-card, .feature-card, .cert-card, .skill-progress-item')
  .forEach(el => observer.observe(el));

// ── Auto-dismiss flash messages ──────────────────────────────────
window.addEventListener('load', () => {
  const flash = document.querySelector('.flash-message');
  if (flash) {
    setTimeout(() => flash.remove(), 4000);
  }
});
