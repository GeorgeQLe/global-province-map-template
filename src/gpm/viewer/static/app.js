/* global maplibregl */

const state = {
  meta: null,
  qa: null,
  politicsQa: null,
  adjacency: {},
  ownershipById: new Map(),
  featuresById: new Map(),
  selectedId: null,
  colorMode: "country",
  map: null,
  bounds: null,
  authoringEnabled: false,
  scenarioId: null,
};

const REFINEMENT_COLORS = {
  "population-weighted-voronoi": "#5eead4",
  "area-weighted-voronoi": "#60a5fa",
  "source-geometry-preserved": "#fbbf24",
  none: "#94a3b8",
};

const QA_COLORS = {
  error: "#fb7185",
  warning: "#fbbf24",
  ok: "#34d399",
};

const ASSIGNMENT_COLORS = {
  baseline: "#94a3b8",
  country_rule: "#60a5fa",
  region_rule: "#a78bfa",
  province_override: "#fbbf24",
};

const PALETTE = [
  "#5eead4",
  "#60a5fa",
  "#a78bfa",
  "#f472b6",
  "#fbbf24",
  "#34d399",
  "#fb7185",
  "#38bdf8",
  "#c084fc",
  "#f59e0b",
  "#2dd4bf",
  "#818cf8",
];

function $(id) {
  return document.getElementById(id);
}

function setStatus(message, isError = false) {
  const banner = $("status-banner");
  banner.textContent = message;
  banner.classList.toggle("error", isError);
  banner.style.display = message ? "block" : "none";
}

async function fetchJson(url) {
  const response = await fetch(url);
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`${url} failed (${response.status}): ${text}`);
  }
  return response.json();
}

function hashColor(key) {
  let hash = 0;
  const text = String(key || "unknown");
  for (let i = 0; i < text.length; i += 1) {
    hash = (hash * 31 + text.charCodeAt(i)) >>> 0;
  }
  return PALETTE[hash % PALETTE.length];
}

function quantizeColor(value, min, max, low, high) {
  if (value == null || Number.isNaN(value) || max <= min) {
    return "#64748b";
  }
  const t = Math.min(1, Math.max(0, (value - min) / (max - min)));
  return interpolateColor(low, high, t);
}

function interpolateColor(a, b, t) {
  const ca = hexToRgb(a);
  const cb = hexToRgb(b);
  const mix = ca.map((part, index) => Math.round(part + (cb[index] - part) * t));
  return `rgb(${mix[0]}, ${mix[1]}, ${mix[2]})`;
}

function hexToRgb(hex) {
  const normalized = hex.replace("#", "");
  return [
    parseInt(normalized.slice(0, 2), 16),
    parseInt(normalized.slice(2, 4), 16),
    parseInt(normalized.slice(4, 6), 16),
  ];
}

function ownershipFor(feature) {
  const provinceId = feature.properties?.province_id;
  return state.ownershipById.get(provinceId) || null;
}

function provinceFillColor(feature) {
  const props = feature.properties || {};
  const findings = props._qa_findings || [];
  const politicsFindings = props._politics_findings || [];
  const ownership = ownershipFor(feature);

  if (state.colorMode === "qa") {
    if (findings.some((item) => item.severity === "error")) {
      return QA_COLORS.error;
    }
    if (findings.some((item) => item.severity === "warning")) {
      return QA_COLORS.warning;
    }
    return QA_COLORS.ok;
  }
  if (state.colorMode === "politics_qa") {
    if (politicsFindings.some((item) => item.severity === "error")) {
      return QA_COLORS.error;
    }
    if (politicsFindings.some((item) => item.severity === "warning")) {
      return QA_COLORS.warning;
    }
    return ownership ? QA_COLORS.ok : "#64748b";
  }
  if (state.colorMode === "owner") {
    if (!ownership) {
      return "#64748b";
    }
    return ownership.owner_color || hashColor(ownership.owner || props.province_id);
  }
  if (state.colorMode === "controller") {
    if (!ownership) {
      return "#64748b";
    }
    return ownership.controller_color || hashColor(ownership.controller || ownership.owner);
  }
  if (state.colorMode === "culture") {
    if (!ownership) {
      return "#64748b";
    }
    return ownership.culture_color || "#8a8a8a";
  }
  if (state.colorMode === "religion") {
    if (!ownership) {
      return "#64748b";
    }
    return ownership.religion_color || "#8a8a8a";
  }
  if (state.colorMode === "assignment") {
    if (!ownership) {
      return "#64748b";
    }
    return ASSIGNMENT_COLORS[ownership.assignment_source] || "#64748b";
  }
  if (state.colorMode === "country") {
    return hashColor(props.parent_country_id || props.province_id);
  }
  if (state.colorMode === "refinement") {
    return REFINEMENT_COLORS[props.refinement_strategy] || REFINEMENT_COLORS.none;
  }
  if (state.colorMode === "area") {
    return quantizeColor(props.area_sq_km, state.areaMin, state.areaMax, "#0f766e", "#fde68a");
  }
  if (state.colorMode === "population") {
    return quantizeColor(
      props.estimated_population,
      state.popMin,
      state.popMax,
      "#1e3a8a",
      "#f472b6",
    );
  }
  return "#64748b";
}

