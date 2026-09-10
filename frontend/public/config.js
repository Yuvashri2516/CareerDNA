/**
 * Career DNA — Frontend Configuration
 *
 * This file is served as a static asset by Vercel at /config.js.
 * It is loaded by standalone public HTML pages (login, register, contact)
 * BEFORE their own JavaScript runs, so they can read window.CAREER_DNA_API_BASE.
 *
 * WHY THIS FILE EXISTS:
 *   Files inside frontend/public/ are copied as-is by Vite and are NOT
 *   processed by Vite's build pipeline. This means import.meta.env.*
 *   substitution does NOT happen in these files. We therefore set the
 *   backend URL here as a plain JS variable so it is always available.
 *
 * IMPORTANT SEPARATION OF CONCERNS:
 *   This URL is used ONLY inside fetch() / API calls.
 *   It must NEVER be used as an href or window.location.href.
 *   All frontend navigation stays within the Vercel domain.
 */
window.CAREER_DNA_API_BASE = "https://career-dna-0ull.onrender.com";
