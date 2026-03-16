# Remote data connections – Python port

This document summarizes **external data sources** used by the AmostraBrasil Python port and migration notes, since the original R package (2016) used endpoints that may have changed.

---

## 1. Municipality list (UF, name, IBGE code)

| Original R | Python port |
|------------|-------------|
| In-package dataset `MUNICIPIOS.IBGE` (LazyData) | **IBGE Localidades API** (recommended) or optional CSV fallback |

- **URL:** `https://servicodados.ibge.gov.br/api/v1/localidades/municipios`
- **Format:** JSON (list of municipalities with `id`, `nome`, nested `UF.sigla`).
- **Status:** Official API; no key required. Prefer this over static CSV.

The Python module `municipios.py` loads from this API by default. If the API is down, you can pass a local CSV with columns `UF`, `MUNICIPIO`, `CODIBGE` to `load_municipios(csv_path="...", use_api=False)`.

---

## 2. Census address files (Cadastro Nacional de Endereços – CNEFE 2010)

| Original R | Python port |
|------------|-------------|
| `ftp://ftp.ibge.gov.br/Censos/Censo_Demografico_2010/Cadastro_Nacional_de_Enderecos_Fins_Estatisticos/{UF}/` | Same base URL in `dir_ftp.DEFAULT_FTP_BASE` |

- **Purpose:** List and download ZIP files containing fixed-width TXT with household addresses per municipality.
- **Risk:** IBGE may have moved or discontinued FTP. Some networks block or restrict FTP.
- **Python:** `dir_ftp()` and `amostra_brasil()` (when `dados=None`) use this. If connection fails, the code raises with a message pointing to this doc.
- **Action:** Check [IBGE Censos](https://www.ibge.gov.br/estatisticas/sociais/trabalho/9662-censo-demografico-2010.html) or [FTP](https://ftp.ibge.gov.br/) for current paths; set a configurable base URL if the structure changes (e.g. HTTPS mirror).

---

## 3. Municipality boundary shapefiles (malhas 2010)

| Original R | Python port |
|------------|-------------|
| `ftp://geoftp.ibge.gov.br/.../censo_2010/setores_censitarios_shp/{uf}/{uf}_municipios.zip` | Same in `ibge_shp.IBGE_SHP_URL_TEMPLATE` (HTTPS first, FTP fallback) |

- **Purpose:** Download municipality polygon(s) to test if geocoded points fall inside the boundary (`set_dentro_fora`).
- **Risk:** Path or zip layout may have changed; layer name inside the zip (e.g. `35MUE250GC_SIR` for SP) is format-dependent and may differ in newer releases.
- **Python:** `get_ibge_mun_shp()` tries HTTPS then FTP; if the zip structure changes, the code looks for any `.shp` inside the zip and subsets by municipality code column (`CD_GEOCODM` or similar).
- **Action:** Confirm current malhas at [IBGE – Organização do território](https://www.ibge.gov.br/geociencias/organizacao-do-territorio/15774-malhas.html).

---

## 4. Google Geocoding API

| Original R | Python port |
|------------|-------------|
| `http://maps.google.com/maps/api/geocode/json?sensor=false&language=pt-BR&address=...` | `https://maps.googleapis.com/maps/api/geocode/json?address=...&language=pt-BR&key=...` |

- **Purpose:** Turn address strings into Lat/Lng (and formatted address, status).
- **Change:** Google **requires an API key** and uses HTTPS. The old “sensor” parameter is obsolete.
- **Python:** `geocode.py` uses the Geocoding API with a key from:
  - argument `api_key` where applicable, or
  - environment variable `GOOGLE_GEOCODING_API_KEY`.
- **Action:** Create a key in [Google Cloud Console](https://console.cloud.google.com/) (Geocoding API), enable billing if required, and set the env var or pass the key. Respect rate limits and terms of use.

---

## 5. Censo 2022 – Coordenadas dos Endereços (CNEFE 2022)

| Use | Python module | URL pattern |
|-----|----------------|-------------|
| Real sample of domicile coordinates per municipality | `cnefe2022.fetch_municipio_coords_2022` | `https://ftp.ibge.gov.br/.../Censo_Demografico_2022/Coordenadas_enderecos/Municipio/{UF_CODE}_{UF}/{codibge}.zip` |

- **Purpose:** One ZIP per municipality containing CSV with `LATITUDE`, `LONGITUDE`, `COD_ESPECIE` (tipo de domicílio: residência, comércio, igreja, etc.), and other fields. No geocoding needed; coordinates are from the census.
- **Folder:** First two digits of codibge + `_` + UF (e.g. `35_SP`, `27_AL`). File: `{codibge}.zip`.
- **Status:** In use; [IBGE FTP listing](https://ftp.ibge.gov.br/Cadastro_Nacional_de_Enderecos_para_Fins_Estatisticos/Censo_Demografico_2022/Coordenadas_enderecos/Municipio/35_SP/) confirms structure.

---

## Summary table

| Component | Used in | URL / source | Likely status |
|-----------|---------|---------------|----------------|
| Municipalities | All functions | IBGE Localidades API | ✅ Prefer API |
| Census address list | `dir_ftp`, `amostra_brasil` | IBGE FTP (2010 CNEFE) | ⚠️ Check current FTP/HTTPS |
| Municipality SHP | `get_ibge_mun_shp`, `amostra_brasil(shape=True)` | geoftp.ibge.gov.br (malhas 2010) | ⚠️ Path/layer may differ |
| Geocoding | `get_geo_code_cs`, `set_lat_long`, `amostra_brasil(geocod=True)` | Google Geocoding API | ✅ Use key + HTTPS |
| Coordenadas 2022 | `cnefe2022.fetch_municipio_coords_2022`, backend API | IBGE FTP Censo 2022 Coordenadas_enderecos/Municipio | ✅ In use |

For a **local React frontend**, the backend can cache municipality list and optionally cache IBGE ZIPs/shapefiles to reduce dependency on remote availability.
