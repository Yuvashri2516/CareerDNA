/**
 * Career DNA — Vite frontend entry point
 *
 * VITE_API_BASE_URL must be set in Vercel environment variables
 * pointing to your Render Flask backend, e.g.
 *   https://your-careerdna-app.onrender.com
 *
 * Set this in: Vercel → Project → Settings → Environment Variables
 *   Key:   VITE_API_BASE_URL
 *   Value: https://your-careerdna-app.onrender.com
 *
 * IMPORTANT SEPARATION OF CONCERNS:
 *   FRONTEND NAVIGATION → use relative frontend routes: /login, /register, etc.
 *   BACKEND API CALLS   → use VITE_API_BASE_URL only inside fetch() / axios()
 *   NEVER use VITE_API_BASE_URL as an href or window.location.href.
 */

const API_BASE = import.meta.env.VITE_API_BASE_URL
  ? import.meta.env.VITE_API_BASE_URL.replace(/\/$/, '') // strip trailing slash
  : null;

if (!API_BASE) {
  console.warn(
    '[Career DNA] VITE_API_BASE_URL is not set.\n' +
    'Set it in Vercel → Project → Settings → Environment Variables.\n' +
    'Value should be your Render backend URL, e.g. https://careerdna.onrender.com'
  );
}

/**
 * Build a full URL to a Flask backend API endpoint.
 * ONLY use this for fetch()/axios() API calls — NEVER for href navigation.
 * Example: fetch(apiUrl('/api/login'), { method: 'POST', body: ... })
 */
function apiUrl(path) {
  return API_BASE ? `${API_BASE}${path}` : null;
}

// ── Wire navbar links to FRONTEND routes (Vercel pages) ──────────
// These navigate within the Vercel frontend — they must NEVER point to the
// Render backend URL. The browser stays on the Vercel domain at all times.
document.getElementById('nav-login-link').href     = '/login';
document.getElementById('nav-register-link').href  = '/register';
document.getElementById('nav-career-paths').href   = '/career-paths';
document.getElementById('nav-resources').href      = '/resources';
document.getElementById('nav-contact').href        = '/contact';

// Assessment CTA — navigate to frontend login page, NOT the backend
document.getElementById('assessment-cta-btn').href = '/login';

// Expose API_BASE and apiUrl globally so frontend pages (login, register)
// can use them for fetch() API calls to the Render backend.
window.CAREER_DNA_API_BASE = API_BASE;
window.careerDnaApiUrl = apiUrl;


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
