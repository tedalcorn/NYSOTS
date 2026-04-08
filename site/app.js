const state = {
  data: null,
  view: "commitments",
  selectedCommitmentId: null,
  selectedAgencyName: null,
  modalOpen: false,
  modalType: "commitment",
  modalHistory: [],
  filters: {
    query: "",
    years: [],
    agency: "all",
    theme: "all",
    commitmentType: "all",
    textCapture: "all",
  },
  sorts: {
    commitments: { key: "year", dir: "desc" },
    agencies: { key: "name", dir: "asc" },
    themes: { key: "label", dir: "asc" },
    agencyCommitments: { key: "year", dir: "desc" },
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
  if (event.key === "Backspace" && state.modalOpen && state.modalHistory.length) {
    const target = event.target;
    const typing =
      target instanceof HTMLInputElement ||
      target instanceof HTMLTextAreaElement ||
      target?.isContentEditable;
    if (!typing) {
      event.preventDefault();
      goBackModal();
    }
  }
  if (event.key === "Escape" && state.modalOpen) {
    closeModal();
  }
});

async function init() {
  const response = await fetch("./data/site-data.json");
  state.data = await response.json();
  const initialId = new URLSearchParams(window.location.search).get("commitment");
  state.selectedCommitmentId = state.data.commitments.find((item) => item.id === initialId)?.id || state.data.commitments[0]?.id || null;
  state.selectedAgencyName = state.data.agencies[0]?.name || null;
  renderHeaderStats();
  renderSiteNote();
  render();
}

function renderHeaderStats() {
  headerStatsEl.innerHTML = "";
}

function renderSiteNote() {
  const meta = state.data.meta;
  siteNoteEl.innerHTML = `
    <span>Last updated</span>
    <strong>${escapeHtml(meta.generated_at_label || "")}</strong>
  `;
}

function render() {
  renderSidebar();
  renderContent();
  renderDetail();
  renderModalState();
}

function renderSidebar() {
  const years = [...new Set(state.data.commitments.map((item) => item.year))].sort();
  const agencies = state.data.agencies.map((item) => item.name);
  const themes = state.data.themes.map((item) => item.label);
  const commitmentTypes = [...new Set(state.data.commitments.map((item) => item.commitment_type))].sort();

  sidebarEl.innerHTML = `
    <div class="filter-group">
      <label for="query">Search by keyword</label>
      <input id="query" type="search" value="${escapeHtml(state.filters.query)}" placeholder="Search goals, agencies, themes">
    </div>
    <div class="filter-group">
      <label>Years</label>
      <div class="checkbox-row">
        ${years.map((year) => `
          <label class="year-check">
            <input type="checkbox" data-year-check="${year}" ${state.filters.years.includes(String(year)) ? "checked" : ""}>
            <span>${year}</span>
          </label>
        `).join("")}
      </div>
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
      <label for="text-capture-filter">Text capture</label>
      <select id="text-capture-filter">
        <option value="all">All</option>
        <option value="high" ${state.filters.textCapture === "high" ? "selected" : ""}>High</option>
        <option value="medium" ${state.filters.textCapture === "medium" ? "selected" : ""}>Medium</option>
        <option value="missing" ${state.filters.textCapture === "missing" ? "selected" : ""}>Missing</option>
      </select>
    </div>
    <div class="utility-row">
      <button class="utility-button" id="reset-filters">Reset</button>
    </div>
  `;

  bindSidebarEvents();
}

