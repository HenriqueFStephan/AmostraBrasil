# AmostraBrasil – Main Functions and Testing Guide

This document describes the **user-facing** functions of the AmostraBrasil R package (not internal helpers), what they do, how to test them, and notes for the Python port.

---

## 1. Main functions (exported in NAMESPACE)

### 1.1 `amostraBrasil` (primary entry point)

**File:** `R/getMun.R`

**Purpose:** Generates a sample (or full list) of Brazilian IBGE census household addresses for a municipality, with optional geocoding and shapefile output.

**Parameters:**

| Parameter    | Type   | Default | Description |
|-------------|--------|---------|-------------|
| `codibge`   | string | `""`    | IBGE municipality code (7 digits) |
| `municipio` | string | `""`    | Municipality name (e.g. "Pindoba") |
| `listasetor`| vector | `c()`   | Optional filter: only these census sectors (setores) |
| `N`         | number | `0`     | Sample size; if 0, returns all addresses |
| `geocod`    | bool   | `FALSE` | If TRUE, geocode addresses via Google Maps |
| `shape`     | bool   | `FALSE` | If TRUE (and geocod=TRUE), create point shapefile and flag inside/outside municipality |
| `saveall`   | bool   | `TRUE`  | Save full address list to `{municipio}_domicilios.dbf` |
| `dados`     | frame  | `NULL`  | Pre-loaded data; if NULL, data is fetched from IBGE FTP |

**Behavior (summary):**

1. Resolves municipality from `codibge` or `municipio` using internal `MUNICIPIOS.IBGE` (name/code/UF).
2. If multiple matches, prompts user to choose (interactive).
3. If `dados` is not provided: builds IBGE FTP URL by UF, calls `dirFTP()` to list ZIPs for that municipality, downloads each ZIP, reads fixed-width TXT inside, parses setor/urbrur/endIBGE and keeps only certain address types (espend 01/02).
4. Optionally filters by `listasetor`, then samples `N` rows if `N > 0`.
5. If `geocod=TRUE`: calls `setLatLong()` (Google geocoding), saves `{municipio}_geo.dbf`, keeps only "OK" geocodes.
6. If `shape=TRUE`: gets municipality polygon via `getIBGEMunSHP()`, builds points, calls `setDentroFora()` to mark inside/outside, writes `{municipio}_pts.shp` and related files.
7. Returns the final dataframe (or 0 on cancel/error).

**How to test (R):**

```r
# Minimal: small sample, no geocoding (avoids Google and heavy I/O)
amostraBrasil(municipio = "Pindoba", N = 5, geocod = FALSE, shape = FALSE, saveall = FALSE)

# With geocoding and shape (needs Google API and IBGE FTP/shapefile access)
amostraBrasil(municipio = "Pindoba", N = 5, geocod = TRUE, shape = TRUE)
```

**Return value:** Data frame with columns such as `setor`, `urbrur`, `espend`, `endIBGE`, and if geocoded: `Lat`, `Lng`, `End`, `Status`; if shape: spatial object with `DENTRO` (inside polygon).

---

### 1.2 `dirFTP`

**File:** `R/dirFTP.R`

**Purpose:** Lists files on an IBGE FTP directory and returns only those whose filename starts with the given 7-digit IBGE municipality code.

**Parameters:**

| Parameter | Type   | Default | Description |
|-----------|--------|---------|-------------|
| `myURL`   | string | `""`    | Full FTP URL (e.g. state folder for census address files) |
| `codibge` | string | `""`    | 7-character municipality code; used as `substring(ibgecode, 1, 7)` |

**Behavior:** Uses `RCurl::getURL(..., dirlistonly=TRUE)` to get the directory listing, splits by newline, keeps rows where the filename starts with `codibge`. Returns a one-column dataframe `ibgecode`.

**How to test (R):**

```r
# Example URL format (2010 census address files by state)
url <- "ftp://ftp.ibge.gov.br/Censos/Censo_Demografico_2010/Cadastro_Nacional_de_Enderecos_Fins_Estatisticos/AL/"
dirFTP(myURL = url, codibge = "2704302")  # e.g. code for Maceió area
```

**Return value:** Data frame with column `ibgecode` (filenames).

