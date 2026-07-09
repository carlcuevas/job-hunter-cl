/* ── Job Hunter CL — Frontend App ─────────────────────────────── */

const API = "";   // mismo origen, FastAPI sirve el frontend
let allJobs = [];
let currentJobId = null;
let scrapeInterval = null;

// ── Init ────────────────────────────────────────────────────────
window.addEventListener("DOMContentLoaded", () => {
  loadStats();
  loadTopJobs();
  loadJobs();
  loadApplications();
  checkScrapeStatus();
});

// ── Navigation ──────────────────────────────────────────────────
function showPage(name) {
  document.querySelectorAll(".page").forEach(p => p.classList.remove("active"));
  document.querySelectorAll(".nav-item").forEach(n => n.classList.remove("active"));
  document.getElementById(`page-${name}`).classList.add("active");
  document.querySelector(`[data-page="${name}"]`).classList.add("active");

  if (name === "jobs") loadJobs();
  if (name === "applications") loadApplications();
  if (name === "dashboard") { loadStats(); loadTopJobs(); }
}

// ── Stats ───────────────────────────────────────────────────────
async function loadStats() {
  try {
    const data = await get("/api/jobs/stats");
    document.getElementById("stat-total").textContent = data.total_jobs;
    document.getElementById("stat-new").textContent = data.new_jobs;
    document.getElementById("stat-applied").textContent = data.applied_jobs;
    document.getElementById("stat-interviews").textContent = data.interviews;

    const badge = document.getElementById("badge-new");
    badge.textContent = data.new_jobs;
    badge.style.display = data.new_jobs > 0 ? "inline" : "none";
  } catch (e) { console.error("Stats error:", e); }
}

// ── Top Jobs (Dashboard) ─────────────────────────────────────────
async function loadTopJobs() {
  const container = document.getElementById("top-jobs-list");
  try {
    const data = await get("/api/jobs/?min_score=50");
    const top = (data.jobs || []).filter(j => j.status !== "descartada").slice(0, 6);

    if (!top.length) {
      container.innerHTML = `<div class="empty-state">
        <div class="empty-icon">🔍</div>
        <p>No hay ofertas aún</p>
        <small>Pulsa "Buscar Ofertas" para comenzar</small>
      </div>`;
      return;
    }
    container.innerHTML = top.map(jobCard).join("");
  } catch (e) {
    container.innerHTML = `<div class="empty-state"><div class="empty-icon">⚠️</div><p>Error cargando ofertas</p></div>`;
  }
}

// ── Jobs Page ───────────────────────────────────────────────────
async function loadJobs() {
  const container = document.getElementById("jobs-list");
  container.innerHTML = `<div class="empty-state"><div class="spinner"></div></div>`;

  try {
    const params = buildFilterParams();
    const data = await get(`/api/jobs/?${params}`);
    allJobs = data.jobs || [];
    renderJobs(allJobs);
  } catch (e) {
    container.innerHTML = `<div class="empty-state"><div class="empty-icon">⚠️</div><p>Error cargando ofertas</p></div>`;
  }
}

function buildFilterParams() {
  const search = document.getElementById("search-input")?.value || "";
  const source = document.getElementById("filter-source")?.value || "";
  const status = document.getElementById("filter-status")?.value || "";
  const score = document.getElementById("filter-score")?.value || "0";

  const params = new URLSearchParams();
  if (search) params.set("search", search);
  if (source) params.set("source", source);
  if (status) params.set("status", status);
  if (parseInt(score) > 0) params.set("min_score", score);
  return params.toString();
}

function filterJobs() {
  loadJobs();
}

function renderJobs(jobs) {
  const container = document.getElementById("jobs-list");
  const countEl = document.getElementById("jobs-count");

  countEl.textContent = `${jobs.length} oferta${jobs.length !== 1 ? "s" : ""} encontrada${jobs.length !== 1 ? "s" : ""}`;

  if (!jobs.length) {
    container.innerHTML = `<div class="empty-state">
      <div class="empty-icon">📭</div>
      <p>No hay ofertas con esos filtros</p>
      <small>Prueba cambiando los filtros o buscando nuevas ofertas</small>
    </div>`;
    return;
  }
  container.innerHTML = jobs.map(jobCard).join("");
}

