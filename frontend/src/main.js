/**
 * Career DNA — Vite frontend entry point
 *
 * VITE_API_BASE_URL must be set in Vercel environment variables
 * pointing to your Render Flask backend, e.g.:
 *   https://your-careerdna-app.onrender.com
 *
 * Set this in: Vercel → Project → Settings → Environment Variables
 *   Key:   VITE_API_BASE_URL
 *   Value: https://your-careerdna-app.onrender.com
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
 * Build a full URL to a Flask backend route.
 * If API_BASE is not set, returns '#' so the link is inert
 * rather than navigating to a relative /login that Vercel rewrites back to index.html.
 */
function backendUrl(path) {
  return API_BASE ? `${API_BASE}${path}` : '#';
}

// ── Wire navbar links to Flask backend ──────────────────────────
document.getElementById('nav-login-link').href     = backendUrl('/login');
document.getElementById('nav-register-link').href  = backendUrl('/signup');
document.getElementById('nav-career-paths').href   = backendUrl('/career-paths');
document.getElementById('nav-resources').href      = backendUrl('/resources');
document.getElementById('nav-contact').href        = backendUrl('/contact');

// Assessment CTA — send to login then redirect to assessment
document.getElementById('assessment-cta-btn').href = backendUrl('/login?next=/assessment');

// If backend URL is not configured, show a helpful message on click
if (!API_BASE) {
  document.querySelectorAll('a[href="#"]').forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      alert(
        'Backend not configured yet.\n\n' +
        'To connect this frontend to the Flask backend:\n' +
        '1. Go to Vercel → Project → Settings → Environment Variables\n' +
        '2. Add: VITE_API_BASE_URL = https://your-app.onrender.com\n' +
        '3. Redeploy'
      );
    });
  });
}


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