function applyColors() {
  if (!state.map || !state.map.getSource("provinces")) {
    return;
  }
  const expression = ["match", ["get", "province_id"]];
  for (const [provinceId, feature] of state.featuresById.entries()) {
    expression.push(provinceId, provinceFillColor(feature));
  }
  expression.push("#475569");
  state.map.setPaintProperty("provinces-fill", "fill-color", expression);
  renderLegend();
}

function renderLegend() {
  const root = $("legend-swatches");
  root.innerHTML = "";
  const add = (color, label) => {
    const row = document.createElement("div");
    row.className = "legend-swatch";
    row.innerHTML = `<span class="swatch" style="background:${color}"></span><span>${label}</span>`;
    root.appendChild(row);
  };

  if (state.colorMode === "country") {
    add(PALETTE[0], "Hashed by parent country");
    add(PALETTE[1], "Stable per country id");
  } else if (state.colorMode === "owner" || state.colorMode === "controller") {
    add(PALETTE[0], "Scenario tag color");
    add("#8a8a8a", "UNK");
  } else if (state.colorMode === "culture" || state.colorMode === "religion") {
    add(PALETTE[0], "Identity color");
    add("#8a8a8a", "unassigned");
  } else if (state.colorMode === "assignment") {
    Object.entries(ASSIGNMENT_COLORS).forEach(([key, color]) => add(color, key));
  } else if (state.colorMode === "area") {
    add("#0f766e", "Smaller area");
    add("#fde68a", "Larger area");
  } else if (state.colorMode === "population") {
    add("#1e3a8a", "Lower population");
    add("#f472b6", "Higher population");
  } else if (state.colorMode === "refinement") {
    Object.entries(REFINEMENT_COLORS).forEach(([key, color]) => add(color, key));
  } else if (state.colorMode === "qa" || state.colorMode === "politics_qa") {
    Object.entries(QA_COLORS).forEach(([key, color]) => add(color, key));
  }
}

function formatNumber(value) {
  if (value == null || value === "") {
    return "—";
  }
  if (typeof value === "number") {
    return value.toLocaleString(undefined, { maximumFractionDigits: 3 });
  }
  return String(value);
}

function chips(values) {
  if (!Array.isArray(values) || values.length === 0) {
    return '<span class="empty">—</span>';
  }
  return `<div class="lineage">${values
    .map((value) => `<span class="chip">${escapeHtml(String(value))}</span>`)
    .join("")}</div>`;
}