function jobCard(job) {
  const scoreColor = getScoreColor(job.match_score);
  const statusClass = { nueva: "", guardada: "saved", postulada: "applied", descartada: "discarded" }[job.status] || "";
  const sourceClass = job.source === "laborum" ? "source-lab" : job.source === "chiletrabajos" ? "source-ct" : "source-gob";
  const sourceName = job.source === "laborum" ? "Laborum" : job.source === "chiletrabajos" ? "ChileTrabajos" : "Get on Board";
  const tags = (job.match_tags || []).slice(0, 4).map(t => `<span class="match-tag">${t}</span>`).join("");

  return `
  <div class="job-card ${statusClass}" onclick="openJobModal('${job.id}')">
    <div class="job-card-header">
      <div class="job-title">${esc(job.title)}</div>
      <div class="score-badge" style="background:${scoreColor}">${job.match_score}%</div>
    </div>
    <div class="job-company">🏢 ${esc(job.company)}</div>
    <div class="job-meta">
      <span class="tag ${sourceClass}">${sourceName}</span>
      ${job.modality ? `<span class="tag modality">${esc(job.modality)}</span>` : ""}
      ${job.location ? `<span class="tag">📍 ${esc(job.location)}</span>` : ""}
    </div>
    <div class="job-description">${esc(job.description)}</div>
    <div class="job-tags">${tags}</div>
    <div class="job-footer">
      <span class="job-salary">${job.salary ? esc(job.salary) : "Salario no indicado"}</span>
      <span class="job-date">
        <span class="status-dot dot-${job.status}"></span>
        ${statusLabel(job.status)} ${job.posted_at ? "· " + esc(job.posted_at) : ""}
      </span>
    </div>
  </div>`;
}

// ── Job Modal ───────────────────────────────────────────────────
async function openJobModal(jobId) {
  currentJobId = jobId;
  const overlay = document.getElementById("job-modal");
  const content = document.getElementById("modal-content");

  overlay.classList.add("open");
  content.innerHTML = `<div style="text-align:center;padding:40px"><div class="spinner"></div></div>`;

  try {
    const job = await get(`/api/jobs/${jobId}`);
    content.innerHTML = renderJobModal(job);

    // Cargar carta de presentación y campos Get on Board
    if (job.cover_letter) {
      document.getElementById("cover-letter-text").value = job.cover_letter;
    } else {
      const res = await get(`/api/jobs/${jobId}/cover-letter/generate`);
      document.getElementById("cover-letter-text").value = res.cover_letter;
      document.getElementById("gob-experience-text").value = res.gob_experience;
      document.getElementById("gob-education-text").value  = res.gob_education;
      await patch(`/api/jobs/${jobId}/cover-letter`, {
        cover_letter:   res.cover_letter,
        gob_experience: res.gob_experience,
        gob_education:  res.gob_education,
      });
    }
    // Si ya tenía cover_letter guardada, cargar también los campos gob
    if (job.gob_experience) document.getElementById("gob-experience-text").value = job.gob_experience;
    if (job.gob_education)  document.getElementById("gob-education-text").value  = job.gob_education;
  } catch (e) {
    content.innerHTML = `<p style="color:var(--red)">Error cargando oferta</p>`;
  }
}

