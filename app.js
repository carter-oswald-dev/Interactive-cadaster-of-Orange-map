// ---- Configuration: image overlay geographic bounds (from GeoTIFF georeferencing) ----
// Bounds format for Leaflet: [[south, west], [north, east]]
const IMAGE_BOUNDS = [
  [44.365626838001994, 4.690140138207285],   // south-west
  [44.44836706961,      4.851866330454634]   // north-east
];

const map = L.map('map', {
  crs: L.CRS.EPSG3857,
  minZoom: 12,
  maxZoom: 20,
  zoomSnap: 0.25
});

// ---- Base layer: the georeferenced topographic image (compressed from the source GeoTIFF) ----
const baseImage = L.imageOverlay('img/base.jpg', IMAGE_BOUNDS, {
  attribution: 'Base map: IGN topographic sheet w/ cadastral fragment overlay (source GeoTIFF)'
}).addTo(map);

map.fitBounds(IMAGE_BOUNDS);

// ---- Transcription layer: polygons + scaling text labels ----
const plaqueLabelPane = map.createPane('plaqueLabels');
plaqueLabelPane.style.zIndex = 650;
plaqueLabelPane.style.pointerEvents = 'none';

let geojsonLayer;
let labelMarkers = []; // {marker, feature, latlngBounds}

function computeFontSize(feature, zoom, bounds) {
  // Base the font size on the polygon's on-screen pixel size at the current zoom,
  // so text scales up/down with the box, and also responds to zoom level directly.
  const nw = map.project(bounds.getNorthWest(), zoom);
  const se = map.project(bounds.getSouthEast(), zoom);
  const pxWidth = Math.abs(se.x - nw.x);
  const pxHeight = Math.abs(se.y - nw.y);

  const text = feature.properties.text || '';
  const lines = text.split('\n');
  const longestLine = Math.max(...lines.map(l => l.length), 1);
  const numLines = lines.length;

  // Monospace char aspect ratio ~0.6 width:height for Courier-like fonts.
  const CHAR_ASPECT = 0.6;

  // Max font size that fits width-wise and height-wise inside the box (with padding).
  const padding = 0.85; // use 85% of box to leave a margin
  const fontSizeForWidth = (pxWidth * padding) / (longestLine * CHAR_ASPECT);
  const fontSizeForHeight = (pxHeight * padding) / numLines;

  let fontSize = Math.min(fontSizeForWidth, fontSizeForHeight);

  // Clamp to sane bounds so text doesn't disappear or explode.
  fontSize = Math.max(4, Math.min(fontSize, 42));

  return { fontSize, pxWidth, pxHeight };
}

function makeLabelIcon(feature, zoom, bounds) {
  const { fontSize, pxWidth, pxHeight } = computeFontSize(feature, zoom, bounds);
  const text = feature.properties.text || '';

  // Hide labels that would be unreadably small (avoids zoomed-out clutter).
  const visible = fontSize >= 5;

  const html = visible
    ? `<div class="plaque-label" style="font-size:${fontSize.toFixed(1)}px; width:${pxWidth}px; height:${pxHeight}px; display:flex; align-items:center; justify-content:center;">${escapeHtml(text)}</div>`
    : '';

  return L.divIcon({
    className: 'plaque-label-wrapper',
    html: html,
    iconSize: [pxWidth, pxHeight],
    iconAnchor: [pxWidth / 2, pxHeight / 2]
  });
}

function escapeHtml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\n/g, '<br>');
}

function refreshLabels() {
  const zoom = map.getZoom();
  labelMarkers.forEach(({ marker, feature, bounds }) => {
    marker.setIcon(makeLabelIcon(feature, zoom, bounds));
  });
}

fetch('data/plaques.geojson')
  .then(r => r.json())
  .then(data => {
    geojsonLayer = L.geoJSON(data, {
      pane: 'overlayPane',
      style: () => ({ className: 'plaque-polygon' }),
      onEachFeature: (feature, layer) => {
        layer.setStyle({
          color: '#7a0000',
          weight: 1.5,
          fillColor: '#ffcc66',
          fillOpacity: 0.12
        });

        const props = feature.properties;
        layer.bindTooltip(
          `<div class="plaque-tooltip"><b>Fragment #${props.id}</b><br>${escapeHtml(props.text)}</div>`,
          { sticky: true }
        );

        const bounds = layer.getBounds();
        const center = bounds.getCenter();
        const zoom = map.getZoom();
        const marker = L.marker(center, {
          icon: makeLabelIcon(feature, zoom, bounds),
          pane: 'plaqueLabels',
          interactive: false
        });
        labelMarkers.push({ marker, feature, bounds });
      }
    });

    const labelGroup = L.layerGroup(labelMarkers.map(l => l.marker));

    const overlayLayers = {
      'Fragment outlines + transcriptions': L.layerGroup([geojsonLayer, labelGroup]).addTo(map)
    };
    const baseLayers = {
      'Topographic base (from GeoTIFF)': baseImage
    };

    L.control.layers(baseLayers, overlayLayers, { collapsed: false }).addTo(map);

    map.on('zoomend', refreshLabels);
  })
  .catch(err => {
    console.error('Failed to load plaques.geojson', err);
  });