function escapeHtml(text) {
  return text
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function renderDatasetStats() {
  const meta = state.meta || {};
  const qaBadge =
    meta.qa_status == null
      ? '<span class="badge muted">no report</span>'
      : `<span class="badge ${meta.qa_status}">${escapeHtml(meta.qa_status)}</span>`;
  const politicsBadge =
    meta.politics_qa_status == null
      ? '<span class="badge muted">n/a</span>'
      : `<span class="badge ${meta.politics_qa_status}">${escapeHtml(meta.politics_qa_status)}</span>`;
  $("dataset-stats").innerHTML = `
    <div class="stat"><span class="label">Profile</span><span class="value">${escapeHtml(
      meta.profile_id || "—",
    )}</span></div>
    <div class="stat"><span class="label">Provinces</span><span class="value">${formatNumber(
      meta.province_count,
    )}</span></div>
    <div class="stat"><span class="label">Adjacency</span><span class="value">${formatNumber(
      meta.adjacency_count,
    )}</span></div>
    <div class="stat"><span class="label">Topology QA</span><span class="value">${qaBadge}</span></div>
    <div class="stat"><span class="label">Scenario</span><span class="value">${escapeHtml(
      meta.scenario_id || "—",
    )}</span></div>
    <div class="stat"><span class="label">Politics QA</span><span class="value">${politicsBadge}</span></div>
  `;
  const gpm = meta.gpm || {};
  $("subtitle").textContent = [
    meta.profile_id,
    meta.scenario_id,
    gpm.id_scheme,
    meta.province_input ? meta.province_input.split(/[\\/]/).pop() : null,
  ]
    .filter(Boolean)
    .join(" · ");
}

function renderScenarioSummary() {
  const panel = $("scenario-summary");
  if (!state.scenarioId) {
    panel.innerHTML =
      'No scenario loaded. Start with <code>gpm review --scenario &lt;id&gt;</code>.';
    return;
  }
  const meta = state.meta || {};
  panel.innerHTML = `
    <div>Active: <strong>${escapeHtml(state.scenarioId)}</strong></div>
    <div class="help" style="margin-top:0.35rem">
      Ownership rows: ${formatNumber(meta.ownership_row_count)} ·
      authoring ${meta.authoring_enabled ? "enabled" : "disabled"}
    </div>
    <div class="help" style="margin-top:0.35rem">
      Color by Owner / Controller / Assignment to review politics layers.
    </div>
  `;
}

function renderQaPanel() {
  const summary = $("qa-summary");
  const list = $("finding-list");
  list.innerHTML = "";
  if (!state.qa || !state.qa.available || !state.qa.report) {
    summary.innerHTML =
      '<span class="empty">No topology QA report was found. Run <code>gpm qa topology</code>.</span>';
    return;
  }
  const report = state.qa.report;
  const findings = Array.isArray(report.findings) ? report.findings : [];
  summary.innerHTML = `
    <div>Status: <span class="badge ${report.status}">${escapeHtml(report.status || "unknown")}</span></div>
    <div class="help" style="margin-top:0.4rem">
      ${formatNumber(findings.length)} findings ·
      coverage ${escapeHtml(report.summary?.analysis?.coverage || "—")} ·
      graph ${escapeHtml(report.summary?.analysis?.graph || "—")}
    </div>
  `;
  if (findings.length === 0) {
    list.innerHTML = '<div class="empty">No findings.</div>';
    return;
  }
  findings.forEach((finding, index) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "finding-item";
    button.innerHTML = `
      <div class="code">${escapeHtml(finding.code || "FINDING")} · ${escapeHtml(
        finding.severity || "info",
      )}</div>
      <div class="message">${escapeHtml(finding.message || "")}</div>
      <div class="message">ids: ${(finding.affected_ids || []).slice(0, 4).map(escapeHtml).join(", ") || "—"}</div>
    `;
    button.addEventListener("click", () => focusFinding(finding, button));
    button.dataset.index = String(index);
    list.appendChild(button);
  });
}

function renderPoliticsQaPanel() {
  const summary = $("politics-qa-summary");
  const list = $("politics-finding-list");
  list.innerHTML = "";
  if (!state.scenarioId) {
    summary.innerHTML = '<span class="empty">Load a scenario to run politics QA.</span>';
    return;
  }
  if (!state.politicsQa || !state.politicsQa.available || !state.politicsQa.report) {
    summary.innerHTML =
      '<span class="empty">No politics QA report. Run <code>gpm qa scenario --scenario …</code>.</span>';
    return;
  }
  const report = state.politicsQa.report;
  const findings = Array.isArray(report.findings) ? report.findings : [];
  summary.innerHTML = `
    <div>Status: <span class="badge ${report.status}">${escapeHtml(report.status || "unknown")}</span></div>
    <div class="help" style="margin-top:0.4rem">
      ${formatNumber(findings.length)} findings ·
      adjacency ${escapeHtml(report.summary?.analysis?.adjacency || "—")} ·
      golden ${escapeHtml(report.summary?.analysis?.golden || "—")}
    </div>
  `;
  if (findings.length === 0) {
    list.innerHTML = '<div class="empty">No findings.</div>';
    return;
  }
  findings.forEach((finding, index) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "finding-item";
    button.innerHTML = `
      <div class="code">${escapeHtml(finding.code || "FINDING")} · ${escapeHtml(
        finding.severity || "info",
      )}</div>
      <div class="message">${escapeHtml(finding.message || "")}</div>
      <div class="message">ids: ${(finding.affected_ids || []).slice(0, 4).map(escapeHtml).join(", ") || "—"}</div>
    `;
    button.addEventListener("click", () => focusFinding(finding, button));
    button.dataset.index = String(index);
    list.appendChild(button);
  });
}

function focusFinding(finding, button) {
  document.querySelectorAll(".finding-item").forEach((node) => node.classList.remove("active"));
  if (button) {
    button.classList.add("active");
  }
  const ids = (finding.affected_ids || []).filter((id) => state.featuresById.has(id));
  if (ids.length === 0) {
    setStatus(`Finding has no mappable province ids: ${finding.code || "unknown"}`);
    return;
  }
  const bounds = new maplibregl.LngLatBounds();
  ids.forEach((id) => {
    const feature = state.featuresById.get(id);
    expandBounds(bounds, feature.geometry);
  });
  if (!bounds.isEmpty()) {
    state.map.fitBounds(bounds, { padding: 64, maxZoom: 7, duration: 700 });
  }
  selectProvince(ids[0], { fly: false });
}