function renderJobModal(job) {
  const scoreColor = getScoreColor(job.match_score);
  const tags = (job.match_tags || []).map(t => `<span class="match-tag">${esc(t)}</span>`).join("");
  const sourceClass = job.source === "laborum" ? "source-lab" : job.source === "chiletrabajos" ? "source-ct" : "source-gob";
  const sourceName = job.source === "laborum" ? "Laborum" : job.source === "chiletrabajos" ? "ChileTrabajos" : "Get on Board";

  return `
    <div class="modal-title">${esc(job.title)}</div>
    <div class="modal-company">🏢 ${esc(job.company)}</div>
    <div class="modal-meta">
      <span class="tag ${sourceClass}">${sourceName}</span>
      ${job.modality ? `<span class="tag modality">${esc(job.modality)}</span>` : ""}
      ${job.location ? `<span class="tag">📍 ${esc(job.location)}</span>` : ""}
      ${job.salary ? `<span class="tag" style="color:var(--green);border-color:var(--green)">💰 ${esc(job.salary)}</span>` : ""}
    </div>

    <div class="modal-score-bar">
      <div class="score-bar-label">
        <span>Match con tu perfil</span>
        <strong style="color:${scoreColor}">${job.match_score}% — ${getScoreLabel(job.match_score)}</strong>
      </div>
      <div class="score-bar-track">
        <div class="score-bar-fill" style="width:${job.match_score}%;background:${scoreColor}"></div>
      </div>
      <div style="margin-top:10px;display:flex;flex-wrap:wrap;gap:4px">${tags}</div>
    </div>

    <div class="modal-description">${esc(job.description)}</div>

    <div class="cover-letter-section">
      <div class="gob-fields-title">✉️ Campos para postular en Get on Board</div>

      <label class="field-label">
        📋 Experiencia y perfil profesional
        <small>(copia y pega esto en Get on Board)</small>
      </label>
      <textarea id="gob-experience-text" onchange="saveCoverLetter('${job.id}')"></textarea>

      <label class="field-label" style="margin-top:16px">
        🎓 Formación académica y estudios
        <small>(copia y pega esto en Get on Board)</small>
      </label>
      <textarea id="gob-education-text" onchange="saveCoverLetter('${job.id}')" style="min-height:140px"></textarea>

      <label class="field-label" style="margin-top:16px">
        📝 Carta de presentación completa
        <small>(opcional, si el portal la pide)</small>
      </label>
      <textarea id="cover-letter-text" onchange="saveCoverLetter('${job.id}')"></textarea>
    </div>

    <div class="modal-actions">
      <a href="${esc(job.url)}" target="_blank" rel="noopener" class="btn btn-primary" onclick="markApplied('${job.id}')">
        🚀 Abrir y Postular
      </a>
      <button class="btn btn-warning" onclick="saveJob('${job.id}')">🔖 Guardar</button>
      <button class="btn btn-outline" onclick="window.open('${esc(job.url)}','_blank')">🔗 Ver Oferta</button>
      <button class="btn btn-danger" onclick="discardJob('${job.id}')">✕ Descartar</button>
    </div>
  `;
}

function closeJobModal() {
  document.getElementById("job-modal").classList.remove("open");
  currentJobId = null;
}

function closeModal(e) {
  if (e.target === document.getElementById("job-modal")) closeJobModal();
}

// ── Job Actions ─────────────────────────────────────────────────
async function markApplied(jobId) {
  const coverLetter = document.getElementById("cover-letter-text")?.value || "";
  try {
    await post("/api/applications/", { job_id: jobId, cover_letter: coverLetter });
    await patch(`/api/jobs/${jobId}/status`, { status: "postulada" });
    showToast("✅ ¡Postulación registrada!", "success");
    loadStats();
    loadTopJobs();
  } catch (e) {
    console.error(e);
  }
}

async function saveJob(jobId) {
  await patch(`/api/jobs/${jobId}/status`, { status: "guardada" });
  showToast("🔖 Oferta guardada", "info");
  closeJobModal();
  loadStats();
}

async function discardJob(jobId) {
  await patch(`/api/jobs/${jobId}/status`, { status: "descartada" });
  showToast("✕ Oferta descartada", "info");
  closeJobModal();
  loadJobs();
  loadStats();
}

async function saveCoverLetter(jobId) {
  const cover_letter   = document.getElementById("cover-letter-text")?.value || "";
  const gob_experience = document.getElementById("gob-experience-text")?.value || "";
  const gob_education  = document.getElementById("gob-education-text")?.value  || "";
  await patch(`/api/jobs/${jobId}/cover-letter`, { cover_letter, gob_experience, gob_education });
}

// ── Scraper ─────────────────────────────────────────────────────
async function runScraper() {
  const btn = document.getElementById("btn-scrape");
  const icon = document.getElementById("scrape-icon");
  const text = document.getElementById("scrape-text");

  btn.disabled = true;
  btn.classList.add("loading");
  icon.textContent = "⏳";
  text.textContent = "Buscando...";

  try {
    await post("/api/scraper/run", {
      portals: ["getonboard", "chiletrabajos"],
      limit: 50,
    });
    pollScrapeStatus();
  } catch (e) {
    btn.disabled = false;
    btn.classList.remove("loading");
    icon.textContent = "🔍";
    text.textContent = "Buscar Ofertas";
    showToast("Error al iniciar búsqueda", "error");
  }
}

function pollScrapeStatus() {
  if (scrapeInterval) clearInterval(scrapeInterval);
  scrapeInterval = setInterval(checkScrapeStatus, 2000);
}

