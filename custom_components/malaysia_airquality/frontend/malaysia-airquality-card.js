/* Malaysia Air Quality Status - map card
 * Every DOE APIMS station on a map, coloured by the official API band.
 * Served by the malaysia_airquality integration; no separate install needed.
 */
const CARD_VERSION = "0.2.7";
const BASE = "/malaysia_airquality";

// DOE Malaysia API bands and their official colours
const BANDS = [
  { max: 50, key: "good", en: "Good", ms: "Baik", bg: "#1E5AC8", fg: "#fff" },
  { max: 100, key: "moderate", en: "Moderate", ms: "Sederhana", bg: "#2E9E44", fg: "#fff" },
  { max: 200, key: "unhealthy", en: "Unhealthy", ms: "Tidak Sihat", bg: "#F2C200", fg: "#222" },
  { max: 300, key: "very_unhealthy", en: "Very Unhealthy", ms: "Sangat Tidak Sihat", bg: "#F07C00", fg: "#fff" },
  { max: Infinity, key: "hazardous", en: "Hazardous", ms: "Berbahaya", bg: "#D0021B", fg: "#fff" },
];
const NA = { key: "unavailable", en: "No data", ms: "Tiada data", bg: "#9E9E9E", fg: "#fff" };

const band = (api) => (api === null || api === undefined || api < 0 ? NA : BANDS.find((b) => api <= b.max));

let leafletPromise;
function loadLeaflet() {
  if (window.L) return Promise.resolve(window.L);
  if (!leafletPromise) {
    leafletPromise = new Promise((resolve, reject) => {
      const s = document.createElement("script");
      s.src = `${BASE}/leaflet.js?v=1.9.4`;
      s.onload = () => resolve(window.L);
      s.onerror = () => reject(new Error("Leaflet failed to load"));
      document.head.appendChild(s);
    });
  }
  return leafletPromise;
}

class MalaysiaAirQualityCard extends HTMLElement {
  setConfig(config) {
    this._config = {
      height: 420,
      zoom: 9,
      show_mobile: true,
      show_legend: true,
      dark_mode: "auto", // auto | true | false
      language: "auto", // auto | en | ms
      ...config,
    };
    this._built = false;
    this._lastStamp = null;
    if (this._hass) this.hass = this._hass; // redraw straight away when the editor changes something
  }

  static getStubConfig(hass) {
    const ent = Object.keys(hass.states).find(
      (e) => e.startsWith("sensor.") && Array.isArray(hass.states[e].attributes.stations)
    );
    return { entity: ent || "" };
  }

  getCardSize() {
    return Math.ceil((this._config?.height || 420) / 50);
  }

  // Sections view: resizable. Default rows follow `height` (HA row = 56px + 8px gap).
  getGridOptions() {
    const h = Number(this._config?.height) || 420;
    return { columns: 12, min_columns: 4, rows: Math.max(3, Math.round((h + 8) / 64)), min_rows: 3 };
  }

  static getConfigElement() {
    return document.createElement("malaysia-airquality-card-editor");
  }

  // HA sets layout = "grid" inside sections; the map then fills whatever size the user drags it to.
  set layout(v) {
    this._layout = v;
    this.classList.toggle("grid", v === "grid");
  }
  get layout() {
    return this._layout;
  }

  set hass(hass) {
    this._hass = hass;
    const id = this._config.entity || MalaysiaAirQualityCard.getStubConfig(hass).entity;
    const st = id && hass.states[id];
    if (!this._built) this._build();
    if (!st) {
      this._msg.textContent = `Entity not found: ${id || "(none)"}. Enable the "All Stations" sensor.`;
      this._msg.style.display = "block";
      return;
    }
    this._msg.style.display = "none";
    if (st.last_updated === this._lastStamp && this._map) return;
    this._lastStamp = st.last_updated;
    this._state = st;
    this._ready.then(() => this._render());
  }

  get _lang() {
    const l = this._config.language;
    if (l === "en" || l === "ms") return l;
    return (this._hass?.locale?.language || this._hass?.language || "en").startsWith("ms") ? "ms" : "en";
  }

  get _dark() {
    const d = this._config.dark_mode;
    if (d === true || d === "true") return true;
    if (d === false || d === "false") return false;
    return !!this._hass?.themes?.darkMode;
  }