function expandBounds(bounds, geometry) {
  if (!geometry) {
    return;
  }
  const walk = (coords) => {
    if (typeof coords[0] === "number") {
      bounds.extend(coords);
      return;
    }
    coords.forEach(walk);
  };
  walk(geometry.coordinates);
}

function selectProvince(provinceId, { fly = true } = {}) {
  state.selectedId = provinceId;
  const feature = state.featuresById.get(provinceId);
  if (!feature) {
    setStatus(`Unknown province: ${provinceId}`, true);
    return;
  }
  if (state.map.getLayer("provinces-selected")) {
    state.map.setFilter("provinces-selected", ["==", ["get", "province_id"], provinceId]);
  }
  renderInspector(feature);
  renderOwnership(provinceId);
  renderAuthoring(provinceId);
  renderAdjacency(provinceId);
  renderProvinceFindings(provinceId);
  if (fly) {
    const bounds = new maplibregl.LngLatBounds();
    expandBounds(bounds, feature.geometry);
    if (!bounds.isEmpty()) {
      state.map.fitBounds(bounds, { padding: 80, maxZoom: 8, duration: 650 });
    }
  }
  setStatus(`Selected ${provinceId}`);
}

function clearSelection() {
  state.selectedId = null;
  if (state.map && state.map.getLayer("provinces-selected")) {
    state.map.setFilter("provinces-selected", ["==", ["get", "province_id"], ""]);
  }
  $("inspector").innerHTML = '<div class="empty">Select a province on the map.</div>';
  $("ownership-panel").innerHTML = state.scenarioId
    ? '<div class="empty">Select a province to inspect ownership.</div>'
    : '<div class="empty">No scenario loaded.</div>';
  $("authoring-panel").innerHTML = state.authoringEnabled
    ? '<div class="empty">Select a province to edit overrides.</div>'
    : '<div class="empty">Load a scenario to author province overrides.</div>';
  $("adjacency-list").innerHTML = '<div class="empty">No province selected.</div>';
  $("province-findings").innerHTML = '<div class="empty">No province selected.</div>';
  $("search").value = "";
  setStatus("Selection cleared");
}

function renderInspector(feature) {
  const props = feature.properties || {};
  const rows = [
    ["province_id", props.province_id],
    ["display_name", props.display_name],
    ["kind", props.kind],
    ["parent_region_id", props.parent_region_id],
    ["parent_country_id", props.parent_country_id],
    ["area_sq_km", formatNumber(props.area_sq_km)],
    ["estimated_population", formatNumber(props.estimated_population)],
    ["population_estimation_method", props.population_estimation_method],
    ["terrain_class", props.terrain_class],
    ["coastal", props.coastal],
    ["island", props.island],
    ["settlement_count", formatNumber(props.settlement_count)],
    ["refinement_parent_id", props.refinement_parent_id],
    ["refinement_strategy", props.refinement_strategy],
    ["refinement_part_index", props.refinement_part_index],
    ["refinement_part_count", props.refinement_part_count],
    ["refinement_skipped_reason", props.refinement_skipped_reason],
    ["source_layer", props.source_layer],
  ];
  $("inspector").innerHTML = `
    <div class="kv-list">
      ${rows
        .map(
          ([key, value]) => `
        <div class="row">
          <div class="key">${escapeHtml(key)}</div>
          <div class="value">${escapeHtml(value == null || value === "" ? "—" : String(value))}</div>
        </div>`,
        )
        .join("")}
      <div class="row">
        <div class="key">source_lineage</div>
        <div class="value">${chips(props.source_lineage)}</div>
      </div>
      <div class="row">
        <div class="key">license_lineage</div>
        <div class="value">${chips(props.license_lineage)}</div>
      </div>
    </div>
  `;
}

function renderOwnership(provinceId) {
  const panel = $("ownership-panel");
  if (!state.scenarioId) {
    panel.innerHTML = '<div class="empty">No scenario loaded.</div>';
    return;
  }
  const ownership = state.ownershipById.get(provinceId);
  if (!ownership) {
    panel.innerHTML = '<div class="empty">No ownership row for this province.</div>';
    return;
  }
  const ownerColor = ownership.owner_color || "#64748b";
  const controllerColor = ownership.controller_color || "#64748b";
  panel.innerHTML = `
    <div class="kv-list">
      <div class="row"><div class="key">scenario</div><div class="value">${escapeHtml(
        ownership.scenario_id || state.scenarioId,
      )}</div></div>
      <div class="row"><div class="key">owner</div><div class="value"><span class="color-chip" style="background:${escapeHtml(
        ownerColor,
      )}"></span>${escapeHtml(ownership.owner || "—")}</div></div>
      <div class="row"><div class="key">controller</div><div class="value"><span class="color-chip" style="background:${escapeHtml(
        controllerColor,
      )}"></span>${escapeHtml(ownership.controller || "—")}</div></div>
      <div class="row"><div class="key">cores</div><div class="value">${chips(ownership.cores)}</div></div>
      <div class="row"><div class="key">claims</div><div class="value">${chips(ownership.claims)}</div></div>
      <div class="row"><div class="key">culture</div><div class="value">${escapeHtml(
        ownership.culture || "—",
      )}</div></div>
      <div class="row"><div class="key">religion</div><div class="value">${escapeHtml(
        ownership.religion || "—",
      )}</div></div>
      <div class="row"><div class="key">disputed</div><div class="value">${escapeHtml(
        String(Boolean(ownership.disputed)),
      )}</div></div>
      <div class="row"><div class="key">assignment</div><div class="value">${escapeHtml(
        ownership.assignment_source || "—",
      )}</div></div>
      <div class="row"><div class="key">notes</div><div class="value">${escapeHtml(
        ownership.notes || "—",
      )}</div></div>
    </div>
  `;
}

