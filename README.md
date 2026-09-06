# Forma Orange B — Cadastral Fragment Transcription Viewer

A static, GitHub-Pages-ready Leaflet map showing the 82 traced/transcribed
Roman cadastral marble fragments over their georeferenced base map.

## How it works

- **`img/base.jpg`** — the original GeoTIFF (`Fig3_PlaquesB_modified.tif`),
  converted to JPEG for web delivery. It is placed on the map using
  Leaflet's `L.imageOverlay`, anchored to the exact lat/lon bounds read
  from the GeoTIFF's embedded georeferencing tags (EPSG:4326 / WGS84):
  - SW corner: `44.365626838001994, 4.690140138207285`
  - NE corner: `44.44836706961, 4.851866330454634`
- **`data/plaques.geojson`** — the shapefile (`traced grid rome.shp` +
  `.dbf`) converted to GeoJSON. Each polygon carries:
  - `id` — fragment number (1–82)
  - `text` — the transcribed inscription text (multi-line, `\n`-separated)
- **`app.js`** — draws the image as the base layer, the fragment polygons
  as an overlay, and renders each fragment's transcription as a
  monospaced (fixed-width, "Roman-style") text label centered in its
  polygon. Label font size is recalculated on every zoom change from
  each polygon's on-screen pixel size, so text scales naturally with
  both the box size and the zoom level. A Leaflet layer control (top
  right) lets you toggle the transcription layer on/off to compare
  against the bare base map.

## Regenerating the data

If the shapefile or GeoTIFF change, regenerate the site data with the
included pure-Python converters (no GDAL/geopandas dependency required):

```bash
# From the folder containing the .shp/.dbf/.tif files:
python3 read_shp.py "traced grid rome"          # sanity-check the shapefile
python3 read_tiff_tags.py "Fig3_PlaquesB_modified.tif"   # confirm georeferencing tags

# Then re-run the conversion steps used to build site/data/plaques.geojson
# and site/img/base.jpg (see the project notes / conversion script).
```

If you use QGIS, the included `shape layer transcribed.qgz` project can
also export the shapefile to GeoJSON directly (Right-click layer →
Export → Save Features As → GeoJSON), and QGIS can export the raster
via Raster → Conversion → Translate, or simply "Save As" a JPEG.

## Deploying to GitHub Pages

1. Put `index.html`, `app.js`, `img/base.jpg`, and `data/plaques.geojson`
   in the repo (e.g. at the repo root, or in a `/docs` folder).
2. Enable GitHub Pages for that branch/folder in repo Settings → Pages.
3. Leaflet itself is loaded from a CDN in `index.html` — no need to
   vendor the library files into the repo.

## Notes / things to tune

- `CHAR_ASPECT` in `app.js` controls the assumed monospace character
  width:height ratio (0.6 is typical for Courier-like fonts) — adjust
  if labels look too cramped or too sparse.
- The minimum-visible-font-size cutoff (5px) hides labels once they'd
  be illegible when zoomed out; raise/lower this in `makeLabelIcon`.
- `minZoom`/`maxZoom` in `app.js` bound how far users can zoom; adjust
  to taste.
