const state = {
  data: null,
  view: "commitments",
  selectedCommitmentId: null,
  modalOpen: false,
  filters: {
    query: "",
    year: "all",
    agency: "all",
    theme: "all",
    commitmentType: "all",
  },
};

const sidebarEl = document.getElementById("sidebar");
const contentEl = document.getElementById("content");
const detailEl = document.getElementById("detail-panel");
const headerStatsEl = document.getElementById("header-stats");
const siteNoteEl = document.getElementById("site-note");
const modalShellEl = document.getElementById("modal-shell");
const modalCloseEl = document.getElementById("modal-close");

document.querySelectorAll(".nav-link").forEach((button) => {
  button.addEventListener("click", () => {
    syncNav(button.dataset.view);
    state.view = button.dataset.view;
    render();
  });
});

modalCloseEl.addEventListener("click", closeModal);
modalShellEl.addEventListener("click", (event) => {
  if (event.target.dataset.closeModal === "true") {
    closeModal();
  }
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && state.modalOpen) {
    closeModal();
  }
});

async function init() {
  const response = await fetch("./data/site-data.json");
  state.data = await response.json();
  const initialId = new URLSearchParams(window.location.search).get("commitment");
  state.selectedCommitmentId = state.data.commitments.find((item) => item.id === initialId)?.id || state.data.commitments[0]?.id || null;
  renderHeaderStats();
  renderSiteNote();
  render();
}

function renderHeaderStats() {
  const totals = state.data.analysis.totals;
  const years = state.data.meta.years_covered.join(", ");
  headerStatsEl.innerHTML = `
    <div class="stat-tile">
      <p class="kicker">Commitments</p>
      <strong>${totals.commitments}</strong>
    </div>
    <div class="stat-tile">
      <p class="kicker">Agencies</p>
      <strong>${totals.agencies}</strong>
    </div>
    <div class="stat-tile">
      <p class="kicker">Themes</p>
      <strong>${totals.themes}</strong>
    </div>
    <div class="stat-tile">
      <p class="kicker">Years Covered</p>
      <strong>${years}</strong>
    </div>
  `;
}

function renderSiteNote() {
  const meta = state.data.meta;
  siteNoteEl.innerHTML = `
    <span>Last updated</span>
    <strong>${escapeHtml(meta.generated_at_label || "")}</strong>
    <span>·</span>
    <span>${escapeHtml(meta.years_covered.join("–"))}</span>
  `;
}

function render() {
  renderSidebar();
  renderContent();
  renderDetail();
  renderModalState();
}

function renderSidebar() {
  const commitments = getFilteredCommitments();
  const years = [...new Set(state.data.commitments.map((item) => item.year))].sort();
  const agencies = state.data.agencies.map((item) => item.name);
  const themes = state.data.themes.map((item) => item.label);
  const commitmentTypes = [...new Set(state.data.commitments.map((item) => item.commitment_type))].sort();

  sidebarEl.innerHTML = `
    <h2 class="panel-title">Browse</h2>
    <div class="filter-group">
      <label for="query">Keyword</label>
      <input id="query" type="search" value="${escapeHtml(state.filters.query)}" placeholder="Search goals, agencies, themes">
    </div>
    <div class="filter-group">
      <label for="year-filter">Year</label>
      <select id="year-filter">
        <option value="all">All years</option>
        ${years.map((year) => `<option value="${year}" ${String(year) === state.filters.year ? "selected" : ""}>${year}</option>`).join("")}
      </select>
    </div>
    <div class="filter-group">
      <label for="agency-filter">Agency</label>
      <select id="agency-filter">
        <option value="all">All agencies</option>
        ${agencies.map((agency) => `<option value="${escapeAttr(agency)}" ${agency === state.filters.agency ? "selected" : ""}>${escapeHtml(agency)}</option>`).join("")}
      </select>
    </div>
    <div class="filter-group">
      <label for="theme-filter">Theme</label>
      <select id="theme-filter">
        <option value="all">All themes</option>
        ${themes.map((theme) => `<option value="${escapeAttr(theme)}" ${theme === state.filters.theme ? "selected" : ""}>${escapeHtml(theme)}</option>`).join("")}
      </select>
    </div>
    <div class="filter-group">
      <label for="type-filter">Commitment Type</label>
      <select id="type-filter">
        <option value="all">All types</option>
        ${commitmentTypes.map((type) => `<option value="${escapeAttr(type)}" ${type === state.filters.commitmentType ? "selected" : ""}>${formatLabel(type)}</option>`).join("")}
      </select>
    </div>
    <div class="filter-group">
      <label>Current selection</label>
      <div class="chip-row">${activeFilterChips()}</div>
    </div>
    <div class="utility-row">
      <button class="utility-button" id="reset-filters">Reset</button>
    </div>
    <div class="detail-block">
      <h3>Result set</h3>
      <p><strong>${commitments.length}</strong> commitments match the current filters.</p>
      <p class="muted">Click any commitment to open a detailed record window.</p>
    </div>
  `;

  bindSidebarEvents();
}