function renderAuthoring(provinceId) {
  const panel = $("authoring-panel");
  if (!state.authoringEnabled) {
    panel.innerHTML = state.scenarioId
      ? '<div class="empty">Authoring disabled for this session.</div>'
      : '<div class="empty">Load a scenario to author province overrides.</div>';
    return;
  }
  const ownership = state.ownershipById.get(provinceId) || {};
  panel.innerHTML = `
    <form class="authoring-form" id="authoring-form">
      <label>owner
        <input name="owner" type="text" value="${escapeHtml(ownership.owner || "")}" required />
      </label>
      <label>controller
        <input name="controller" type="text" value="${escapeHtml(ownership.controller || "")}" />
      </label>
      <label>cores (comma-separated)
        <input name="cores" type="text" value="${escapeHtml((ownership.cores || []).join(", "))}" />
      </label>
      <label>claims (comma-separated)
        <input name="claims" type="text" value="${escapeHtml((ownership.claims || []).join(", "))}" />
      </label>
      <label>culture
        <input name="culture" type="text" value="${escapeHtml(ownership.culture || "")}" />
      </label>
      <label>religion
        <input name="religion" type="text" value="${escapeHtml(ownership.religion || "")}" />
      </label>
      <label class="row-inline">
        <input name="disputed" type="checkbox" ${ownership.disputed ? "checked" : ""} />
        disputed
      </label>
      <label>notes
        <textarea name="notes">${escapeHtml(ownership.notes || "")}</textarea>
      </label>
      <div class="authoring-actions">
        <button type="submit">Save override</button>
        <button type="button" class="danger" id="clear-override">Remove override</button>
      </div>
      <div class="help" id="authoring-status">Writes province_overrides into the scenario JSON.</div>
    </form>
  `;
  $("authoring-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    await saveOverride(provinceId, new FormData(event.target));
  });
  $("clear-override").addEventListener("click", async () => {
    await deleteOverride(provinceId);
  });
}

async function saveOverride(provinceId, formData) {
  const status = $("authoring-status");
  status.textContent = "Saving…";
  const payload = {
    province_id: provinceId,
    owner: String(formData.get("owner") || "").trim(),
    controller: String(formData.get("controller") || "").trim() || undefined,
    cores: String(formData.get("cores") || ""),
    claims: String(formData.get("claims") || ""),
    culture: String(formData.get("culture") || "").trim() || undefined,
    religion: String(formData.get("religion") || "").trim() || undefined,
    disputed: formData.get("disputed") === "on",
    notes: String(formData.get("notes") || "").trim() || undefined,
  };
  try {
    const response = await fetch("/api/scenario/override", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const body = await response.json();
    if (!response.ok) {
      throw new Error(body.error || `Save failed (${response.status})`);
    }
    await refreshOwnershipState();
    selectProvince(provinceId, { fly: false });
    applyColors();
    status.textContent = `Saved (${body.result?.action || "updated"}). Politics QA: ${
      body.politics_qa_status || "—"
    }.`;
    setStatus(`Override ${body.result?.action || "saved"} for ${provinceId}`);
  } catch (error) {
    status.textContent = error.message || String(error);
    setStatus(error.message || String(error), true);
  }
}

async function deleteOverride(provinceId) {
  const status = $("authoring-status");
  status.textContent = "Removing override…";
  try {
    const response = await fetch("/api/scenario/override", {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ province_id: provinceId }),
    });
    const body = await response.json();
    if (!response.ok) {
      throw new Error(body.error || `Delete failed (${response.status})`);
    }
    await refreshOwnershipState();
    selectProvince(provinceId, { fly: false });
    applyColors();
    status.textContent = `Removed override (${body.result?.action || "removed"}).`;
    setStatus(`Override removed for ${provinceId}`);
  } catch (error) {
    status.textContent = error.message || String(error);
    setStatus(error.message || String(error), true);
  }
}

