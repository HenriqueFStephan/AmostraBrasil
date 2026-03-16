# AmostraBrasil – Python backend

Python port of the R package **AmostraBrasil**: generate samples or full lists of Brazilian IBGE census household addresses, with optional geocoding (Google Maps) and shapefile output.

## Install

From the repo root or from `py/`:

```bash
pip install -r py/requirements.txt
```

To run tests, install from the repo root and run:

```bash
cd py && pip install -e .  # if you add a pyproject.toml/setup.py
# Or from repo root:
pip install -r py/requirements.txt
python -m pytest py/tests/ -v
```

To use the package without installing, set `PYTHONPATH` so that `amostra_brasil` is importable (e.g. `PYTHONPATH=py python your_script.py`).

## Main functions (mirror of R exports)

| R | Python |
|---|--------|
| `amostraBrasil()` | `amostra_brasil.amostra_brasil()` |
| `dirFTP()` | `dir_ftp.dir_ftp()` |
| `getGeoCodeCS()` | `geocode.get_geo_code_cs()` |
| `setLatLong()` | `geocode.set_lat_long()` |
| `getIBGEMunSHP()` | `ibge_shp.get_ibge_mun_shp()` |
| `setDentroFora()` | `dentro_fora.set_dentro_fora()` |

Municipality list: loaded from **IBGE Localidades API** by default (no key). Optional CSV fallback via `load_municipios(csv_path="...", use_api=False)`.

## Geocoding (Google)

Set your API key:

```bash
export GOOGLE_GEOCODING_API_KEY=your_key
```

Or pass `google_api_key=...` into `amostra_brasil(..., google_api_key="...")` / `get_geo_code_cs(..., api_key="...")`.

## Remote data and possible breakage

See **`REMOTE_DATA.md`** in this directory for:

- Municipality list (API – recommended)
- IBGE FTP for census address files (2010 – may have moved)
- IBGE shapefile URLs (malhas 2010 – path/layer may differ)
- Google Geocoding API (key required, HTTPS)

## Quick test (no key)

```python
from amostra_brasil import load_municipios, resolve_municipio

load_municipios()
print(resolve_municipio(municipio="Pindoba"))
```

## Full sample (with key and network)

```python
from amostra_brasil import amostra_brasil

df = amostra_brasil(
    municipio="Pindoba",
    N=5,
    geocod=True,
    shape=True,
    saveall=True,
    out_dir="./output",
)
print(df)
```