  _build() {
    this._built = true;
    const h = this._config.height;
    if (this._map) { this._map.remove(); this._map = null; } this._tiles = null;
    if (!this.shadowRoot) this.attachShadow({ mode: "open" });
    this.shadowRoot.innerHTML = `
      <link rel="stylesheet" href="${BASE}/leaflet.css?v=1.9.4">
      <style>
        :host { display: block; }
        :host(.grid) { height: 100%; }
        ha-card { overflow: hidden; display: flex; flex-direction: column; }
        :host(.grid) ha-card { height: 100%; }
        .wrap { position: relative; flex: 1 1 auto; min-height: 0; }
        .leaflet-container { background: var(--secondary-background-color, #eee); font: inherit; }
        :host(.dark) .leaflet-tile-pane { filter: invert(.9) hue-rotate(180deg) brightness(1.1) contrast(1.1) saturate(.35); }
        :host(.dark) .leaflet-control-attribution, :host(.dark) .leaflet-bar a { background: #222; color: #ccc; }
        .head { padding: 12px 16px 0; font: 500 16px var(--paper-font-body1_-_font-family, inherit); }
        #map { height: ${h}px; width: 100%; background: var(--secondary-background-color); }
        :host(.grid) #map { height: 100%; min-height: 120px; }
        .msg { display:none; padding: 16px; color: var(--error-color); }
        .pin { display:flex; align-items:center; justify-content:center; border-radius:50%;
               font: 700 11px/1 system-ui, sans-serif; box-shadow: 0 1px 4px rgba(0,0,0,.45);
               border: 2px solid rgba(255,255,255,.9); box-sizing: border-box; }
        .pin.sel { border: 3px solid #000; outline: 2px solid #fff; }
        .pin.mob { border-style: dashed; }
        .home { width:14px; height:14px; border-radius:50%; background: var(--primary-color, #03a9f4);
                border: 3px solid #fff; box-shadow: 0 0 0 2px var(--primary-color, #03a9f4); }
        .legend { position:absolute; left:8px; bottom:22px; z-index:500; display:flex; gap:2px;
                  font: 600 10px system-ui, sans-serif; border-radius: 6px; overflow:hidden;
                  box-shadow: 0 1px 4px rgba(0,0,0,.35); }
        .legend span { padding: 4px 6px; }
        .pop b { font-size: 14px; } .pop .api { font-size: 22px; font-weight: 700; }
        .pop .chip { display:inline-block; padding:2px 8px; border-radius:10px; margin:4px 0; font-weight:600; }
        .pop small { color: #666; }
        .stamp { position:absolute; right:8px; top:8px; z-index:500;
                 background: rgba(0,0,0,.55); color:#fff; font: 11px system-ui; padding: 3px 7px; border-radius: 4px; }
      </style>
      <ha-card>
        ${this._config.title ? `<div class="head">${this._config.title}</div>` : ""}
        <div class="msg"></div>
        <div class="wrap">
          <div id="map"></div>
          <div class="stamp"></div>
          <div class="legend"></div>
        </div>
      </ha-card>`;
    this._msg = this.shadowRoot.querySelector(".msg");
    this._stamp = this.shadowRoot.querySelector(".stamp");
    this._ready = loadLeaflet()
      .then((L) => this._initMap(L))
      .catch((e) => {
        this._msg.textContent = e.message;
        this._msg.style.display = "block";
      });
  }

  _initMap(L) {
    this.L = L;
    const el = this.shadowRoot.getElementById("map");
    const lat = this._config.center?.[0] ?? this._hass.config.latitude ?? 3.139;
    const lon = this._config.center?.[1] ?? this._hass.config.longitude ?? 101.6869;
    this._map = L.map(el, { zoomControl: true, attributionControl: true, scrollWheelZoom: false }).setView([lat, lon], this._config.zoom);
    this._setTiles();
    this._layer = L.layerGroup().addTo(this._map);
    if (this._hass.config.latitude) {
      L.marker([this._hass.config.latitude, this._hass.config.longitude], {
        icon: L.divIcon({ className: "", html: '<div class="home"></div>', iconSize: [14, 14] }),
        interactive: false,
        zIndexOffset: 1000,
      }).addTo(this._map);
    }
    this._center = [lat, lon];
    this._sized = false;
    new ResizeObserver(() => {
      if (!this._map || !el.clientWidth || !el.clientHeight) return;
      // Leaflet caches the size it was created at (often 0 in the editor preview): re-centre once it has a real one.
      this._map._sizeChanged = true;
      this._map.invalidateSize();
      if (!this._sized) {
        this._sized = true;
        this._map.setView(this._center, this._config.zoom);
      }
    }).observe(el);
    if (this._config.show_legend) {
      this.shadowRoot.querySelector(".legend").innerHTML = BANDS.map(
        (b) => `<span style="background:${b.bg};color:${b.fg}">${b[this._lang]}</span>`
      ).join("");
    }
  }