async function refreshOwnershipState() {
  const [ownershipPayload, politicsPayload, meta] = await Promise.all([
    fetchJson("/api/ownership.json"),
    fetchJson("/api/politics-qa.json"),
    fetchJson("/api/meta"),
  ]);
  state.meta = meta;
  state.politicsQa = politicsPayload;
  state.ownershipById = new Map();
  (ownershipPayload.records || []).forEach((row) => {
    state.ownershipById.set(row.province_id, row);
  });
  attachOwnershipToFeatures();
  renderDatasetStats();
  renderScenarioSummary();
  renderPoliticsQaPanel();
}

function renderAdjacency(provinceId) {
  const neighbors = state.adjacency[provinceId] || [];
  if (neighbors.length === 0) {
    $("adjacency-list").innerHTML = '<div class="empty">No adjacency rows for this province.</div>';
    return;
  }
  const root = document.createElement("div");
  root.className = "neighbor-list";
  neighbors.forEach((edge) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "neighbor-item";
    const neighbor = state.featuresById.get(edge.neighbor_id);
    const name = neighbor?.properties?.display_name || edge.neighbor_id;
    button.innerHTML = `
      <div><strong>${escapeHtml(name)}</strong></div>
      <div class="meta">${escapeHtml(edge.neighbor_id)}</div>
      <div class="meta">${escapeHtml(edge.adjacency_type || "land")} · ${formatNumber(
        edge.shared_border_km,
      )} km · ${escapeHtml(edge.crossing_type || "shared_border")}</div>
    `;
    button.addEventListener("click", () => selectProvince(edge.neighbor_id));
    root.appendChild(button);
  });
  $("adjacency-list").innerHTML = "";
  $("adjacency-list").appendChild(root);
}

function renderProvinceFindings(provinceId) {
  const feature = state.featuresById.get(provinceId);
  const topology = feature?.properties?._qa_findings || [];
  const politics = feature?.properties?._politics_findings || [];
  if (topology.length === 0 && politics.length === 0) {
    $("province-findings").innerHTML = '<div class="empty">No QA findings reference this province.</div>';
    return;
  }
  const renderGroup = (title, findings) => {
    if (!findings.length) {
      return "";
    }
    return `
      <div class="help" style="margin:0.35rem 0">${escapeHtml(title)}</div>
      ${findings
        .map(
          (finding) => `
        <div class="finding-item">
          <div class="code">${escapeHtml(finding.code || "FINDING")} · ${escapeHtml(
            finding.severity || "info",
          )}</div>
          <div class="message">${escapeHtml(finding.message || "")}</div>
        </div>`,
        )
        .join("")}
    `;
  };
  $("province-findings").innerHTML =
    renderGroup("Topology", topology) + renderGroup("Politics", politics);
}

function createMapStyle(showBasemap) {
  const style = {
    version: 8,
    glyphs: "https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf",
    sources: {},
    layers: [
      {
        id: "background",
        type: "background",
        paint: { "background-color": "#07111f" },
      },
    ],
  };
  if (showBasemap) {
    style.sources.basemap = {
      type: "raster",
      tiles: [
        "https://a.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}.png",
        "https://b.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}.png",
        "https://c.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}.png",
      ],
      tileSize: 256,
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>',
    };
    style.layers.push({
      id: "basemap",
      type: "raster",
      source: "basemap",
      paint: { "raster-opacity": 0.55 },
    });
  }
  return style;
}

function computeNumericExtents(features) {
  let areaMin = Infinity;
  let areaMax = -Infinity;
  let popMin = Infinity;
  let popMax = -Infinity;
  features.forEach((feature) => {
    const area = Number(feature.properties?.area_sq_km);
    if (!Number.isNaN(area)) {
      areaMin = Math.min(areaMin, area);
      areaMax = Math.max(areaMax, area);
    }
    const population = Number(feature.properties?.estimated_population);
    if (!Number.isNaN(population) && population != null) {
      popMin = Math.min(popMin, population);
      popMax = Math.max(popMax, population);
    }
  });
  state.areaMin = Number.isFinite(areaMin) ? areaMin : 0;
  state.areaMax = Number.isFinite(areaMax) ? areaMax : 1;
  state.popMin = Number.isFinite(popMin) ? popMin : 0;
  state.popMax = Number.isFinite(popMax) ? popMax : 1;
}