**Note:** FTP listing format and base URL may have changed; see “Remote data” section.

---

### 1.3 `getGeoCodeCS`

**File:** `R/getGeoCodeCS.R`

**Purpose:** Geocodes a **single** address string using Google Maps Geocoding API (HTTP/JSON).

**Parameters:**

| Parameter | Type   | Description |
|-----------|--------|-------------|
| `gcStr`   | string | Single address string to geocode |

**Behavior:** Encodes string to UTF-8, replaces spaces with `%20`, calls `http://maps.google.com/maps/api/geocode/json?sensor=false&language=pt-BR&address=...`, parses JSON and extracts `lat`, `lng`, `formatted_address`, `status`. Returns named vector: `Lat`, `Lng`, `Ender`, `Status`.

**How to test (R):**

```r
getGeoCodeCS("Rua Augusta, São Paulo, Brasil")
```

**Return value:** Vector with elements `Lat`, `Lng`, `Ender`, `Status`. (Google’s API now requires an API key; see “Remote data”.)

---

### 1.4 `setLatLong`

**File:** `R/setLatLong.R`

**Purpose:** Batch geocoding: for each value in an address column, calls `getGeoCodeCS()` and appends columns `Lat`, `Lng`, `End`, `Status` to the dataframe.

**Parameters:**

| Parameter    | Type    | Description |
|-------------|---------|-------------|
| `datafr`    | dataframe | Table to which geocoding results will be appended |
| `addresscol`| vector    | Address strings (same length as `datafr` rows) |

**Behavior:** `sapply(addresscol, getGeoCodeCS)`, then binds results as four new columns to `datafr`.

**How to test (R):**

```r
df <- data.frame(endIBGE = c("Rua A, São Paulo", "Av. Paulista, São Paulo"))
setLatLong(df, df$endIBGE)
```

**Return value:** Original dataframe plus `Lat`, `Lng`, `End`, `Status`.

---

### 1.5 `getIBGEMunSHP`

**File:** `R/getIBGEMunSHP.R`

**Purpose:** Downloads the municipality boundary (shapefile) from IBGE FTP and returns it as a spatial object (and writes a local SHP).

**Parameters:**

| Parameter | Type   | Default | Description |
|-----------|--------|---------|-------------|
| `codibge` | string | `""`    | IBGE municipality code |
| `nomemun` | string | `""`    | Municipality name (alternative to code) |

**Behavior:** Looks up municipality in `MUNICIPIOS.IBGE` to get code/name/UF. Builds URL to `ftp://geoftp.ibge.gov.br/.../censo_2010/setores_censitarios_shp/{uf}/{uf}_municipios.zip`, downloads and unzips. Reads layer `{ufCode}MUE250GC_SIR`, subsets to `CD_GEOCODM == codibge`, reprojects to WGS84, writes `{nomemun}_lmts.shp`, returns the spatial polygon object.

**How to test (R):**

```r
getIBGEMunSHP(codibge = "2704302")
# or
getIBGEMunSHP(nomemun = "Maceió")
```

**Return value:** Spatial polygon object (SP) in WGS84.

**Note:** FTP path and layer names may have changed; see “Remote data”.

---

### 1.6 `setDentroFora`

**File:** `R/setDentroFora.R`

**Purpose:** For a set of points (spatial) and a polygon (municipality limits), marks each point as inside or outside the polygon and optionally plots.

**Parameters:**

| Parameter | Type   | Description |
|-----------|--------|-------------|
| `pontos`  | SpatialPointsDataFrame | Point layer (e.g. geocoded addresses) |
| `limites` | SpatialPolygons(DataFrame) | Municipality boundary |

**Behavior:** Uses `sp::over(pontos, as(limites, "SpatialPolygons"))`; non-NA means inside. Adds column `DENTRO` (TRUE/FALSE). Plots `limites`, then points (blue = inside, red = outside). Returns `pontos` with `DENTRO` column.

**How to test (R):** Requires building points and polygon first (e.g. via `amostraBrasil(..., geocod=TRUE, shape=TRUE)` or manually with `sp`).

**Return value:** Same `pontos` with `@data$DENTRO` added.

---

## 2. Data dependency (not a “function” but required)