function bindSidebarEvents() {
  sidebarEl.querySelector("#query").addEventListener("input", (event) => {
    state.filters.query = event.target.value;
    render();
  });
  sidebarEl.querySelector("#year-filter").addEventListener("change", (event) => {
    state.filters.year = event.target.value;
    render();
  });
  sidebarEl.querySelector("#agency-filter").addEventListener("change", (event) => {
    state.filters.agency = event.target.value;
    render();
  });
  sidebarEl.querySelector("#theme-filter").addEventListener("change", (event) => {
    state.filters.theme = event.target.value;
    render();
  });
  sidebarEl.querySelector("#type-filter").addEventListener("change", (event) => {
    state.filters.commitmentType = event.target.value;
    render();
  });
  sidebarEl.querySelector("#reset-filters").addEventListener("click", () => {
    state.filters = { query: "", year: "all", agency: "all", theme: "all", commitmentType: "all" };
    render();
  });
  sidebarEl.querySelectorAll("[data-clear-filter]").forEach((button) => {
    button.addEventListener("click", () => {
      const key = button.dataset.clearFilter;
      state.filters[key] = key === "query" ? "" : "all";
      render();
    });
  });
}

function activeFilterChips() {
  const entries = [
    ["query", state.filters.query],
    ["year", state.filters.year !== "all" ? state.filters.year : ""],
    ["agency", state.filters.agency !== "all" ? state.filters.agency : ""],
    ["theme", state.filters.theme !== "all" ? state.filters.theme : ""],
    ["commitmentType", state.filters.commitmentType !== "all" ? formatLabel(state.filters.commitmentType) : ""],
  ].filter(([, value]) => value);

  if (!entries.length) {
    return `<span class="mini-chip">No filters applied</span>`;
  }

  return entries
    .map(([key, value]) => `<span class="chip">${escapeHtml(String(value))} <button type="button" data-clear-filter="${key}" aria-label="Clear ${escapeAttr(key)}">×</button></span>`)
    .join("");
}

function renderContent() {
  switch (state.view) {
    case "agencies":
      renderAgenciesView();
      break;
    case "themes":
      renderThemesView();
      break;
    case "analysis":
      renderAnalysisView();
      break;
    default:
      renderCommitmentsView();
      break;
  }
}

function renderCommitmentsView() {
  const commitments = getFilteredCommitments();
  const years = [...new Set(commitments.map((item) => item.year))].sort();
  const quantified = commitments.filter((item) => item.quantified === "yes").length;
  const continuation = commitments.filter((item) => item.continuity_to_prior_year && item.continuity_to_prior_year !== "new").length;

  contentEl.innerHTML = `
    <div class="view-header">
      <div>
        <h2>Commitments</h2>
        <p>Search the goals directly, or narrow by year, agency, theme, and commitment type.</p>
      </div>
    </div>
    <div class="summary-strip">
      <div class="summary-card">
        <p>Results</p>
        <strong>${commitments.length}</strong>
      </div>
      <div class="summary-card">
        <p>Years in view</p>
        <strong>${years.join(", ") || "None"}</strong>
      </div>
      <div class="summary-card">
        <p>Quantified</p>
        <strong>${quantified}</strong>
      </div>
      <div class="summary-card">
        <p>Carryover items</p>
        <strong>${continuation}</strong>
      </div>
    </div>
    ${commitments.length ? `<div class="commitment-list">${commitments.map(renderCommitmentCard).join("")}</div>` : `<div class="empty-state">No commitments match the current filters.</div>`}
  `;

  contentEl.querySelectorAll(".commitment-card").forEach((card) => {
    card.addEventListener("click", () => openCommitment(card.dataset.commitmentId));
  });
  contentEl.querySelectorAll("[data-theme-jump]").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      state.filters.theme = button.dataset.themeJump;
      render();
    });
  });
}

