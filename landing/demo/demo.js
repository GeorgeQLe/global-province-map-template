/* global maplibregl, pmtiles */

(() => {
  // Root-absolute: page is served at /demo (no trailing slash) under Vercel cleanUrls.
  const DATA_BASE = "/demo/data";

  const ASSIGNMENT_COLORS = {
    baseline: "#94a3b8",
    country_rule: "#60a5fa",
    region_rule: "#a78bfa",
    province_override: "#fbbf24",
  };

  const EDGE_COLORS = {
    land: "#e8a54b",
    sea: "#5eead4",
    port_to_sea: "#38bdf8",
    strait: "#f472b6",
  };

  // Vic2/EU-style nesting: thin area seams < region borders < superregion borders.
  const HIERARCHY_LINE_STYLE = {
    area: { color: "rgba(240, 234, 214, 0.35)", width: 0.6 },
    region: { color: "rgba(240, 234, 214, 0.7)", width: 1.6 },
    superregion: { color: "rgba(255, 246, 218, 0.9)", width: 2.8 },
  };

  const MAX_LEGEND_ROWS = 40;

  const state = {
    manifest: null,
    scenarioId: "modern-baseline",
    cache: new Map(),
    map: null,
    selectedId: null,
    paintMode: "ownership",
    periodGeometry: false,
    boundaryHints: true,
    usePmtiles: false,
    pmtilesProtocolReady: false,
    hierarchy: { areas: null, regions: null, superregions: null },
    hierarchyNames: new Map(),
    adjacencyLines: null,
  };

  function ensurePmtilesProtocol() {
    if (state.pmtilesProtocolReady) return true;
    if (typeof pmtiles === "undefined" || !pmtiles.Protocol) return false;
    const protocol = new pmtiles.Protocol();
    maplibregl.addProtocol("pmtiles", protocol.tile);
    state.pmtilesProtocolReady = true;
    return true;
  }

  const $ = (id) => document.getElementById(id);

  function setStatus(message, isError = false) {
    const banner = $("status-banner");
    if (!banner) return;
    if (!message) {
      banner.hidden = true;
      banner.textContent = "";
      return;
    }
    banner.hidden = false;
    banner.textContent = message;
    banner.classList.toggle("error", isError);
  }

  async function fetchJson(url, options = undefined) {
    const response = await fetch(url, options);
    if (!response.ok) {
      throw new Error(`${url} failed (${response.status})`);
    }
    return response.json();
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  }

  // Vector-tile values are scalar: list properties (cores, claims) arrive as
  // comma-joined strings, while the period GeoJSON path still yields arrays.
  function splitList(value) {
    if (Array.isArray(value)) return value;
    if (value == null || value === "") return [];
    return String(value)
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean);
  }

  function formatList(value) {
    const items = splitList(value);
    return items.length ? items.join(", ") : "—";
  }

  function scenarioMeta(id) {
    return (state.manifest?.scenarios || []).find((s) => s.id === id) || null;
  }

  function centroidOf(feature) {
    const geom = feature.geometry;
    if (!geom) return null;
    let rings = [];
    if (geom.type === "Polygon") {
      rings = [geom.coordinates[0] || []];
    } else if (geom.type === "MultiPolygon") {
      rings = (geom.coordinates || []).map((poly) => poly[0] || []);
    } else {
      return null;
    }
    let x = 0;
    let y = 0;
    let n = 0;
    rings.forEach((ring) => {
      ring.forEach(([lng, lat]) => {
        x += lng;
        y += lat;
        n += 1;
      });
    });
    if (!n) return null;
    return [x / n, y / n];
  }

  function labelPointCollection(collection) {
    const features = (collection?.features || [])
      .filter((feature) => Array.isArray(feature.properties?.label_point))
      .map((feature) => ({
        type: "Feature",
        properties: {
          region_id: feature.properties.region_id,
          display_name: feature.properties.display_name,
        },
        geometry: {
          type: "Point",
          coordinates: feature.properties.label_point,
        },
      }));
    return { type: "FeatureCollection", features };
  }

  function createMapStyle() {
    return {
      version: 8,
      glyphs: "https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf",
      sources: {
        basemap: {
          type: "raster",
          tiles: [
            "https://a.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}.png",
            "https://b.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}.png",
            "https://c.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}.png",
          ],
          tileSize: 256,
          attribution:
            '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>',
        },
      },
      layers: [
        {
          id: "background",
          type: "background",
          paint: { "background-color": "#071018" },
        },
        {
          id: "basemap",
          type: "raster",
          source: "basemap",
          paint: { "raster-opacity": 0.5 },
        },
      ],
    };
  }

  function ownershipFillExpression() {
    return ["coalesce", ["get", "owner_color"], "#b0b0b0"];
  }

  function cultureFillExpression() {
    return ["coalesce", ["get", "culture_color"], "#8a8a8a"];
  }

  function religionFillExpression() {
    return ["coalesce", ["get", "religion_color"], "#8a8a8a"];
  }

  function hierarchyFillExpression() {
    return ["coalesce", ["get", "area_color"], "#4b5c66"];
  }

  function assignmentFillExpression() {
    return [
      "match",
      ["get", "assignment_source"],
      "baseline",
      ASSIGNMENT_COLORS.baseline,
      "country_rule",
      ASSIGNMENT_COLORS.country_rule,
      "region_rule",
      ASSIGNMENT_COLORS.region_rule,
      "province_override",
      ASSIGNMENT_COLORS.province_override,
      "#64748b",
    ];
  }

  const TEXT_STYLE = {
    "text-color": "#f5f0e4",
    "text-halo-color": "rgba(7, 16, 24, 0.9)",
    "text-halo-width": 1.2,
  };

  // Static overlay sources/layers (created once). Province polygon layers are
  // recreated whenever the source mode (PMTiles global / period GeoJSON) flips.
  function ensureStaticLayers() {
    const map = state.map;
    if (map.getSource("hierarchy-areas")) return;

    const empty = { type: "FeatureCollection", features: [] };
    map.addSource("hierarchy-areas", { type: "geojson", data: state.hierarchy.areas || empty });
    map.addSource("hierarchy-regions", { type: "geojson", data: state.hierarchy.regions || empty });
    map.addSource("hierarchy-superregions", {
      type: "geojson",
      data: state.hierarchy.superregions || empty,
    });
    map.addSource("hierarchy-region-labels", {
      type: "geojson",
      data: labelPointCollection(state.hierarchy.regions),
    });
    map.addSource("hierarchy-superregion-labels", {
      type: "geojson",
      data: labelPointCollection(state.hierarchy.superregions),
    });
    map.addSource("boundary-hints", { type: "geojson", data: empty });
    map.addSource("adjacency-lines", {
      type: "geojson",
      data: state.adjacencyLines || empty,
    });

    map.addLayer({
      id: "hierarchy-area-lines",
      type: "line",
      source: "hierarchy-areas",
      paint: {
        "line-color": HIERARCHY_LINE_STYLE.area.color,
        "line-width": HIERARCHY_LINE_STYLE.area.width,
      },
      minzoom: 2.5,
    });
    map.addLayer({
      id: "hierarchy-region-lines",
      type: "line",
      source: "hierarchy-regions",
      paint: {
        "line-color": HIERARCHY_LINE_STYLE.region.color,
        "line-width": HIERARCHY_LINE_STYLE.region.width,
      },
    });
    map.addLayer({
      id: "hierarchy-superregion-lines",
      type: "line",
      source: "hierarchy-superregions",
      paint: {
        "line-color": HIERARCHY_LINE_STYLE.superregion.color,
        "line-width": HIERARCHY_LINE_STYLE.superregion.width,
      },
    });
    map.addLayer({
      id: "boundary-hints-fill",
      type: "fill",
      source: "boundary-hints",
      filter: ["==", ["geometry-type"], "Polygon"],
      paint: {
        "fill-color": "#f59e0b",
        "fill-opacity": 0.12,
      },
    });
    map.addLayer({
      id: "boundary-hints-line",
      type: "line",
      source: "boundary-hints",
      paint: {
        "line-color": "#f59e0b",
        "line-width": 2.4,
        "line-dasharray": [1.6, 1.2],
        "line-opacity": 0.95,
      },
    });
    map.addLayer({
      id: "adjacency-lines",
      type: "line",
      source: "adjacency-lines",
      minzoom: 4,
      paint: {
        "line-color": [
          "match",
          ["get", "type"],
          "land",
          EDGE_COLORS.land,
          "sea",
          EDGE_COLORS.sea,
          "port_to_sea",
          EDGE_COLORS.port_to_sea,
          "strait",
          EDGE_COLORS.strait,
          "#94a3b8",
        ],
        "line-width": 1.4,
        "line-opacity": 0.75,
      },
    });
    map.addLayer({
      id: "region-labels",
      type: "symbol",
      source: "hierarchy-region-labels",
      minzoom: 2.5,
      maxzoom: 6,
      layout: {
        "text-field": ["get", "display_name"],
        "text-size": 12,
        "text-font": ["Noto Sans Regular"],
        "text-max-width": 8,
        "text-transform": "uppercase",
        "text-letter-spacing": 0.08,
      },
      paint: { ...TEXT_STYLE, "text-opacity": 0.85 },
    });
    map.addLayer({
      id: "superregion-labels",
      type: "symbol",
      source: "hierarchy-superregion-labels",
      maxzoom: 3,
      layout: {
        "text-field": ["get", "display_name"],
        "text-size": 16,
        "text-font": ["Noto Sans Regular"],
        "text-max-width": 10,
        "text-transform": "uppercase",
        "text-letter-spacing": 0.2,
      },
      paint: { ...TEXT_STYLE, "text-opacity": 0.7 },
    });
  }

  function pmtilesUrlFor(meta) {
    if (!meta?.pmtiles) return null;
    // Absolute URL so range requests resolve under /demo cleanUrls hosting.
    const origin = window.location.origin || "";
    return `pmtiles://${origin}${DATA_BASE}/${meta.pmtiles}`;
  }

  // Swap the province polygon source. Global scenarios are PMTiles-only
  // (no full-world GeoJSON ships with the demo); the period-geometry sample
  // keeps the regional GeoJSON path.
  function setProvinceSourceMode({ meta, periodGeojson }) {
    const map = state.map;
    if (!map) return;
    const usePeriod = Boolean(state.periodGeometry && periodGeojson);
    const wantTiles = !usePeriod;
    if (wantTiles && !ensurePmtilesProtocol()) {
      throw new Error("PMTiles protocol unavailable — vector tiles cannot load.");
    }
    state.usePmtiles = wantTiles;

    const sourceLayer = state.manifest?.pmtiles?.source_layer || "ownership";
    const dynamicLayers = ["province-labels", "provinces-selected", "provinces-outline", "provinces-fill"];
    dynamicLayers.forEach((id) => {
      if (map.getLayer(id)) map.removeLayer(id);
    });
    if (map.getSource("provinces")) map.removeSource("provinces");

    if (wantTiles) {
      map.addSource("provinces", {
        type: "vector",
        url: pmtilesUrlFor(meta),
        promoteId: "province_id",
      });
    } else {
      map.addSource("provinces", {
        type: "geojson",
        data: periodGeojson,
        promoteId: "province_id",
      });
    }
    const layerSource = wantTiles ? { source: "provinces", "source-layer": sourceLayer } : { source: "provinces" };

    map.addLayer(
      {
        id: "provinces-fill",
        type: "fill",
        ...layerSource,
        paint: {
          "fill-color": ownershipFillExpression(),
          "fill-opacity": 0.78,
        },
      },
      "hierarchy-area-lines",
    );
    map.addLayer(
      {
        id: "provinces-outline",
        type: "line",
        ...layerSource,
        paint: {
          "line-color": "rgba(7, 16, 24, 0.75)",
          "line-width": ["interpolate", ["linear"], ["zoom"], 2, 0.2, 5, 0.7, 8, 1.1],
        },
      },
      "hierarchy-area-lines",
    );
    map.addLayer(
      {
        id: "provinces-selected",
        type: "line",
        ...layerSource,
        filter: ["==", ["get", "province_id"], ""],
        paint: {
          "line-color": "#e8a54b",
          "line-width": 3,
        },
      },
      "region-labels",
    );
    map.addLayer({
      id: "province-labels",
      type: "symbol",
      ...layerSource,
      minzoom: 5,
      layout: {
        "text-field": ["coalesce", ["get", "display_name"], ["get", "province_id"]],
        "text-size": 11,
        // demotiles hosts Noto Sans Regular; "Open Sans Regular" 404s and
        // prevents the entire provinces source from tiling/rendering.
        "text-font": ["Noto Sans Regular"],
        "text-max-width": 8,
      },
      paint: TEXT_STYLE,
    });

  }

  // Delegated listeners are bound once per map (they survive layer
  // remove/re-add by id); rebinding on every source swap would accumulate
  // duplicate handlers.
  function bindProvinceInteraction() {
    const map = state.map;
    map.on("click", "provinces-fill", (event) => {
      const feature = event.features?.[0];
      if (!feature) return;
      selectProvince(feature.properties?.province_id, feature.properties);
    });
    map.on("mouseenter", "provinces-fill", () => {
      map.getCanvas().style.cursor = "pointer";
    });
    map.on("mouseleave", "provinces-fill", () => {
      map.getCanvas().style.cursor = "";
    });
  }

  function applyPaintMode() {
    const map = state.map;
    if (!map?.getLayer("provinces-fill")) return;
    const ownershipOn = $("layer-ownership")?.checked !== false;
    const assignmentOn = $("layer-assignment")?.checked === true;
    const cultureOn = $("layer-culture")?.checked === true;
    const religionOn = $("layer-religion")?.checked === true;
    const hierarchyPaintOn = $("layer-hierarchy-paint")?.checked === true && !state.periodGeometry;
    // Priority: assignment > culture > religion > hierarchy > ownership > neutral
    if (assignmentOn) {
      state.paintMode = "assignment";
      map.setPaintProperty("provinces-fill", "fill-color", assignmentFillExpression());
    } else if (cultureOn) {
      state.paintMode = "culture";
      map.setPaintProperty("provinces-fill", "fill-color", cultureFillExpression());
    } else if (religionOn) {
      state.paintMode = "religion";
      map.setPaintProperty("provinces-fill", "fill-color", religionFillExpression());
    } else if (hierarchyPaintOn) {
      state.paintMode = "hierarchy";
      map.setPaintProperty("provinces-fill", "fill-color", hierarchyFillExpression());
    } else if (ownershipOn) {
      state.paintMode = "ownership";
      map.setPaintProperty("provinces-fill", "fill-color", ownershipFillExpression());
    } else {
      state.paintMode = "neutral";
      map.setPaintProperty("provinces-fill", "fill-color", "#4b5c66");
    }
    const painted = ownershipOn || assignmentOn || cultureOn || religionOn || hierarchyPaintOn;
    map.setPaintProperty("provinces-fill", "fill-opacity", painted ? 0.78 : 0.25);
  }

  function applyLayerVisibility() {
    const map = state.map;
    if (!map?.getLayer("adjacency-lines")) return;
    const adjToggle = $("layer-adjacency");
    const hierToggle = $("layer-hierarchy");
    const labels = $("layer-labels")?.checked !== false;
    const hints = $("layer-boundary-hints")?.checked === true;

    // The precomputed adjacency lines and hierarchy borders describe the global
    // build; hide them while the regional period-geometry sample is active.
    const adj = adjToggle?.checked !== false && !state.periodGeometry;
    const hier = hierToggle?.checked !== false && !state.periodGeometry;
    if (adjToggle) adjToggle.disabled = state.periodGeometry;
    if (hierToggle) hierToggle.disabled = state.periodGeometry;
    const hierPaintToggle = $("layer-hierarchy-paint");
    if (hierPaintToggle) hierPaintToggle.disabled = state.periodGeometry;

    map.setLayoutProperty("adjacency-lines", "visibility", adj ? "visible" : "none");
    [
      "hierarchy-area-lines",
      "hierarchy-region-lines",
      "hierarchy-superregion-lines",
      "region-labels",
      "superregion-labels",
    ].forEach((id) => {
      if (map.getLayer(id)) {
        map.setLayoutProperty(id, "visibility", hier ? "visible" : "none");
      }
    });
    if (map.getLayer("province-labels")) {
      map.setLayoutProperty("province-labels", "visibility", labels ? "visible" : "none");
    }
    if (map.getLayer("boundary-hints-line")) {
      const showHints = hints && state.boundaryHints;
      map.setLayoutProperty("boundary-hints-line", "visibility", showHints ? "visible" : "none");
      map.setLayoutProperty("boundary-hints-fill", "visibility", showHints ? "visible" : "none");
    }
    applyPaintMode();
  }

  function geometryTierLabel(meta) {
    if (state.periodGeometry && meta?.supports_period_geometry) {
      const pack = state.manifest?.period_geometry_pack || "period pack";
      return `geometry: ${state.manifest?.period_geometry_tier || "period-geometry"} (${pack})`;
    }
    return `geometry: ${state.manifest?.geometry_tier || "scaffold-baseline"} (global)`;
  }

  function syncM15Controls(meta) {
    const periodToggle = $("layer-period-geometry");
    const hintsToggle = $("layer-boundary-hints");
    const supports = Boolean(meta?.supports_period_geometry);
    if (periodToggle) {
      periodToggle.disabled = !supports;
      if (!supports) {
        periodToggle.checked = false;
        state.periodGeometry = false;
      } else {
        state.periodGeometry = periodToggle.checked === true;
      }
    }
    if (hintsToggle) {
      hintsToggle.disabled = !supports || !state.periodGeometry;
      if (!supports || !state.periodGeometry) {
        hintsToggle.checked = false;
        state.boundaryHints = false;
      } else {
        if (!hintsToggle.dataset.userTouched) {
          hintsToggle.checked = true;
        }
        state.boundaryHints = hintsToggle.checked === true;
      }
    }
  }

  function renderFutureSlots() {
    const root = $("future-slots");
    if (!root || !state.manifest) return;
    const slots = state.manifest.future_slots || [];
    root.innerHTML = slots
      .map(
        (slot) => `
      <li class="future-item" aria-disabled="true">
        <span class="lock" title="Not implemented yet">⊘</span>
        <div>
          <strong>${escapeHtml(slot.label)}</strong>
          <div class="meta">
            <span class="milestone">${escapeHtml(slot.milestone)}</span>
            <span class="slot-chip">room reserved</span>
          </div>
          <p>${escapeHtml(slot.desc)}</p>
        </div>
      </li>`,
      )
      .join("");
  }

  function identityLegendRows(legend) {
    const entries = legend?.entries || [];
    return entries.map((entry) => ({
      key: entry.id,
      label: entry.display_name || entry.id,
      color: entry.fill_color || entry.color || "#8a8a8a",
      count: entry.province_count,
    }));
  }

  function renderLegend(legend, identityLegend) {
    const root = $("legend");
    if (!root) return;
    if (state.paintMode === "assignment") {
      root.innerHTML = Object.entries(ASSIGNMENT_COLORS)
        .map(
          ([key, color]) => `
        <div class="legend-row">
          <span class="legend-swatch" style="background:${color}"></span>
          <span>${escapeHtml(key)}</span>
        </div>`,
        )
        .join("");
      return;
    }
    if (state.paintMode === "hierarchy") {
      const counts = state.manifest?.hierarchy?.counts || {};
      root.innerHTML = `
        <p class="help">Deterministic color per area (M21 hierarchy).</p>
        <p class="help">${escapeHtml(String(counts.areas ?? "—"))} areas ·
          ${escapeHtml(String(counts.regions ?? "—"))} regions ·
          ${escapeHtml(String(counts.superregions ?? "—"))} superregions</p>`;
      return;
    }
    if (state.paintMode === "culture" || state.paintMode === "religion") {
      const rows = identityLegendRows(identityLegend);
      if (!rows.length) {
        root.innerHTML = `<p class="help">No ${state.paintMode} entries in this scenario.</p>`;
        return;
      }
      const unassigned = identityLegend?.unassigned_province_count ?? 0;
      root.innerHTML =
        rows
          .slice(0, MAX_LEGEND_ROWS)
          .map(
            (row) => `
      <div class="legend-row">
        <span class="legend-swatch" style="background:${escapeHtml(row.color)}"></span>
        <span>${escapeHtml(row.label)} <code>${escapeHtml(row.key)}</code></span>
        <span class="legend-count">${escapeHtml(String(row.count ?? "—"))} prov</span>
      </div>`,
          )
          .join("") +
        (rows.length > MAX_LEGEND_ROWS
          ? `<p class="help">+${rows.length - MAX_LEGEND_ROWS} more…</p>`
          : "") +
        `<p class="help">unassigned: ${escapeHtml(String(unassigned))} · curated hints</p>`;
      return;
    }
    const tags = (legend?.tags || [])
      .slice()
      .sort((a, b) => (b.owner_province_count ?? 0) - (a.owner_province_count ?? 0));
    if (!tags.length) {
      root.innerHTML = `<p class="help">No legend tags in this scenario.</p>`;
      return;
    }
    root.innerHTML =
      tags
        .slice(0, MAX_LEGEND_ROWS)
        .map(
          (tag) => `
      <div class="legend-row">
        <span class="legend-swatch" style="background:${escapeHtml(tag.fill_color || tag.color || "#b0b0b0")}"></span>
        <span>${escapeHtml(tag.display_name || tag.tag)} <code>${escapeHtml(tag.tag)}</code></span>
        <span class="legend-count">${escapeHtml(String(tag.owner_province_count ?? "—"))} prov</span>
      </div>`,
        )
        .join("") +
      (tags.length > MAX_LEGEND_ROWS
        ? `<p class="help">+${tags.length - MAX_LEGEND_ROWS} more owners…</p>`
        : "");
  }

  function hierarchyName(id) {
    if (!id) return null;
    return state.hierarchyNames.get(id) || null;
  }

  function hierarchyRow(label, id) {
    const name = hierarchyName(id);
    if (!id) {
      return `<dt>${label}</dt><dd>—</dd>`;
    }
    return `<dt>${label}</dt><dd>${name ? `${escapeHtml(name)} ` : ""}<code class="hier-id">${escapeHtml(id)}</code></dd>`;
  }

  function selectProvince(provinceId, props) {
    state.selectedId = provinceId || null;
    const map = state.map;
    if (map?.getLayer("provinces-selected")) {
      map.setFilter("provinces-selected", [
        "==",
        ["get", "province_id"],
        provinceId || "",
      ]);
    }
    const root = $("inspector");
    if (!root) return;
    if (!provinceId || !props) {
      root.className = "inspector empty";
      root.innerHTML = "<p>Select a province on the map.</p>";
      return;
    }
    root.className = "inspector";
    const ownerColor = props.owner_color || "#b0b0b0";
    root.innerHTML = `
      <div class="inspector-card">
        <h3>${escapeHtml(props.display_name || provinceId)}</h3>
        <p class="pid">${escapeHtml(provinceId)}</p>
        <dl class="kv">
          <dt>Owner</dt>
          <dd><span class="swatch" style="background:${escapeHtml(ownerColor)}"></span><code>${escapeHtml(props.owner || "—")}</code></dd>
          <dt>Controller</dt>
          <dd><code>${escapeHtml(props.controller || "—")}</code></dd>
          <dt>Cores</dt>
          <dd>${escapeHtml(formatList(props.cores))}</dd>
          <dt>Claims</dt>
          <dd>${escapeHtml(formatList(props.claims))}</dd>
          <dt>Assignment</dt>
          <dd><code>${escapeHtml(props.assignment_source || "—")}</code></dd>
          <dt>Culture</dt>
          <dd><span class="swatch" style="background:${escapeHtml(props.culture_color || "#8a8a8a")}"></span>${escapeHtml(props.culture || "unassigned")}</dd>
          <dt>Religion</dt>
          <dd><span class="swatch" style="background:${escapeHtml(props.religion_color || "#8a8a8a")}"></span>${escapeHtml(props.religion || "unassigned")}</dd>
          <dt>Country</dt>
          <dd><code>${escapeHtml(props.parent_country_id || "—")}</code> / <code>${escapeHtml(props.parent_region_id || "—")}</code></dd>
          ${hierarchyRow("Area", props.parent_area_id)}
          ${hierarchyRow("Region", props.parent_geo_region_id)}
          ${hierarchyRow("Superregion", props.parent_superregion_id)}
          <dt>Scenario</dt>
          <dd><code>${escapeHtml(props.scenario_id || state.scenarioId)}</code></dd>
          <dt>Notes</dt>
          <dd>${escapeHtml(props.notes || "—")}</dd>
        </dl>
      </div>`;
  }

  function updateChrome(meta, legend) {
    const label = $("scenario-label");
    const politics = $("politics-tier");
    const geometry = $("geometry-tier");
    if (label) {
      label.textContent = legend?.label || meta?.label || meta?.id || state.scenarioId;
    }
    if (politics) {
      politics.textContent = `politics: ${meta?.politics_tier || "—"}`;
    }
    if (geometry) {
      geometry.textContent = geometryTierLabel(meta);
    }
  }

  async function loadScenario(scenarioId) {
    const meta = scenarioMeta(scenarioId);
    if (!meta || meta.status !== "live") {
      setStatus("That era is reserved for a future milestone — geometry and politics not packaged yet.", false);
      return;
    }

    setStatus("Loading scenario…");
    state.scenarioId = scenarioId;

    document.querySelectorAll(".era-btn").forEach((btn) => {
      const active = btn.dataset.era === scenarioId;
      btn.classList.toggle("is-active", active && !btn.classList.contains("is-future"));
      if (!btn.classList.contains("is-future")) {
        btn.setAttribute("aria-selected", active ? "true" : "false");
      }
    });

    syncM15Controls(meta);

    let bundle = state.cache.get(scenarioId);
    if (!bundle) {
      const optional = (key) =>
        meta[key] ? fetchJson(`${DATA_BASE}/${meta[key]}`) : Promise.resolve(null);
      const [
        legend,
        cultureLegend,
        religionLegend,
        periodGeojson,
        periodLegend,
        periodCultureLegend,
        periodReligionLegend,
        boundaryHints,
      ] = await Promise.all([
        fetchJson(`${DATA_BASE}/${meta.legend}`),
        optional("culture_legend"),
        optional("religion_legend"),
        optional("period_geojson"),
        optional("period_legend"),
        optional("period_culture_legend"),
        optional("period_religion_legend"),
        optional("boundary_hints"),
      ]);
      bundle = {
        legend,
        cultureLegend,
        religionLegend,
        periodGeojson,
        periodLegend,
        periodCultureLegend,
        periodReligionLegend,
        boundaryHints,
      };
      state.cache.set(scenarioId, bundle);
    }

    const firstLoad = !state.map.getSource("hierarchy-areas");
    ensureStaticLayers();
    setProvinceSourceMode({ meta, periodGeojson: bundle.periodGeojson });
    if (firstLoad) {
      bindProvinceInteraction();
    }

    state.map
      .getSource("boundary-hints")
      .setData(
        (state.periodGeometry && bundle.boundaryHints) || {
          type: "FeatureCollection",
          features: [],
        },
      );
    applyLayerVisibility();

    const legend =
      state.periodGeometry && bundle.periodLegend ? bundle.periodLegend : bundle.legend;
    const cultureLegend =
      state.periodGeometry && bundle.periodCultureLegend
        ? bundle.periodCultureLegend
        : bundle.cultureLegend;
    const religionLegend =
      state.periodGeometry && bundle.periodReligionLegend
        ? bundle.periodReligionLegend
        : bundle.religionLegend;
    updateChrome(meta, legend);
    const identityLegend =
      state.paintMode === "religion" ? religionLegend : cultureLegend;
    renderLegend(legend, identityLegend);

    if (state.periodGeometry && bundle.periodGeojson) {
      // Frame the regional period-geometry sample.
      const bounds = new maplibregl.LngLatBounds();
      (bundle.periodGeojson.features || []).forEach((feature) => {
        const c = centroidOf(feature);
        if (c) bounds.extend(c);
        const coords =
          feature.geometry?.type === "Polygon"
            ? feature.geometry.coordinates[0]
            : feature.geometry?.type === "MultiPolygon"
              ? feature.geometry.coordinates.flatMap((p) => p[0] || [])
              : [];
        coords.forEach((pair) => bounds.extend(pair));
      });
      if (!bounds.isEmpty()) {
        state.map.fitBounds(bounds, { padding: 56, maxZoom: 7.2, duration: 600 });
      }
    }

    // Selection: the source swap cleared the on-map highlight, so the card
    // must not keep showing the previous scenario's politics. Re-resolve
    // against the period sample when active; otherwise clear until the next
    // click on the new scenario's tiles.
    if (state.selectedId) {
      if (state.periodGeometry && bundle.periodGeojson) {
        const match = (bundle.periodGeojson.features || []).find(
          (f) => f.properties?.province_id === state.selectedId,
        );
        if (match) {
          selectProvince(state.selectedId, match.properties);
        } else {
          selectProvince(null);
        }
      } else {
        selectProvince(null);
      }
    }

    setStatus("");
  }

  function bindControls() {
    document.querySelectorAll(".era-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        if (btn.classList.contains("is-future") || btn.getAttribute("aria-disabled") === "true") {
          setStatus(
            "That era slot is reserved pending worldwide research and runtime certification. Live eras: modern-baseline.",
            false,
          );
          return;
        }
        loadScenario(btn.dataset.era).catch((err) => {
          console.error(err);
          setStatus(err.message || "Failed to load scenario", true);
        });
      });
    });

    function refreshPaintAndLegend() {
      applyLayerVisibility();
      const meta = scenarioMeta(state.scenarioId);
      const bundle = state.cache.get(state.scenarioId);
      const legend =
        state.periodGeometry && bundle?.periodLegend
          ? bundle.periodLegend
          : bundle?.legend;
      const cultureLegend =
        state.periodGeometry && bundle?.periodCultureLegend
          ? bundle.periodCultureLegend
          : bundle?.cultureLegend;
      const religionLegend =
        state.periodGeometry && bundle?.periodReligionLegend
          ? bundle.periodReligionLegend
          : bundle?.religionLegend;
      const identityLegend =
        state.paintMode === "religion" ? religionLegend : cultureLegend;
      renderLegend(legend, identityLegend);
      updateChrome(meta, legend);
    }

    ["layer-ownership", "layer-assignment", "layer-adjacency", "layer-labels", "layer-hierarchy"].forEach(
      (id) => {
        $(id)?.addEventListener("change", refreshPaintAndLegend);
      },
    );

    // Paint-mode exclusivity: culture / religion / hierarchy paint are mutually
    // exclusive; the priority chain in applyPaintMode handles ownership.
    const exclusivePaint = ["layer-culture", "layer-religion", "layer-hierarchy-paint"];
    exclusivePaint.forEach((id) => {
      $(id)?.addEventListener("change", (event) => {
        if (event.target.checked) {
          exclusivePaint
            .filter((other) => other !== id)
            .forEach((other) => {
              if ($(other)) $(other).checked = false;
            });
        }
        refreshPaintAndLegend();
      });
    });

    $("layer-period-geometry")?.addEventListener("change", (event) => {
      state.periodGeometry = event.target.checked === true;
      loadScenario(state.scenarioId).catch((err) => {
        console.error(err);
        setStatus(err.message || "Failed to toggle period geometry", true);
      });
    });
    $("layer-boundary-hints")?.addEventListener("change", (event) => {
      event.target.dataset.userTouched = "1";
      state.boundaryHints = event.target.checked === true;
      applyLayerVisibility();
    });
  }

  function indexHierarchyNames() {
    ["areas", "regions", "superregions"].forEach((key) => {
      (state.hierarchy[key]?.features || []).forEach((feature) => {
        const props = feature.properties || {};
        if (props.region_id) {
          state.hierarchyNames.set(props.region_id, props.display_name || props.region_id);
        }
      });
    });
  }

  async function boot() {
    bindControls();
    try {
      // Revalidate the release contract on every page load so a promoted M22
      // deployment cannot be paired with a stale pre-M22 manifest from cache.
      const manifest = await fetchJson(`${DATA_BASE}/demo-manifest.json`, {
        cache: "no-cache",
      });
      state.manifest = manifest;
      renderFutureSlots();

      const hierarchyFiles = manifest.hierarchy || {};
      const optionalLayer = (name) =>
        name
          ? fetchJson(`${DATA_BASE}/${name}`).catch(() => null)
          : Promise.resolve(null);
      const [areas, regions, superregions, adjacencyLines] = await Promise.all([
        optionalLayer(hierarchyFiles.areas),
        optionalLayer(hierarchyFiles.regions),
        optionalLayer(hierarchyFiles.superregions),
        optionalLayer(manifest.adjacency?.lines),
      ]);
      state.hierarchy = { areas, regions, superregions };
      state.adjacencyLines = adjacencyLines;
      indexHierarchyNames();

      state.map = new maplibregl.Map({
        container: "map",
        style: createMapStyle(),
        center: [12, 30],
        zoom: 1.7,
        attributionControl: true,
      });
      state.map.addControl(new maplibregl.NavigationControl({ visualizePitch: false }), "top-right");

      await new Promise((resolve) => {
        if (state.map.loaded()) resolve();
        else state.map.once("load", resolve);
      });

      await loadScenario(state.scenarioId);
    } catch (err) {
      console.error(err);
      setStatus(err.message || "Demo failed to start", true);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