- **`MUNICIPIOS.IBGE`:** Internal dataset of Brazilian municipalities: `UF`, `MUNICIPIO`, `CODIBGE`. Loaded with the package (LazyData). In the repo there is no `data/` or `sysdata.rda` in the copy we inspected; the package may expect it to be built at install time or shipped in the built tarball. For Python you will need an equivalent table (e.g. CSV or fetch from IBGE API).

---

## 3. Remote data connections – migration notes

These are **old** endpoints; they may be moved, require HTTPS, or have different structure.

| Component | What it does | Old URL / API | Risk / suggestion |
|-----------|--------------|---------------|-------------------|
| **Census address files** | List and download ZIPs per municipality | `ftp://ftp.ibge.gov.br/Censos/Censo_Demografico_2010/Cadastro_Nacional_de_Enderecos_Fins_Estatisticos/{UF}/` | FTP may be deprecated or path changed; prefer HTTPS or official API if available. |
| **dirFTP** | List files on that FTP | Same base URL | Same as above; directory listing format may differ. |
| **Municipality shapefiles** | Download SHP of census sectors / municipalities | `ftp://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/.../censo_2010/setores_censitarios_shp/{uf}/{uf}_municipios.zip` | Path and file names may have changed; check [IBGE downloads](https://www.ibge.gov.br/). |
| **getIBGEMunSHP** | Unzip and read layer `{ufCode}MUE250GC_SIR` | After unzipping in current dir | Layer name is format-dependent; may differ in newer releases. |
| **Google Geocoding** | Geocode one address | `http://maps.google.com/maps/api/geocode/json?sensor=false&language=pt-BR&address=...` | **Requires API key** now; use Geocoding API with key and HTTPS. Rate limits and terms apply. |

**Recommendations for Python backend:**

1. **Municipalities:** Ship a static CSV (UF, MUNICIPIO, CODIBGE) or use IBGE’s localidades API to resolve name/code.
2. **Census addresses:** Check current IBGE FTP/HTTPS structure; add a configurable base URL and fallback or error message if connection fails.
3. **Shapefiles:** Check current IBGE geographic downloads; make layer name and subfolder configurable.
4. **Geocoding:** Use `requests` (or similar) with Google Geocoding API key in env/config; do not hardcode keys.

---

## 4. Suggested test order (for R or Python)

1. **Municipality lookup** – Resolve "Pindoba" or a known code to one row (UF, CODIBGE, MUNICIPIO).
2. **dirFTP** – List files for one municipality (may fail if FTP is down or path changed).
3. **getIBGEMunSHP** – Download one municipality shapefile (may fail if URL/layer changed).
4. **getGeoCodeCS** – One address (will fail without valid Google API key).
5. **setLatLong** – Small dataframe with 1–2 addresses (same API key requirement).
6. **setDentroFora** – With synthetic points and polygon (no network).
7. **amostraBrasil** – Without geocoding/shape first (`N=5`, `geocod=FALSE`, `shape=FALSE`, `saveall=FALSE`); then add geocoding/shape if endpoints and API key are set.

This order isolates network and API issues from pure logic.

---

## 5. Python port – where to test

The Python backend lives under `py/`:

- **Package:** `py/amostra_brasil/`
- **Entry point:** `amostra_brasil.amostra_brasil()`
- **Tests:** `py/tests/test_amostra_brasil.py` (pytest)

Suggested test order (Python):

1. **Municipality lookup** – `load_municipios()` then `resolve_municipio(municipio="Pindoba")` (uses IBGE API).
2. **dir_ftp** – `dir_ftp(my_url=..., codibge="2704302")` (may fail if FTP is down or path changed).
3. **get_ibge_mun_shp** – `get_ibge_mun_shp(codibge="2704302")` (downloads shapefile).
4. **get_geo_code_cs** – Requires `GOOGLE_GEOCODING_API_KEY`; otherwise raises.
5. **set_dentro_fora** – Unit test with synthetic points/polygon (no network).
6. **amostra_brasil** – Start with `amostra_brasil(municipio="Pindoba", N=5, geocod=False, shape=False, saveall=False)` then add geocoding if key is set.

Remote data and key requirements are documented in `py/REMOTE_DATA.md`.