function bindSidebarEvents() {
  sidebarEl.querySelector("#query").addEventListener("input", (event) => {
    state.filters.query = event.target.value;
    renderWithPreservedQuery(event.target);
  });
  sidebarEl.querySelectorAll("[data-year-check]").forEach((checkbox) => {
    checkbox.addEventListener("change", (event) => {
      const year = event.target.dataset.yearCheck;
      state.filters.years = event.target.checked
        ? [...new Set([...state.filters.years, year])].sort()
        : state.filters.years.filter((item) => item !== year);
      render();
    });
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
  sidebarEl.querySelector("#text-capture-filter").addEventListener("change", (event) => {
    state.filters.textCapture = event.target.value;
    render();
  });
  sidebarEl.querySelector("#reset-filters").addEventListener("click", () => {
    state.filters = { query: "", years: [], agency: "all", theme: "all", commitmentType: "all", textCapture: "all" };
    render();
  });
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
  const commitments = sortCommitments(getFilteredCommitments(), state.sorts.commitments);

  contentEl.innerHTML = `
    <div class="view-header">
      <div>
        <h2>Commitments</h2>
      </div>
    </div>
    ${commitments.length ? renderCommitmentTable(commitments) : `<div class="empty-state">No commitments match the current filters.</div>`}
  `;

  contentEl.querySelectorAll("[data-commitment-id]").forEach((row) => {
    row.addEventListener("click", () => openCommitment(row.dataset.commitmentId));
  });
  bindSortControls("commitments");
}

function renderCommitmentTable(commitments) {
  return `
    <div class="dense-table">
      <div class="dense-head dense-row">
        <button class="sort-button" type="button" data-sort-table="commitments" data-sort-key="year">${renderSortLabel("Year", "commitments", "year")}</button>
        <button class="sort-button" type="button" data-sort-table="commitments" data-sort-key="title">${renderSortLabel("Commitment", "commitments", "title")}</button>
        <button class="sort-button" type="button" data-sort-table="commitments" data-sort-key="agency">${renderSortLabel("Primary Agency", "commitments", "agency")}</button>
        <button class="sort-button" type="button" data-sort-table="commitments" data-sort-key="theme">${renderSortLabel("Theme", "commitments", "theme")}</button>
        <button class="sort-button" type="button" data-sort-table="commitments" data-sort-key="text">${renderSortLabel("Text", "commitments", "text")}</button>
      </div>
      ${commitments.map(renderCommitmentRow).join("")}
    </div>
  `;
}

function renderCommitmentRow(item) {
  const primaryAgency = item.lead_agencies.join(", ") || item.all_agencies.join(", ") || "Not yet coded";
  return `
    <button class="dense-row dense-button ${item.id === state.selectedCommitmentId ? "is-selected" : ""}" type="button" data-commitment-id="${item.id}">
      <div>${item.year}</div>
      <div class="dense-title" title="${escapeAttr(item.title)}">${escapeHtml(item.title)}</div>
      <div title="${escapeAttr(primaryAgency)}">${escapeHtml(primaryAgency)}</div>
      <div title="${escapeAttr(item.theme_labels[0] || "")}">${escapeHtml(item.theme_labels[0] || "")}</div>
      <div>${escapeHtml(formatConfidence(item.text_capture_confidence))}</div>
    </button>
  `;
}

function renderAgenciesView() {
  const agencies = sortAgencies(state.data.agencies.filter((agency) => {
    const query = state.filters.query.trim().toLowerCase();
    if (!query) return true;
    return agency.name.toLowerCase().includes(query) || agency.top_themes.some((theme) => theme.label.toLowerCase().includes(query));
  }), state.sorts.agencies);

  contentEl.innerHTML = `
    <div class="view-header">
      <div>
        <h2>Agencies</h2>
      </div>
    </div>
    <div class="dense-table dense-table-agencies">
      <div class="dense-head dense-row">
        <button class="sort-button" type="button" data-sort-table="agencies" data-sort-key="name">${renderSortLabel("Agency", "agencies", "name")}</button>
        <button class="sort-button" type="button" data-sort-table="agencies" data-sort-key="count">${renderSortLabel("Commitments", "agencies", "count")}</button>
      </div>
      ${agencies.map((agency) => `
        <button class="dense-row dense-button ${agency.name === state.selectedAgencyName ? "is-selected" : ""}" type="button" data-open-agency="${escapeAttr(agency.name)}">
          <div class="dense-title" title="${escapeAttr(agency.name)}">${escapeHtml(agency.name)}</div>
          <div>${agency.commitment_count}</div>
        </button>
      `).join("")}
    </div>
  `;

  contentEl.querySelectorAll("[data-open-agency]").forEach((button) => {
    button.addEventListener("click", () => {
      openAgency(button.dataset.openAgency);
    });
  });
  bindSortControls("agencies");
}

function renderThemesView() {
  const themes = sortThemes(state.data.themes.filter((theme) => {
    const query = state.filters.query.trim().toLowerCase();
    if (!query) return true;
    return theme.label.toLowerCase().includes(query) || theme.top_agencies.some((agency) => agency.name.toLowerCase().includes(query));
  }), state.sorts.themes);

  contentEl.innerHTML = `
    <div class="view-header">
      <div>
        <h2>Themes</h2>
      </div>
    </div>
    <div class="dense-table dense-table-agencies">
      <div class="dense-head dense-row">
        <button class="sort-button" type="button" data-sort-table="themes" data-sort-key="label">${renderSortLabel("Theme", "themes", "label")}</button>
        <button class="sort-button" type="button" data-sort-table="themes" data-sort-key="count">${renderSortLabel("Commitments", "themes", "count")}</button>
      </div>
      ${themes.map((theme) => `
        <button class="dense-row dense-button" type="button" data-open-theme="${escapeAttr(theme.label)}">
          <div class="dense-title" title="${escapeAttr(theme.label)}">${escapeHtml(theme.label)}</div>
          <div>${theme.commitment_count}</div>
        </button>
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
  bindSortControls("themes");
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
  if (state.modalType === "agency") {
    renderAgencyDetail();
    return;
  }
  const item = state.data.commitments.find((commitment) => commitment.id === state.selectedCommitmentId);
  if (!item) {
    detailEl.innerHTML = `<div class="detail-empty"><p>Select a commitment to inspect its coding, source links, and progress fields.</p></div>`;
    return;
  }
  const linkedPriorLabel = item.matched_prior_title && item.year > 2022 ? `${item.year - 1}: ${item.matched_prior_title}` : "";
  const sourceSection = item.subsection || item.section_bucket || "";
  const sourceParts = [
    item.source.url ? `<a href="${escapeAttr(item.source.url)}" target="_blank" rel="noreferrer">${escapeHtml(item.source.label)}</a>` : escapeHtml(item.source.label),
    sourceSection ? escapeHtml(sourceSection) : "",
    item.source_page ? `p. ${escapeHtml(item.source_page)}${item.source_page_end && item.source_page_end !== item.source_page ? `-${escapeHtml(item.source_page_end)}` : ""}` : "",
    item.text_capture_confidence ? `text: ${escapeHtml(formatConfidence(item.text_capture_confidence))}` : "",
  ].filter(Boolean);
  const relatedPrior = item.matched_prior_title
    ? `<div class="detail-block">
      <h3>Related Prior Commitment(s)</h3>
      <p>${item.matched_prior_commitment_id ? `<button class="inline-link" type="button" data-jump-related="${escapeAttr(item.matched_prior_commitment_id)}">${escapeHtml(linkedPriorLabel)}</button>` : escapeHtml(linkedPriorLabel)}</p>
    </div>`
    : "";

  detailEl.innerHTML = `
    ${renderModalToolbar()}
    <div class="meta-line">
      <span class="meta-pill blue">${item.year}</span>
      <span class="meta-pill">${escapeHtml(formatLabel(item.commitment_type))}</span>
    </div>
    <h2 class="detail-title" id="detail-modal-title">Commitment: ${escapeHtml(item.title)}</h2>
    ${item.commitment_text ? `<div class="detail-block"><div class="blurb-text">${renderParagraphs(item.commitment_text)}</div></div>` : ""}

    <div class="detail-block">
      <div class="detail-grid">
        <dl>
          <dt>Lead agencies</dt>
          <dd>${renderAgencyLinks(item.lead_agencies)}</dd>
        </dl>
        <dl>
          <dt>Supporting agencies</dt>
          <dd>${renderAgencyLinks(item.supporting_agencies)}</dd>
        </dl>
        <dl>
          <dt>Theme</dt>
          <dd>${renderBlankableText(item.theme_labels.join(", "))}</dd>
        </dl>
        <dl>
          <dt>Implementation pathway</dt>
          <dd>${escapeHtml(formatLabel(item.implementation_pathway))}</dd>
        </dl>
      </div>
    </div>

    <div class="detail-block">
      <h3>Progress</h3>
      <div class="line-field"><span class="line-label">Quantified Goal?</span><span>${item.quantified === "yes" ? "Y" : item.quantified === "no" ? "N" : ""}</span></div>
      <div class="line-field"><span class="line-label">Indicator:</span><span>${renderBlankableText(item.indicator)}</span></div>
      <div class="line-field"><span class="line-label">Progress report:</span><span></span></div>
    </div>

    ${relatedPrior}

    <div class="detail-block">
      <h3>Source</h3>
      <p class="source-line">${sourceParts.map((part) => `<span>${part}</span>`).join(`<span class="source-sep">·</span>`)}</p>
    </div>
  `;

  bindDetailEvents();
}

function renderAgencyDetail() {
  const agency = state.data.agencies.find((item) => item.name === state.selectedAgencyName);
  if (!agency) {
    detailEl.innerHTML = `<div class="detail-empty"><p>Select an agency to inspect its commitments.</p></div>`;
    return;
  }
  const commitments = sortCommitments(agency.commitment_ids
    .map((id) => state.data.commitments.find((item) => item.id === id))
    .filter(Boolean)
  , state.sorts.agencyCommitments);

  detailEl.innerHTML = `
    ${renderModalToolbar()}
    <div class="meta-line">
      <span class="meta-pill blue">${agency.commitment_count} commitments</span>
      <span class="meta-pill">Lead on ${agency.lead_count}</span>
      <span class="meta-pill">Support on ${agency.support_count}</span>
    </div>
    <h2 class="detail-title" id="detail-modal-title">${escapeHtml(agency.name)}</h2>
    <div class="detail-block">
      <h3>Commitments</h3>
      <div class="dense-table dense-table-modal">
        <div class="dense-head dense-row">
          <button class="sort-button" type="button" data-sort-table="agencyCommitments" data-sort-key="year">${renderSortLabel("Year", "agencyCommitments", "year")}</button>
          <button class="sort-button" type="button" data-sort-table="agencyCommitments" data-sort-key="title">${renderSortLabel("Commitment", "agencyCommitments", "title")}</button>
          <button class="sort-button" type="button" data-sort-table="agencyCommitments" data-sort-key="theme">${renderSortLabel("Theme", "agencyCommitments", "theme")}</button>
        </div>
        ${commitments.map((item) => `
          <button class="dense-row dense-button" type="button" data-jump-commitment="${item.id}">
            <div>${item.year}</div>
            <div class="dense-title" title="${escapeAttr(item.title)}">${escapeHtml(item.title)}</div>
            <div title="${escapeAttr(item.theme_labels[0] || "")}">${escapeHtml(item.theme_labels[0] || "")}</div>
          </button>
        `).join("")}
      </div>
    </div>
  `;

  detailEl.querySelectorAll("[data-jump-commitment]").forEach((button) => {
    button.addEventListener("click", () => openCommitment(button.dataset.jumpCommitment, { preserve: true }));
  });
  bindSortControls("agencyCommitments", detailEl);
  bindDetailEvents();
}

function renderModalState() {
  modalShellEl.classList.toggle("is-open", state.modalOpen);
  modalShellEl.setAttribute("aria-hidden", state.modalOpen ? "false" : "true");
  modalShellEl.querySelector(".detail-modal").classList.toggle("is-wide", state.modalType === "agency");
  document.body.style.overflow = state.modalOpen ? "hidden" : "";
}

function openCommitment(id, options = {}) {
  pushModalHistory(options);
  state.selectedCommitmentId = id;
  state.modalType = "commitment";
  state.modalOpen = true;
  updateUrl(id);
  renderDetail();
  renderContent();
  renderModalState();
}

function openAgency(name, options = {}) {
  pushModalHistory(options);
  state.selectedAgencyName = name;
  state.modalType = "agency";
  state.modalOpen = true;
  updateUrl(null);
  renderDetail();
  renderContent();
  renderModalState();
}

function closeModal() {
  state.modalOpen = false;
  state.modalHistory = [];
  updateUrl(null);
  renderModalState();
}

function goBackModal() {
  const previous = state.modalHistory.pop();
  if (!previous) return;
  state.modalType = previous.type;
  state.selectedCommitmentId = previous.commitmentId;
  state.selectedAgencyName = previous.agencyName;
  state.modalOpen = true;
  updateUrl(previous.type === "commitment" ? previous.commitmentId : null);
  renderDetail();
  renderContent();
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

  if (state.filters.years.length) items = items.filter((item) => state.filters.years.includes(String(item.year)));
  if (state.filters.agency !== "all") items = items.filter((item) => item.all_agencies.includes(state.filters.agency));
  if (state.filters.theme !== "all") items = items.filter((item) => item.theme_labels.includes(state.filters.theme));
  if (state.filters.commitmentType !== "all") items = items.filter((item) => item.commitment_type === state.filters.commitmentType);
  if (state.filters.textCapture !== "all") items = items.filter((item) => (item.text_capture_confidence || "missing") === state.filters.textCapture);
  if (query) {
    items = items.filter((item) => {
      const haystack = [
        item.title,
        item.commitment_text,
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

function bindSortControls(tableName, root = contentEl) {
  root.querySelectorAll(`[data-sort-table="${tableName}"]`).forEach((button) => {
    button.addEventListener("click", () => {
      toggleSort(tableName, button.dataset.sortKey);
      if (tableName === "agencyCommitments") {
        renderDetail();
      } else {
        renderContent();
      }
    });
  });
}

function bindDetailEvents() {
  detailEl.querySelector("[data-go-back]")?.addEventListener("click", goBackModal);
  detailEl.querySelectorAll("[data-open-agency-link]").forEach((button) => {
    button.addEventListener("click", () => openAgency(button.dataset.openAgencyLink, { preserve: true }));
  });
  detailEl.querySelectorAll("[data-jump-related]").forEach((button) => {
    button.addEventListener("click", () => openCommitment(button.dataset.jumpRelated, { preserve: true }));
  });
}

function renderModalToolbar() {
  return `
    <div class="modal-toolbar">
      ${state.modalHistory.length ? `<button class="back-button" type="button" data-go-back="true" aria-label="Go back">←</button>` : `<span></span>`}
    </div>
  `;
}

function renderAgencyLinks(agencies) {
  if (!agencies.length) return "";
  return agencies
    .map((agency) => `<button class="inline-link" type="button" data-open-agency-link="${escapeAttr(agency)}">${escapeHtml(agency)}</button>`)
    .join(", ");
}

function renderBlankableText(value) {
  return value ? escapeHtml(String(value)) : "";
}

function renderParagraphs(text) {
  return text
    .split(/\n{2,}/)
    .map((paragraph) => normalizeParagraph(paragraph))
    .filter(Boolean)
    .map((paragraph) => `<p>${escapeHtml(paragraph)}</p>`)
    .join("");
}

function normalizeParagraph(text) {
  return text.replace(/\s+/g, " ").trim();
}

function pushModalHistory(options) {
  if (!options.preserve || !state.modalOpen) return;
  state.modalHistory.push({
    type: state.modalType,
    commitmentId: state.selectedCommitmentId,
    agencyName: state.selectedAgencyName,
  });
}

function toggleSort(tableName, key) {
  const current = state.sorts[tableName];
  state.sorts[tableName] = {
    key,
    dir: current.key === key && current.dir === "asc" ? "desc" : "asc",
  };
}

function renderSortLabel(label, tableName, key) {
  const sort = state.sorts[tableName];
  if (sort.key !== key) return escapeHtml(label);
  return `${escapeHtml(label)} ${sort.dir === "asc" ? "↑" : "↓"}`;
}

function sortCommitments(items, sort) {
  const sorted = [...items];
  sorted.sort((a, b) => {
    let left = "";
    let right = "";
    if (sort.key === "year") {
      left = a.year;
      right = b.year;
    } else if (sort.key === "agency") {
      left = (a.lead_agencies.join(", ") || a.all_agencies.join(", ")).toLowerCase();
      right = (b.lead_agencies.join(", ") || b.all_agencies.join(", ")).toLowerCase();
    } else if (sort.key === "theme") {
      left = (a.theme_labels[0] || "").toLowerCase();
      right = (b.theme_labels[0] || "").toLowerCase();
    } else if (sort.key === "text") {
      left = confidenceRank(a.text_capture_confidence);
      right = confidenceRank(b.text_capture_confidence);
    } else {
      left = a.title.toLowerCase();
      right = b.title.toLowerCase();
    }
    if (left < right) return sort.dir === "asc" ? -1 : 1;
    if (left > right) return sort.dir === "asc" ? 1 : -1;
    return a.title.localeCompare(b.title);
  });
  return sorted;
}

function renderWithPreservedQuery(input) {
  const value = input.value;
  const start = input.selectionStart ?? value.length;
  const end = input.selectionEnd ?? value.length;
  render();
  const next = sidebarEl.querySelector("#query");
  if (!next) return;
  next.focus();
  next.setSelectionRange(start, end);
}

function confidenceRank(value) {
  if (value === "high") return 3;
  if (value === "medium") return 2;
  return 1;
}

function formatConfidence(value) {
  if (value === "high") return "High";
  if (value === "medium") return "Medium";
  return "Missing";
}

function sortAgencies(items, sort) {
  const sorted = [...items];
  sorted.sort((a, b) => {
    const left = sort.key === "count" ? a.commitment_count : a.name.toLowerCase();
    const right = sort.key === "count" ? b.commitment_count : b.name.toLowerCase();
    if (left < right) return sort.dir === "asc" ? -1 : 1;
    if (left > right) return sort.dir === "asc" ? 1 : -1;
    return a.name.localeCompare(b.name);
  });
  return sorted;
}

function sortThemes(items, sort) {
  const sorted = [...items];
  sorted.sort((a, b) => {
    const left = sort.key === "count" ? a.commitment_count : a.label.toLowerCase();
    const right = sort.key === "count" ? b.commitment_count : b.label.toLowerCase();
    if (left < right) return sort.dir === "asc" ? -1 : 1;
    if (left > right) return sort.dir === "asc" ? 1 : -1;
    return a.label.localeCompare(b.label);
  });
  return sorted;
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
