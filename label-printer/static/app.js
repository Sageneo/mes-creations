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

document.getElementById("save-btn").addEventListener("click", async () => {
  setStatus("Enregistrement de la configuration…");
  try {
    const data = new FormData(form);
    const res = await fetch("/api/config", { method: "POST", body: data });
    const out = await res.json();
    setStatus(out.saved ? "✅ Configuration enregistrée (rechargée au prochain lancement)." : "❌ Échec de l'enregistrement.", out.saved ? "ok" : "err");
  } catch (e) {
    setStatus("❌ " + e.message, "err");
  }
});

async function detectMedia(silent) {
  const out = document.getElementById("media-result");
  if (!silent) out.textContent = "Lecture de l'imprimante…";
  try {
    const printer = encodeURIComponent(form.printer.value || "");
    const res = await fetch("/api/media?printer=" + printer);
    const data = await res.json();
    if (!data.available) {
      out.textContent = silent ? "" : "❌ " + (data.message || "Étiquette non détectée.");
      return;
    }
    const kind = data.media_length ? (data.media_width + "x" + data.media_length + "mm") : (data.media_width + "mm continu");
    let msg = "✅ Détecté : " + kind + " (" + (data.media_type || "?") + ")";
    if (data.label) {
      const opt = Array.from(labelSelect.options).find((o) => o.value === data.label);
      if (opt) { labelSelect.value = data.label; toggleLength(); msg += " → format « " + opt.textContent + " » sélectionné"; }
      else { msg += " — aucun format correspondant dans la liste"; }
    }
    if (data.errors && data.errors.length) msg += " ⚠️ " + data.errors.join(", ");
    out.textContent = msg;
  } catch (e) {
    out.textContent = silent ? "" : "❌ " + e.message;
  }
}

document.getElementById("detect-media-btn").addEventListener("click", () => detectMedia(false));

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

// ----- Mode « code matériel » -----
const codeEnabled = document.getElementById("code_enabled");
const codeFields = document.getElementById("code-fields");
const codeSeries = document.getElementById("code_series");
const seriesEndField = document.getElementById("series-end-field");
const codePrefix = document.getElementById("code_prefix");
const codeYear = document.getElementById("code_year");
const codeNumber = document.getElementById("code_number");
const codePreviewText = document.getElementById("code-preview-text");

function updateCodeMode() {
  const on = codeEnabled.checked;
  codeFields.style.display = on ? "block" : "none";
  document.querySelectorAll(".manual-section").forEach((el) => {
    el.style.display = on ? "none" : "";
  });
  updateCodePreviewText();
}

function updateSeries() {
  seriesEndField.style.display = codeSeries.checked ? "flex" : "none";
  updateCodePreviewText();
}

function updateCodePreviewText() {
  if (!codeEnabled.checked) { codePreviewText.textContent = ""; return; }
  const start = (codeNumber.value || "").padStart(4, "0");
  let txt = codePrefix.value + "-" + codeYear.value + "-" + start;
  if (codeSeries.checked) {
    const end = (document.getElementById("code_number_end").value || "").padStart(4, "0");
    const n = (parseInt(end, 10) - parseInt(start, 10)) + 1;
    txt += " → " + codePrefix.value + "-" + codeYear.value + "-" + end +
           (n > 0 ? "  (" + n + " étiquettes)" : "");
  }
  codePreviewText.textContent = "Code : " + txt;
}

codeEnabled.addEventListener("change", updateCodeMode);
codeSeries.addEventListener("change", updateSeries);
[codePrefix, codeYear, codeNumber, document.getElementById("code_number_end")]
  .forEach((el) => el.addEventListener("input", updateCodePreviewText));

document.getElementById("next-num-btn").addEventListener("click", async () => {
  try {
    const url = "/api/next-number?prefix=" + encodeURIComponent(codePrefix.value) +
                "&year=" + encodeURIComponent(codeYear.value);
    const res = await fetch(url);
    const data = await res.json();
    if (data.number !== undefined) {
      codeNumber.value = data.number;
      updateCodePreviewText();
      setStatus("Prochain numéro libre : " + data.number, "ok");
    } else {
      setStatus("❌ " + (data.error || "Erreur"), "err");
    }
  } catch (e) { setStatus("❌ " + e.message, "err"); }
});

updateCodeMode();
updateSeries();

document.getElementById("quit-btn").addEventListener("click", async () => {
  if (!confirm("Arrêter le programme ? Tu pourras le relancer depuis l'icône.")) return;
  try {
    await fetch("/api/quit", { method: "POST" });
  } catch (e) { /* le serveur se coupe, l'erreur réseau est normale */ }
  document.body.innerHTML =
    "<div style='padding:3rem;text-align:center;font-family:sans-serif'>" +
    "<h2>Programme arrêté ✅</h2><p>Tu peux fermer cet onglet. " +
    "Relance via l'icône « Étiquettes QL-570 ».</p></div>";
});

// Détection automatique de l'étiquette au démarrage (silencieuse).
loadLabelMeta().then(() => detectMedia(true));