function renderCommitmentCard(item) {
  return `
    <article class="commitment-card ${item.id === state.selectedCommitmentId ? "is-selected" : ""}" data-commitment-id="${item.id}">
      <div class="meta-line">
        <span class="meta-pill blue">${item.year}</span>
        <span class="meta-pill">${escapeHtml(formatLabel(item.commitment_type))}</span>
        <span class="meta-pill gold">${escapeHtml(item.progress.label)}</span>
      </div>
      <h3>${escapeHtml(item.title)}</h3>
      <p class="muted">${escapeHtml(item.section_bucket)}${item.subsection ? ` · ${escapeHtml(item.subsection)}` : ""}</p>
      <div class="mini-chip-row">
        ${item.theme_labels.map((theme) => `<button class="chip-button" type="button" data-theme-jump="${escapeAttr(theme)}">${escapeHtml(theme)}</button>`).join("")}
      </div>
      <div class="detail-block">
        <p><strong>Agencies:</strong> ${escapeHtml(item.all_agencies.join(", ") || "Not yet coded")}</p>
        <p><strong>Quantified:</strong> ${item.quantified === "yes" ? escapeHtml(item.metric_or_target || "Yes") : "No"}</p>
      </div>
    </article>
  `;
}

function renderAgenciesView() {
  const agencies = state.data.agencies.filter((agency) => {
    const query = state.filters.query.trim().toLowerCase();
    if (!query) return true;
    return agency.name.toLowerCase().includes(query) || agency.top_themes.some((theme) => theme.label.toLowerCase().includes(query));
  });

  contentEl.innerHTML = `
    <div class="view-header">
      <div>
        <h2>Agencies</h2>
        <p>See which agencies own the largest share of commitments and jump directly into their item lists.</p>
      </div>
    </div>
    <div class="card-list">
      ${agencies.map((agency) => `
        <article class="browse-card">
          <h3>${escapeHtml(agency.name)}</h3>
          <div class="meta-line">
            <span class="meta-pill blue">${agency.commitment_count} commitments</span>
            <span class="meta-pill">Lead on ${agency.lead_count}</span>
            <span class="meta-pill">Support on ${agency.support_count}</span>
          </div>
          <div class="mini-chip-row">
            ${agency.top_themes.map((theme) => `<span class="mini-chip">${escapeHtml(theme.label)} (${theme.count})</span>`).join("")}
          </div>
          <div class="utility-row">
            <button class="utility-button" data-open-agency="${escapeAttr(agency.name)}">Open commitments</button>
          </div>
        </article>
      `).join("")}
    </div>
  `;

  contentEl.querySelectorAll("[data-open-agency]").forEach((button) => {
    button.addEventListener("click", () => {
      state.filters.agency = button.dataset.openAgency;
      state.view = "commitments";
      syncNav("commitments");
      render();
    });
  });
}

function renderThemesView() {
  const themes = state.data.themes.filter((theme) => {
    const query = state.filters.query.trim().toLowerCase();
    if (!query) return true;
    return theme.label.toLowerCase().includes(query) || theme.top_agencies.some((agency) => agency.name.toLowerCase().includes(query));
  });

  contentEl.innerHTML = `
    <div class="view-header">
      <div>
        <h2>Themes</h2>
        <p>Themes cut across years and agencies, and they provide a better analytic layer than agency names alone.</p>
      </div>
    </div>
    <div class="card-list">
      ${themes.map((theme) => `
        <article class="browse-card">
          <h3>${escapeHtml(theme.label)}</h3>
          <div class="meta-line">
            <span class="meta-pill blue">${theme.commitment_count} commitments</span>
          </div>
          <div class="mini-chip-row">
            ${theme.top_agencies.map((agency) => `<span class="mini-chip">${escapeHtml(agency.name)} (${agency.count})</span>`).join("")}
          </div>
          <div class="utility-row">
            <button class="utility-button" data-open-theme="${escapeAttr(theme.label)}">Open commitments</button>
          </div>
        </article>
      `).join("")}
    </div>
  `;

  contentEl.querySelectorAll("[data-open-theme]").forEach((button) => {
    button.addEventListener("click", () => {
      state.filters.theme = button.dataset.openTheme;
      state.view = "commitments";
      syncNav("commitments");
      render();
    });
  });
}

