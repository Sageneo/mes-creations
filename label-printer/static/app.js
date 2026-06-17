const form = document.getElementById("label-form");
const statusEl = document.getElementById("status");
const previewImg = document.getElementById("preview-img");
const previewEmpty = document.getElementById("preview-empty");
const labelSelect = document.getElementById("label");
const lengthField = document.getElementById("length-field");

const labelMeta = {};

function setStatus(msg, kind) {
  statusEl.textContent = msg;
  statusEl.className = "status" + (kind ? " " + kind : "");
}

async function loadLabelMeta() {
  try {
    const res = await fetch("/api/labels");
    const list = await res.json();
    list.forEach((l) => (labelMeta[l.id] = l));
    toggleLength();
  } catch (e) { /* ignore */ }
}

function toggleLength() {
  const meta = labelMeta[labelSelect.value];
  lengthField.style.display = meta && meta.continuous === false ? "none" : "flex";
}

labelSelect.addEventListener("change", toggleLength);

async function doPreview() {
  setStatus("Génération de l'aperçu…");
  try {
    const data = new FormData(form);
    const res = await fetch("/api/preview", { method: "POST", body: data });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error || "Erreur d'aperçu");
    }
    const blob = await res.blob();
    previewImg.src = URL.createObjectURL(blob);
    previewImg.style.display = "block";
    previewEmpty.style.display = "none";
    setStatus("");
  } catch (e) {
    setStatus(e.message, "err");
  }
}

document.getElementById("preview-btn").addEventListener("click", doPreview);

form.addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const btn = document.getElementById("print-btn");
  btn.disabled = true;
  setStatus("Envoi à l'imprimante…");
  try {
    const data = new FormData(form);
    const res = await fetch("/api/print", { method: "POST", body: data });
    const out = await res.json();
    if (out.success) {
      setStatus("✅ " + out.message, "ok");
    } else {
      setStatus("❌ " + (out.message || "Échec") + (out.hint ? " — " + out.hint : ""), "err");
    }
  } catch (e) {
    setStatus("❌ " + e.message, "err");
  } finally {
    btn.disabled = false;
  }
});

document.getElementById("detect-btn").addEventListener("click", async () => {
  const out = document.getElementById("detect-result");
  out.textContent = "Recherche…";
  try {
    const res = await fetch("/api/printers");
    const data = await res.json();
    if (data.detected && data.detected.length) {
      const ids = data.detected.map((d) => d.identifier).join(", ");
      out.textContent = "Détecté : " + ids;
      form.printer.value = data.detected[0].identifier;
    } else {
      out.textContent = "Aucune imprimante détectée (valeur par défaut conservée).";
    }
  } catch (e) {
    out.textContent = "Erreur de détection : " + e.message;
  }
});

loadLabelMeta();