  _setTiles() {
    this.classList.toggle("dark", this._dark);
    if (this._tiles) return;
    this._tiles = this.L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
      // HA pages send no Referer, and OSM blocks tiles without one (403), same fix as the Rapid Bus card.
      referrerPolicy: "strict-origin-when-cross-origin",
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> | DOE Malaysia (APIMS)',
    }).addTo(this._map);
  }

  _render() {
    if (!this._map || !this._state) return;
    const L = this.L;
    this._setTiles();
    this._layer.clearLayers();
    const lang = this._lang;
    const selected = this._state.attributes.selected;
    let newest = null;
    for (const [id, name, lat, lon, api, pol, updated, mobile] of this._state.attributes.stations || []) {
      if (mobile && !this._config.show_mobile) continue;
      const b = band(api);
      const val = api === null || api === undefined ? "–" : Math.round(api);
      const size = b === NA ? 20 : api >= 100 ? 34 : 30;
      const cls = ["pin", id === selected ? "sel" : "", mobile ? "mob" : ""].join(" ");
      const icon = L.divIcon({
        className: "",
        html: `<div class="${cls}" style="width:${size}px;height:${size}px;background:${b.bg};color:${b.fg}">${val}</div>`,
        iconSize: [size, size],
        iconAnchor: [size / 2, size / 2],
      });
      const t = updated ? new Date(updated) : null;
      if (t && (!newest || t > newest)) newest = t;
      const when = t
        ? t.toLocaleString(lang === "ms" ? "ms-MY" : "en-MY", { hour: "numeric", minute: "2-digit", day: "numeric", month: "short", timeZone: "Asia/Kuala_Lumpur" })
        : "–";
      L.marker([lat, lon], { icon, zIndexOffset: b === NA ? -1000 : api || 0 })
        .bindPopup(
          `<div class="pop"><b>${name}</b>${mobile ? " <small>(mobile)</small>" : ""}<br>
           <span class="api">${val}</span><br>
           <span class="chip" style="background:${b.bg};color:${b.fg}">${b[lang]}</span><br>
           ${lang === "ms" ? "Pencemar" : "Pollutant"}: ${pol || "–"}<br>
           <small>${id} · ${when}</small></div>`
        )
        .addTo(this._layer);
    }
    this._stamp.textContent = newest
      ? newest.toLocaleTimeString(lang === "ms" ? "ms-MY" : "en-MY", { hour: "numeric", minute: "2-digit", timeZone: "Asia/Kuala_Lumpur" })
      : "";
  }
}

class MalaysiaAirQualityCardEditor extends HTMLElement {
  setConfig(config) {
    this._config = config;
    this._draw();
  }
  set hass(hass) {
    this._hass = hass;
    this._draw();
  }
  _draw() {
    if (!this._hass || !this._config) return;
    if (!this._form) {
      this._form = document.createElement("ha-form");
      this._form.computeLabel = (s) =>
        ({
          entity: "All Stations sensor",
          title: "Title",
          zoom: "Zoom",
          height: "Height in px (masonry view only)",
          show_mobile: "Show mobile stations",
          show_legend: "Show legend",
          dark_mode: "Map style",
          language: "Language",
        })[s.name] || s.name;
      this._form.addEventListener("value-changed", (ev) => {
        this._config = ev.detail.value;
        this.dispatchEvent(new CustomEvent("config-changed", { detail: { config: this._config }, bubbles: true, composed: true }));
      });
      this.appendChild(this._form);
    }
    this._form.hass = this._hass;
    this._form.data = { zoom: 9, height: 420, show_mobile: true, show_legend: true, dark_mode: "auto", language: "auto", ...this._config };
    this._form.schema = [
      { name: "entity", required: true, selector: { entity: { integration: "malaysia_airquality", domain: "sensor" } } },
      { name: "title", selector: { text: {} } },
      {
        type: "grid",
        name: "",
        schema: [
          { name: "zoom", selector: { number: { min: 5, max: 16, mode: "box" } } },
          { name: "height", selector: { number: { min: 150, max: 900, step: 10, mode: "box" } } },
          { name: "show_mobile", selector: { boolean: {} } },
          { name: "show_legend", selector: { boolean: {} } },
          {
            name: "dark_mode",
            selector: {
              select: {
                mode: "dropdown",
                options: [
                  { value: "auto", label: "Follow theme" },
                  { value: "true", label: "Always dark" },
                  { value: "false", label: "Always light" },
                ],
              },
            },
          },
          {
            name: "language",
            selector: {
              select: {
                mode: "dropdown",
                options: [
                  { value: "auto", label: "Follow HA" },
                  { value: "en", label: "English" },
                  { value: "ms", label: "Bahasa Melayu" },
                ],
              },
            },
          },
        ],
      },
    ];
  }
}

if (!customElements.get("malaysia-airquality-card")) customElements.define("malaysia-airquality-card", MalaysiaAirQualityCard);
if (!customElements.get("malaysia-airquality-card-editor"))
  customElements.define("malaysia-airquality-card-editor", MalaysiaAirQualityCardEditor);
window.customCards = window.customCards || [];
if (!window.customCards.some((c) => c.type === "malaysia-airquality-card")) {
  window.customCards.push({
    type: "malaysia-airquality-card",
    name: "Malaysia Air Quality Map",
    description: "Every DOE APIMS station on a map, coloured by API band.",
    preview: true,
    documentationURL: "https://github.com/zubir2k/homeassistant-malaysiaairquality",
  });
}
console.info(`%c MALAYSIA-AIRQUALITY-CARD %c ${CARD_VERSION} `, "background:#F2C200;color:#222;font-weight:700", "background:#222;color:#fff");