function attachQaToFeatures(collection) {
  const findings = state.qa?.report?.findings || [];
  const byId = new Map();
  findings.forEach((finding) => {
    (finding.affected_ids || []).forEach((id) => {
      if (!byId.has(id)) {
        byId.set(id, []);
      }
      byId.get(id).push({
        code: finding.code,
        severity: finding.severity,
        message: finding.message,
      });
    });
  });
  collection.features.forEach((feature) => {
    const provinceId = feature.properties?.province_id;
    feature.properties = feature.properties || {};
    feature.properties._qa_findings = byId.get(provinceId) || [];
    feature.properties._qa_severity = feature.properties._qa_findings.some(
      (item) => item.severity === "error",
    )
      ? "error"
      : feature.properties._qa_findings.some((item) => item.severity === "warning")
        ? "warning"
        : "ok";
    state.featuresById.set(provinceId, feature);
  });
  attachOwnershipToFeatures();
}

function attachOwnershipToFeatures() {
  const politicsFindings = state.politicsQa?.report?.findings || [];
  const politicsById = new Map();
  politicsFindings.forEach((finding) => {
    (finding.affected_ids || []).forEach((id) => {
      if (!politicsById.has(id)) {
        politicsById.set(id, []);
      }
      politicsById.get(id).push({
        code: finding.code,
        severity: finding.severity,
        message: finding.message,
      });
    });
  });

  for (const [provinceId, feature] of state.featuresById.entries()) {
    feature.properties = feature.properties || {};
    const ownership = state.ownershipById.get(provinceId);
    feature.properties._politics_findings = politicsById.get(provinceId) || [];
    feature.properties._politics_severity = feature.properties._politics_findings.some(
      (item) => item.severity === "error",
    )
      ? "error"
      : feature.properties._politics_findings.some((item) => item.severity === "warning")
        ? "warning"
        : "ok";
    if (ownership) {
      feature.properties.owner = ownership.owner;
      feature.properties.controller = ownership.controller;
      feature.properties.assignment_source = ownership.assignment_source;
      feature.properties.owner_color = ownership.owner_color;
      feature.properties.controller_color = ownership.controller_color;
      feature.properties.culture = ownership.culture;
      feature.properties.religion = ownership.religion;
      feature.properties.culture_color = ownership.culture_color;
      feature.properties.religion_color = ownership.religion_color;
      feature.properties.disputed = ownership.disputed;
    }
  }

  if (state.map && state.map.getSource("provinces")) {
    const features = Array.from(state.featuresById.values());
    state.map.getSource("provinces").setData({
      type: "FeatureCollection",
      features,
    });
  }
}

function buildBounds(collection) {
  const bounds = new maplibregl.LngLatBounds();
  collection.features.forEach((feature) => expandBounds(bounds, feature.geometry));
  return bounds;
}

function searchProvinces(query) {
  const needle = query.trim().toLowerCase();
  if (!needle) {
    return;
  }
  for (const [provinceId, feature] of state.featuresById.entries()) {
    const name = String(feature.properties?.display_name || "").toLowerCase();
    const owner = String(state.ownershipById.get(provinceId)?.owner || "").toLowerCase();
    if (
      provinceId.toLowerCase().includes(needle) ||
      name.includes(needle) ||
      owner.includes(needle)
    ) {
      selectProvince(provinceId);
      return;
    }
  }
  setStatus(`No province matched “${query}”`, true);
}

function wireControls() {
  $("color-mode").addEventListener("change", (event) => {
    state.colorMode = event.target.value;
    applyColors();
  });
  $("toggle-basemap").addEventListener("change", (event) => {
    const checked = event.target.checked;
    if (!state.map.getSource("basemap") && checked) {
      state.map.addSource("basemap", createMapStyle(true).sources.basemap);
      state.map.addLayer(
        {
          id: "basemap",
          type: "raster",
          source: "basemap",
          paint: { "raster-opacity": 0.55 },
        },
        "provinces-fill",
      );
    }
    if (state.map.getLayer("basemap")) {
      state.map.setLayoutProperty("basemap", "visibility", checked ? "visible" : "none");
    }
  });
  $("toggle-qa-overlay").addEventListener("change", (event) => {
    const visibility = event.target.checked ? "visible" : "none";
    if (state.map.getLayer("qa-errors")) {
      state.map.setLayoutProperty("qa-errors", "visibility", visibility);
    }
    if (state.map.getLayer("qa-warnings")) {
      state.map.setLayoutProperty("qa-warnings", "visibility", visibility);
    }
  });
  $("toggle-politics-overlay").addEventListener("change", (event) => {
    const visibility = event.target.checked ? "visible" : "none";
    if (state.map.getLayer("politics-errors")) {
      state.map.setLayoutProperty("politics-errors", "visibility", visibility);
    }
    if (state.map.getLayer("politics-warnings")) {
      state.map.setLayoutProperty("politics-warnings", "visibility", visibility);
    }
  });
  $("search").addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      searchProvinces(event.target.value);
    }
  });
  $("clear-selection").addEventListener("click", clearSelection);
}

