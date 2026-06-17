const statusEl = document.getElementById("reg-status");
let allCodes = [];

function setStatus(msg, kind) {
  statusEl.textContent = msg || "";
  statusEl.className = "status" + (kind ? " " + kind : "");
}

function fmtDate(s) {
  if (!s) return "—";
  return s.replace("T", " ").slice(0, 16);
}

function renderCounters(counters) {
  const tb = document.querySelector("#counters tbody");
  tb.innerHTML = "";
  document.getElementById("counters-empty").style.display = counters.length ? "none" : "block";
  counters.forEach((c) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td>${c.prefix}</td><td>${c.year}</td><td>${c.count}</td>` +
      `<td>${c.last}</td><td><strong>${c.next}</strong></td>`;
    tb.appendChild(tr);
  });
}

function renderCodes() {
  const q = document.getElementById("filter").value.trim().toUpperCase();
  const tb = document.querySelector("#codes tbody");
  tb.innerHTML = "";
  const rows = allCodes.filter((c) => !q || c.code.includes(q));
  document.getElementById("codes-empty").style.display = rows.length ? "none" : "block";
  rows.forEach((c) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td>${c.code}</td><td>${c.count || 1}</td>` +
      `<td>${fmtDate(c.first_printed)}</td><td>${fmtDate(c.last_printed)}</td>` +
      `<td><button class="del ghost" data-code="${c.code}">🗑️</button></td>`;
    tb.appendChild(tr);
  });
  tb.querySelectorAll(".del").forEach((b) => b.addEventListener("click", onDelete));
}

async function load() {
  try {
    const res = await fetch("/api/registry");
    const data = await res.json();
    allCodes = data.codes || [];
    document.getElementById("total").textContent = allCodes.length;
    renderCounters(data.counters || []);
    renderCodes();
  } catch (e) {
    setStatus("Erreur de chargement : " + e.message, "err");
  }
}

async function onDelete(ev) {
  const code = ev.target.dataset.code;
  if (!confirm("Supprimer " + code + " du suivi ?")) return;
  const body = new FormData();
  body.append("code", code);
  const res = await fetch("/api/registry/delete", { method: "POST", body });
  const out = await res.json();
  setStatus(out.message, out.success ? "ok" : "err");
  load();
}

document.getElementById("filter").addEventListener("input", renderCodes);
document.getElementById("refresh").addEventListener("click", load);

document.getElementById("import-btn").addEventListener("click", async () => {
  const file = document.getElementById("import-file").files[0];
  if (!file) { setStatus("Choisis d'abord un fichier .json", "err"); return; }
  const body = new FormData();
  body.append("file", file);
  body.append("mode", document.getElementById("import-replace").checked ? "replace" : "merge");
  setStatus("Import en cours…");
  try {
    const res = await fetch("/api/registry/import", { method: "POST", body });
    const out = await res.json();
    setStatus(out.message, out.success ? "ok" : "err");
    if (out.success) load();
  } catch (e) {
    setStatus("Erreur : " + e.message, "err");
  }
});

load();
