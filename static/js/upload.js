/* SDIS — upload.js: drag & drop + file preview */
(function () {
  const zone  = document.getElementById("dropZone");
  const input = document.getElementById("fileInput");
  const list  = document.getElementById("fileList");
  const btn   = document.getElementById("uploadBtn");
  if (!zone) return;

  const ALLOWED = ["pdf","docx","txt","png","jpg","jpeg"];

  input.addEventListener("change", () => render(input.files));
  zone.addEventListener("click", e => { if (e.target.tagName !== "LABEL") input.click(); });

  ["dragenter","dragover"].forEach(ev =>
    zone.addEventListener(ev, e => { e.preventDefault(); zone.classList.add("drag-over"); }));
  ["dragleave","drop"].forEach(ev =>
    zone.addEventListener(ev, e => { e.preventDefault(); zone.classList.remove("drag-over"); }));
  zone.addEventListener("drop", e => { input.files = e.dataTransfer.files; render(e.dataTransfer.files); });

  function render(files) {
    list.innerHTML = "";
    let ok = 0;
    Array.from(files).forEach(f => {
      const ext = f.name.split(".").pop().toLowerCase();
      const valid = ALLOWED.includes(ext);
      if (valid) ok++;
      const el = document.createElement("div");
      el.className = "file-item";
      el.innerHTML = `
        <span class="ftype ftype--${ext}">${ext.toUpperCase()}</span>
        <span class="file-item-name">${f.name}</span>
        <span class="file-item-size">${fmt(f.size)}</span>
        ${!valid ? '<span style="color:var(--red);font-size:.78rem">✕ Unsupported</span>' : ""}`;
      list.appendChild(el);
    });
    list.classList.toggle("hidden", !files.length);
    btn.disabled = ok === 0;
    btn.textContent = ok ? `Upload & Index ${ok} File${ok > 1 ? "s" : ""}` : "Upload & Index";
  }

  function fmt(b) {
    if (b < 1024) return b + " B";
    if (b < 1048576) return (b/1024).toFixed(1) + " KB";
    return (b/1048576).toFixed(1) + " MB";
  }
})();
