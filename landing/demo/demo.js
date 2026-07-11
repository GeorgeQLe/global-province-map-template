/* global maplibregl */

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

  const state = {
    manifest: null,
    adjacency: null,
    scenarioId: "official-1444",
    cache: new Map(),
    map: null,
    selectedId: null,
    paintMode: "ownership",
  };

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

  async function fetchJson(url) {
    const response = await fetch(url);
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

  function formatList(value) {
    if (Array.isArray(value)) {
      return value.length ? value.join(", ") : "—";
    }
    if (value == null || value === "") return "—";
    return String(value);
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

  function buildAdjacencyGeoJSON(features, edges) {
    const centers = new Map();
    features.forEach((feature) => {
      const id = feature.properties?.province_id;
      const c = centroidOf(feature);
      if (id && c) centers.set(id, c);
    });

    const lineFeatures = [];
    const nodeFeatures = [];
    centers.forEach((coords, id) => {
      nodeFeatures.push({
        type: "Feature",
        properties: { province_id: id },
        geometry: { type: "Point", coordinates: coords },
      });
    });

    (edges || []).forEach((edge) => {
      const a = centers.get(edge.from);
      const b = centers.get(edge.to);
      // Skip edges that leave the land sample (e.g. sea zones not in choropleth).
      if (!a || !b) return;
      lineFeatures.push({
        type: "Feature",
        properties: {
          type: edge.type,
          from: edge.from,
          to: edge.to,
        },
        geometry: {
          type: "LineString",
          coordinates: [a, b],
        },
      });
    });

    return {
      lines: { type: "FeatureCollection", features: lineFeatures },
      nodes: { type: "FeatureCollection", features: nodeFeatures },
    };
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

  function ensureLayers() {
    const map = state.map;
    if (!map.getSource("provinces")) {
      map.addSource("provinces", {
        type: "geojson",
        data: { type: "FeatureCollection", features: [] },
        promoteId: "province_id",
      });
      map.addSource("adjacency-lines", {
        type: "geojson",
        data: { type: "FeatureCollection", features: [] },
      });
      map.addSource("adjacency-nodes", {
        type: "geojson",
        data: { type: "FeatureCollection", features: [] },
      });

      map.addLayer({
        id: "provinces-fill",
        type: "fill",
        source: "provinces",
        paint: {
          "fill-color": ownershipFillExpression(),
          "fill-opacity": 0.78,
        },
      });
      map.addLayer({
        id: "provinces-outline",
        type: "line",
        source: "provinces",
        paint: {
          "line-color": "rgba(7, 16, 24, 0.75)",
          "line-width": 1.1,
        },
      });
      map.addLayer({
        id: "provinces-selected",
        type: "line",
        source: "provinces",
        filter: ["==", ["get", "province_id"], ""],
        paint: {
          "line-color": "#e8a54b",
          "line-width": 3,
        },
      });
      map.addLayer({
        id: "adjacency-lines",
        type: "line",
        source: "adjacency-lines",
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
          "line-width": 2,
          "line-opacity": 0.85,
        },
      });
      map.addLayer({
        id: "adjacency-nodes",
        type: "circle",
        source: "adjacency-nodes",
        paint: {
          "circle-radius": 3.5,
          "circle-color": "#ebe6d8",
          "circle-stroke-width": 1,
          "circle-stroke-color": "#0c1a24",
        },
      });
      map.addLayer({
        id: "province-labels",
        type: "symbol",
        source: "provinces",
        layout: {
          "text-field": ["coalesce", ["get", "display_name"], ["get", "province_id"]],
          "text-size": 11,
          "text-font": ["Open Sans Regular"],
          "text-max-width": 8,
        },
        paint: {
          "text-color": "#f5f0e4",
          "text-halo-color": "rgba(7, 16, 24, 0.9)",
          "text-halo-width": 1.2,
        },
      });

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
  }

  function applyPaintMode() {
    const map = state.map;
    if (!map?.getLayer("provinces-fill")) return;
    const ownershipOn = $("layer-ownership")?.checked !== false;
    const assignmentOn = $("layer-assignment")?.checked === true;
    if (assignmentOn) {
      state.paintMode = "assignment";
      map.setPaintProperty("provinces-fill", "fill-color", assignmentFillExpression());
    } else if (ownershipOn) {
      state.paintMode = "ownership";
      map.setPaintProperty("provinces-fill", "fill-color", ownershipFillExpression());
    } else {
      state.paintMode = "neutral";
      map.setPaintProperty("provinces-fill", "fill-color", "#4b5c66");
    }
    map.setPaintProperty("provinces-fill", "fill-opacity", ownershipOn || assignmentOn ? 0.78 : 0.25);
  }

  function applyLayerVisibility() {
    const map = state.map;
    if (!map?.getLayer("adjacency-lines")) return;
    const adj = $("layer-adjacency")?.checked !== false;
    const labels = $("layer-labels")?.checked !== false;
    map.setLayoutProperty("adjacency-lines", "visibility", adj ? "visible" : "none");
    map.setLayoutProperty("adjacency-nodes", "visibility", adj ? "visible" : "none");
    map.setLayoutProperty("province-labels", "visibility", labels ? "visible" : "none");
    applyPaintMode();
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

  function renderLegend(legend) {
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
    const tags = legend?.tags || [];
    if (!tags.length) {
      root.innerHTML = `<p class="help">No legend tags in sample.</p>`;
      return;
    }
    root.innerHTML = tags
      .map(
        (tag) => `
      <div class="legend-row">
        <span class="legend-swatch" style="background:${escapeHtml(tag.fill_color || tag.color || "#b0b0b0")}"></span>
        <span>${escapeHtml(tag.display_name || tag.tag)} <code>${escapeHtml(tag.tag)}</code></span>
        <span class="legend-count">${escapeHtml(String(tag.owner_province_count ?? "—"))} prov</span>
      </div>`,
      )
      .join("");
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
          <dd>${escapeHtml(props.culture || "—")}</dd>
          <dt>Religion</dt>
          <dd>${escapeHtml(props.religion || "—")}</dd>
          <dt>Parent</dt>
          <dd><code>${escapeHtml(props.parent_country_id || "—")}</code> / <code>${escapeHtml(props.parent_region_id || "—")}</code></dd>
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
      geometry.textContent = `geometry: ${state.manifest?.geometry_tier || "scaffold-baseline"}`;
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

    let bundle = state.cache.get(scenarioId);
    if (!bundle) {
      const [geojson, legend] = await Promise.all([
        fetchJson(`${DATA_BASE}/${meta.geojson}`),
        fetchJson(`${DATA_BASE}/${meta.legend}`),
      ]);
      const graph = buildAdjacencyGeoJSON(geojson.features || [], state.adjacency?.edges || []);
      bundle = { geojson, legend, graph };
      state.cache.set(scenarioId, bundle);
    }

    ensureLayers();
    state.map.getSource("provinces").setData(bundle.geojson);
    state.map.getSource("adjacency-lines").setData(bundle.graph.lines);
    state.map.getSource("adjacency-nodes").setData(bundle.graph.nodes);
    applyLayerVisibility();
    updateChrome(meta, bundle.legend);
    renderLegend(bundle.legend);

    const bounds = new maplibregl.LngLatBounds();
    (bundle.geojson.features || []).forEach((feature) => {
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

    // Reselect if still present.
    if (state.selectedId) {
      const match = (bundle.geojson.features || []).find(
        (f) => f.properties?.province_id === state.selectedId,
      );
      if (match) {
        selectProvince(state.selectedId, match.properties);
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
            "1936 is a reserved HOI-leaning slot (M16+). Live eras today: official-1444, official-1836, modern-baseline.",
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

    ["layer-ownership", "layer-assignment", "layer-adjacency", "layer-labels"].forEach((id) => {
      $(id)?.addEventListener("change", () => {
        applyLayerVisibility();
        const meta = scenarioMeta(state.scenarioId);
        const legend = state.cache.get(state.scenarioId)?.legend;
        renderLegend(legend);
        updateChrome(meta, legend);
      });
    });
  }

  async function boot() {
    bindControls();
    try {
      const [manifest, adjacency] = await Promise.all([
        fetchJson(`${DATA_BASE}/demo-manifest.json`),
        fetchJson(`${DATA_BASE}/adjacency.json`),
      ]);
      state.manifest = manifest;
      state.adjacency = adjacency;
      renderFutureSlots();

      state.map = new maplibregl.Map({
        container: "map",
        style: createMapStyle(),
        center: [4.2, 50.5],
        zoom: 5.2,
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