function renderAnalysisView() {
  const analysis = state.data.analysis;
  const years = state.data.years;
  const agencies = state.data.agencies.slice(0, 10);
  const themes = state.data.themes.slice(0, 10);

  contentEl.innerHTML = `
    <div class="view-header">
      <div>
        <h2>Analysis</h2>
        <p>This is a first analytical layer over the coded commitments. Progress evidence can plug into the same structure later.</p>
      </div>
    </div>
    <div class="summary-strip">
      <div class="summary-card">
        <p>Commitments</p>
        <strong>${analysis.totals.commitments}</strong>
      </div>
      <div class="summary-card">
        <p>Quantified share</p>
        <strong>${percent(analysis.coded_shares.quantified_yes)}</strong>
      </div>
      <div class="summary-card">
        <p>Binary-evaluable share</p>
        <strong>${percent(analysis.coded_shares.binary_yes)}</strong>
      </div>
      <div class="summary-card">
        <p>Progress reviewed</p>
        <strong>${analysis.progress_counts.not_assessed ? "0%" : "n/a"}</strong>
      </div>
    </div>
    <div class="analysis-grid">
      <section class="analysis-card">
        <h3 class="section-title">Years</h3>
        <div class="bar-list">
          ${years.map((year) => renderBarRow(String(year.year), year.commitment_count, maxValue(years.map((item) => item.commitment_count)))).join("")}
        </div>
      </section>
      <section class="analysis-card">
        <h3 class="section-title">Top Agencies</h3>
        <div class="bar-list">
          ${agencies.map((agency) => renderBarRow(agency.name, agency.commitment_count, maxValue(agencies.map((item) => item.commitment_count)))).join("")}
        </div>
      </section>
      <section class="analysis-card">
        <h3 class="section-title">Top Themes</h3>
        <div class="bar-list">
          ${themes.map((theme) => renderBarRow(theme.label, theme.commitment_count, maxValue(themes.map((item) => item.commitment_count)))).join("")}
        </div>
      </section>
      <section class="analysis-card">
        <h3 class="section-title">Commitment Types</h3>
        <div class="bar-list">
          ${Object.entries(analysis.type_counts).sort((a, b) => b[1] - a[1]).map(([label, count]) => renderBarRow(formatLabel(label), count, maxValue(Object.values(analysis.type_counts)))).join("")}
        </div>
      </section>
    </div>
  `;
}

function renderBarRow(label, value, max) {
  const width = max ? Math.max(6, Math.round((value / max) * 100)) : 0;
  return `
    <div class="bar-row">
      <div>${escapeHtml(label)}</div>
      <div class="bar-track"><div class="bar-fill" style="width:${width}%"></div></div>
      <div>${value}</div>
    </div>
  `;
}

function renderDetail() {
  const item = state.data.commitments.find((commitment) => commitment.id === state.selectedCommitmentId);
  if (!item) {
    detailEl.innerHTML = `<div class="detail-empty"><p>Select a commitment to inspect its coding, source links, and progress fields.</p></div>`;
    return;
  }

  detailEl.innerHTML = `
    <div class="meta-line">
      <span class="meta-pill blue">${item.year}</span>
      <span class="meta-pill">${escapeHtml(formatLabel(item.commitment_type))}</span>
      <span class="meta-pill gold">${escapeHtml(item.progress.label)}</span>
    </div>
    <h2 class="detail-title" id="detail-modal-title">${escapeHtml(item.title)}</h2>
    <p class="muted">${escapeHtml(item.section_bucket)}${item.subsection ? ` · ${escapeHtml(item.subsection)}` : ""}</p>

    <div class="detail-block">
      <h3>Overview</h3>
      <div class="detail-grid">
        <dl>
          <dt>Lead agencies</dt>
          <dd>${escapeHtml(item.lead_agencies.join(", ") || "Not yet coded")}</dd>
        </dl>
        <dl>
          <dt>Supporting agencies</dt>
          <dd>${escapeHtml(item.supporting_agencies.join(", ") || "None listed")}</dd>
        </dl>
        <dl>
          <dt>Theme</dt>
          <dd>${escapeHtml(item.theme_labels.join(", "))}</dd>
        </dl>
        <dl>
          <dt>Implementation pathway</dt>
          <dd>${escapeHtml(formatLabel(item.implementation_pathway))}</dd>
        </dl>
      </div>
    </div>

    <div class="detail-block">
      <h3>Coding</h3>
      <div class="detail-grid">
        <dl>
          <dt>Quantified</dt>
          <dd>${escapeHtml(item.quantified)}</dd>
        </dl>
        <dl>
          <dt>Metric or target</dt>
          <dd>${escapeHtml(item.metric_or_target || "Not specified in the current pass")}</dd>
        </dl>
        <dl>
          <dt>Binary evaluable</dt>
          <dd>${escapeHtml(item.binary_evaluable)}${item.binary_unit ? ` · ${escapeHtml(item.binary_unit)}` : ""}</dd>
        </dl>
        <dl>
          <dt>Continuity to prior year</dt>
          <dd>${escapeHtml(item.continuity_to_prior_year || "Base year / not yet linked")}</dd>
        </dl>
      </div>
      ${item.matched_prior_title ? `<p><strong>Linked prior commitment:</strong> ${escapeHtml(item.matched_prior_title)}</p>` : ""}
      <p><strong>Evidence still needed:</strong> ${escapeHtml(item.status_evidence_needed || "Not yet specified")}</p>
    </div>

    <div class="detail-block">
      <h3>Progress</h3>
      <p><strong>Status:</strong> ${escapeHtml(item.progress.label)}</p>
      <p class="muted">This first draft is ready for evidence records, but no implementation evidence has been added yet.</p>
    </div>

    <div class="detail-block">
      <h3>Source</h3>
      <dl class="detail-list">
        <dt>Document</dt>
        <dd>${escapeHtml(item.source.label)}</dd>
        <dt>Source PDF</dt>
        <dd>${item.source.url ? `<a href="${escapeAttr(item.source.url)}" target="_blank" rel="noreferrer">Open official PDF</a>` : "Not available"}</dd>
        <dt>Program page</dt>
        <dd>${item.source.landing_url ? `<a href="${escapeAttr(item.source.landing_url)}" target="_blank" rel="noreferrer">Open official page</a>` : "Not available"}</dd>
        <dt>Shareable link</dt>
        <dd><a href="${escapeAttr(buildCommitmentHref(item.id))}">${escapeHtml(item.id)}</a></dd>
      </dl>
    </div>
  `;
}

