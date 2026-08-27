/* -------------------------------------------------
   Global UI utilities for Career DNA
   ------------------------------------------------- */

// Smooth scrolling for anchor links
document.addEventListener('click', function (e) {
  const target = e.target.closest('a[href^="#"]');
  if (target) {
    const hash = target.getAttribute('href');
    const element = document.querySelector(hash);
    if (element) {
      e.preventDefault();
      element.scrollIntoView({ behavior: 'smooth' });
      history.pushState(null, null, hash);
    }
  }
});

// Fade‑in animation when elements enter the viewport
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

// Auto‑dismiss flash messages after a few seconds
window.addEventListener('load', () => {
  const flash = document.querySelector('.flash-message');
  if (flash) {
    setTimeout(() => flash.remove(), 4000);
  }
});

// Navigation links visibility override based on current pathname
document.addEventListener("DOMContentLoaded", function () {
  const path = window.location.pathname;

  const assessmentLink = document.getElementById("assessmentLink");
  const startTestBtn = document.getElementById("startTestBtn");

  // If NOT home page → hide Assessment + Start Test
  if (path !== "/" && !path.includes("index.html")) {
    if (assessmentLink) assessmentLink.style.display = "none";
    if (startTestBtn) startTestBtn.style.display = "none";
  }
});

/* -------------------------------------------------
   End of script.js
   ------------------------------------------------- */
