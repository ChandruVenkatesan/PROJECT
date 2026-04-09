/* SDIS — main.js */

/* ── Theme Toggle ───────────────────────── */
function toggleTheme() {
    const body = document.body;
    const btn = document.querySelector(".btn-theme");

    body.classList.toggle("dark-theme");

    if (body.classList.contains("dark-theme")) {
        localStorage.setItem("theme", "dark");
        if (btn) btn.textContent = "☀️";
    } else {
        localStorage.setItem("theme", "light");
        if (btn) btn.textContent = "🌙";
    }
}

/* ── On Page Load ───────────────────────── */
document.addEventListener("DOMContentLoaded", () => {

  /* Load saved theme */
  const savedTheme = localStorage.getItem("theme");
  const btn = document.querySelector(".btn-theme");

  if (savedTheme === "dark") {
    document.body.classList.add("dark-theme");
    if (btn) btn.textContent = "☀️";
  } else {
    if (btn) btn.textContent = "🌙";
  }

  /* Flash auto-dismiss */
  document.querySelectorAll(".flash").forEach(el => {
    setTimeout(() => {
      el.style.transition = "opacity .4s";
      el.style.opacity = "0";
      setTimeout(() => el.remove(), 400);
    }, 5000);
  });

});