function renderModalState() {
  modalShellEl.classList.toggle("is-open", state.modalOpen);
  modalShellEl.setAttribute("aria-hidden", state.modalOpen ? "false" : "true");
  document.body.style.overflow = state.modalOpen ? "hidden" : "";
}

function openCommitment(id) {
  state.selectedCommitmentId = id;
  state.modalOpen = true;
  updateUrl(id);
  renderDetail();
  renderContent();
  renderModalState();
}

function closeModal() {
  state.modalOpen = false;
  updateUrl(null);
  renderModalState();
}

function updateUrl(id) {
  const url = new URL(window.location.href);
  if (id) {
    url.searchParams.set("commitment", id);
  } else {
    url.searchParams.delete("commitment");
  }
  window.history.replaceState({}, "", url);
}

function buildCommitmentHref(id) {
  const url = new URL(window.location.href);
  url.searchParams.set("commitment", id);
  return url.toString();
}

function getFilteredCommitments() {
  let items = [...state.data.commitments];
  const query = state.filters.query.trim().toLowerCase();

  if (state.filters.year !== "all") items = items.filter((item) => String(item.year) === state.filters.year);
  if (state.filters.agency !== "all") items = items.filter((item) => item.all_agencies.includes(state.filters.agency));
  if (state.filters.theme !== "all") items = items.filter((item) => item.theme_labels.includes(state.filters.theme));
  if (state.filters.commitmentType !== "all") items = items.filter((item) => item.commitment_type === state.filters.commitmentType);
  if (query) {
    items = items.filter((item) => {
      const haystack = [
        item.title,
        item.section_bucket,
        item.subsection,
        item.commitment_type,
        item.implementation_pathway,
        item.metric_or_target,
        item.notes,
        ...item.all_agencies,
        ...item.theme_labels,
      ].join(" ").toLowerCase();
      return haystack.includes(query);
    });
  }

  items.sort((a, b) => (a.year !== b.year ? b.year - a.year : a.title.localeCompare(b.title)));
  if (items.length && !items.some((item) => item.id === state.selectedCommitmentId)) {
    state.selectedCommitmentId = items[0].id;
  }
  return items;
}

function syncNav(view) {
  document.querySelectorAll(".nav-link").forEach((item) => {
    item.classList.toggle("is-active", item.dataset.view === view);
  });
}

function formatLabel(value) {
  return String(value).replaceAll("_", " ").replaceAll("/", " / ").replace(/\b\w/g, (char) => char.toUpperCase());
}

function percent(value) {
  return `${Math.round(value * 100)}%`;
}

function maxValue(values) {
  return Math.max(...values, 1);
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function escapeAttr(value) {
  return escapeHtml(value).replaceAll("'", "&#39;");
}

init().catch((error) => {
  contentEl.innerHTML = `<div class="empty-state">Could not load site data. ${escapeHtml(error.message)}</div>`;
});