async function main() {
  try {
    setStatus("Loading metadata…");
    state.meta = await fetchJson("/api/meta");
    state.scenarioId = state.meta.scenario_id || null;
    state.authoringEnabled = Boolean(state.meta.authoring_enabled);
    const SCENARIO_COLOR_MODES = [
      "owner",
      "controller",
      "assignment",
      "culture",
      "religion",
    ];
    if (state.scenarioId && !SCENARIO_COLOR_MODES.includes(state.colorMode)) {
      state.colorMode = "owner";
      $("color-mode").value = "owner";
    }
    renderDatasetStats();
    renderScenarioSummary();

    setStatus("Loading adjacency, QA, and scenario…");
    const [adjacencyPayload, qaPayload, ownershipPayload, politicsPayload] = await Promise.all([
      fetchJson("/api/adjacency.json"),
      fetchJson("/api/qa.json"),
      fetchJson("/api/ownership.json"),
      fetchJson("/api/politics-qa.json"),
    ]);
    state.adjacency = adjacencyPayload.adjacency || {};
    state.qa = qaPayload;
    state.politicsQa = politicsPayload;
    state.ownershipById = new Map();
    (ownershipPayload.records || []).forEach((row) => {
      state.ownershipById.set(row.province_id, row);
    });
    renderQaPanel();
    renderPoliticsQaPanel();

    setStatus("Loading province geometries…");
    const collection = await fetchJson("/api/provinces.geojson");
    attachQaToFeatures(collection);
    computeNumericExtents(collection.features);
    state.bounds = buildBounds(collection);

    state.map = new maplibregl.Map({
      container: "map",
      style: createMapStyle($("toggle-basemap").checked),
      center: [10, 20],
      zoom: 1.4,
      attributionControl: true,
    });
    state.map.addControl(new maplibregl.NavigationControl({ visualizePitch: false }), "top-right");

    state.map.on("load", () => {
      state.map.addSource("provinces", {
        type: "geojson",
        data: collection,
      });
      state.map.addLayer({
        id: "provinces-fill",
        type: "fill",
        source: "provinces",
        paint: {
          "fill-color": "#475569",
          "fill-opacity": 0.72,
        },
      });
      state.map.addLayer({
        id: "provinces-outline",
        type: "line",
        source: "provinces",
        paint: {
          "line-color": "rgba(226, 232, 240, 0.55)",
          "line-width": 0.4,
        },
      });
      state.map.addLayer({
        id: "qa-warnings",
        type: "line",
        source: "provinces",
        filter: ["==", ["get", "_qa_severity"], "warning"],
        paint: {
          "line-color": QA_COLORS.warning,
          "line-width": 1.8,
        },
      });
      state.map.addLayer({
        id: "qa-errors",
        type: "line",
        source: "provinces",
        filter: ["==", ["get", "_qa_severity"], "error"],
        paint: {
          "line-color": QA_COLORS.error,
          "line-width": 2.4,
        },
      });
      state.map.addLayer({
        id: "politics-warnings",
        type: "line",
        source: "provinces",
        filter: ["==", ["get", "_politics_severity"], "warning"],
        paint: {
          "line-color": "#f59e0b",
          "line-width": 1.6,
          "line-dasharray": [1.5, 1.2],
        },
      });
      state.map.addLayer({
        id: "politics-errors",
        type: "line",
        source: "provinces",
        filter: ["==", ["get", "_politics_severity"], "error"],
        paint: {
          "line-color": "#fb7185",
          "line-width": 2.2,
          "line-dasharray": [2, 1],
        },
      });
      state.map.addLayer({
        id: "provinces-selected",
        type: "line",
        source: "provinces",
        filter: ["==", ["get", "province_id"], ""],
        paint: {
          "line-color": "#5eead4",
          "line-width": 2.8,
        },
      });

      applyColors();
      if (state.bounds && !state.bounds.isEmpty()) {
        state.map.fitBounds(state.bounds, { padding: 28, duration: 0 });
      }
      const ownershipNote = state.scenarioId
        ? ` · scenario ${state.scenarioId} (${state.ownershipById.size} ownership rows)`
        : "";
      setStatus(
        `Loaded ${state.meta.province_count} provinces · ${state.meta.adjacency_count} adjacency rows${ownershipNote}`,
      );
      setTimeout(() => setStatus(""), 2500);
    });

    state.map.on("click", "provinces-fill", (event) => {
      const feature = event.features && event.features[0];
      if (!feature) {
        return;
      }
      selectProvince(feature.properties.province_id, { fly: false });
    });
    state.map.on("mouseenter", "provinces-fill", () => {
      state.map.getCanvas().style.cursor = "pointer";
    });
    state.map.on("mouseleave", "provinces-fill", () => {
      state.map.getCanvas().style.cursor = "";
    });

    wireControls();
  } catch (error) {
    console.error(error);
    setStatus(error.message || String(error), true);
  }
}

main();