async function checkScrapeStatus() {
  try {
    const status = await get("/api/scraper/status");
    const btn = document.getElementById("btn-scrape");
    const icon = document.getElementById("scrape-icon");
    const text = document.getElementById("scrape-text");

    if (!status.running) {
      clearInterval(scrapeInterval);
      btn.disabled = false;
      btn.classList.remove("loading");
      icon.textContent = "🔍";
      text.textContent = "Buscar Ofertas";

      if (status.last_run) {
        const count = status.last_count || 0;
        document.getElementById("last-scrape-info").textContent =
          `Última búsqueda: ${count} oferta${count !== 1 ? "s" : ""} encontrada${count !== 1 ? "s" : ""}`;
        showToast(`✅ ${count} ofertas encontradas`, "success");
        loadStats();
        loadTopJobs();
        loadJobs();
      }
    }
  } catch (e) { console.error(e); }
}

// ── Applications ─────────────────────────────────────────────────
async function loadApplications() {
  const container = document.getElementById("applications-list");
  try {
    const data = await get("/api/applications/");
    const apps = data.applications || [];

    if (!apps.length) {
      container.innerHTML = `<div class="empty-state">
        <div class="empty-icon">📭</div>
        <p>Aún no has postulado a ningún trabajo</p>
        <small>Usa el botón "Abrir y Postular" en cada oferta para registrarla</small>
      </div>`;
      return;
    }

    container.innerHTML = apps.map(appCard).join("");
  } catch (e) {
    container.innerHTML = `<div class="empty-state"><div class="empty-icon">⚠️</div><p>Error cargando postulaciones</p></div>`;
  }
}

function appCard(app) {
  const date = app.applied_at ? new Date(app.applied_at).toLocaleDateString("es-CL") : "";
  return `
  <div class="app-card">
    <div>
      <div class="app-title">${esc(app.job_title)}</div>
      <div class="app-company">🏢 ${esc(app.company)}</div>
      <div class="app-date">
        ${app.source === "laborum" ? "Laborum" : app.source === "chiletrabajos" ? "ChileTrabajos" : "Get on Board"} · Postulada el ${date}
      </div>
    </div>
    <div>
      <select class="app-status status-${app.status}"
        onchange="updateAppStatus('${app.id}', this.value, this)">
        <option value="enviada" ${app.status === "enviada" ? "selected" : ""}>Enviada</option>
        <option value="en_revision" ${app.status === "en_revision" ? "selected" : ""}>En revisión</option>
        <option value="entrevista" ${app.status === "entrevista" ? "selected" : ""}>Entrevista 🎉</option>
        <option value="rechazada" ${app.status === "rechazada" ? "selected" : ""}>Rechazada</option>
        <option value="oferta" ${app.status === "oferta" ? "selected" : ""}>Oferta 🏆</option>
      </select>
    </div>
  </div>`;
}

async function updateAppStatus(appId, newStatus, el) {
  el.className = `app-status status-${newStatus}`;
  await patch(`/api/applications/${appId}`, { status: newStatus });
  showToast("Estado actualizado", "success");
  loadStats();
}

// ── HTTP Helpers ─────────────────────────────────────────────────
async function get(url) {
  const r = await fetch(API + url);
  if (!r.ok) throw new Error(`GET ${url} → ${r.status}`);
  return r.json();
}

async function post(url, body) {
  const r = await fetch(API + url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(`POST ${url} → ${r.status}`);
  return r.json();
}

async function patch(url, body) {
  const r = await fetch(API + url, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(`PATCH ${url} → ${r.status}`);
  return r.json();
}

// ── Utils ────────────────────────────────────────────────────────
function esc(str) {
  return String(str || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function getScoreColor(score) {
  if (score >= 75) return "#22c55e";
  if (score >= 50) return "#f59e0b";
  if (score >= 25) return "#f97316";
  return "#ef4444";
}

function getScoreLabel(score) {
  if (score >= 75) return "Excelente match";
  if (score >= 50) return "Buen match";
  if (score >= 25) return "Match regular";
  return "Match bajo";
}

function statusLabel(status) {
  return { nueva: "Nueva", guardada: "Guardada", postulada: "Postulada", descartada: "Descartada" }[status] || status;
}

function showToast(msg, type = "info") {
  const toast = document.getElementById("toast");
  toast.textContent = msg;
  toast.className = `toast ${type} show`;
  setTimeout(() => toast.classList.remove("show"), 3500);
}
