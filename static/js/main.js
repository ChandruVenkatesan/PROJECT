/* ═══════════════════════════════════════════
   SDIS — main.js
   Global utilities:
     - Theme toggle (light / dark)
     - Flash message auto-dismiss
     - Active nav link highlight
   ═══════════════════════════════════════════ */


/* ── Theme Toggle ───────────────────────────
   FIX 2: toggleTheme() was called in base.html
   but was never defined anywhere.
   This is the correct implementation.
   ─────────────────────────────────────────── */

function toggleTheme() {
  const isLight = document.body.classList.toggle("light-mode");
  const btn = document.querySelector(".btn-theme");
  if (btn) {
    btn.textContent = isLight ? "☀️" : "🌙";
    btn.title = isLight ? "Switch to dark mode" : "Switch to light mode";
  }
  // Persist preference so theme survives page navigation
  localStorage.setItem("sdis-theme", isLight ? "light" : "dark");
}

/* Restore saved theme on every page load */
(function applyStoredTheme() {
  const saved = localStorage.getItem("sdis-theme");
  if (saved === "light") {
    document.body.classList.add("light-mode");
    /* btn not yet in DOM at this point — handled in DOMContentLoaded */
  }
})();


/* ── DOMContentLoaded ────────────────────── */
document.addEventListener("DOMContentLoaded", () => {

  /* Sync theme button icon with saved preference */
  const btn = document.querySelector(".btn-theme");
  if (btn && localStorage.getItem("sdis-theme") === "light") {
    btn.textContent = "☀️";
    btn.title = "Switch to dark mode";
  }

  /* Auto-dismiss flash messages after 5 seconds */
  document.querySelectorAll(".flash").forEach((el) => {
    setTimeout(() => {
      el.style.transition = "opacity 0.4s ease";
      el.style.opacity = "0";
      setTimeout(() => el.remove(), 400);
    }, 5000);
  });

  /* Highlight active nav link based on current path */
  const path = window.location.pathname;
  document.querySelectorAll(".nav-link").forEach((link) => {
    const href = link.getAttribute("href");
    if (href && path.startsWith(href) && href !== "/") {
      link.classList.add("active");
    }
  });

});