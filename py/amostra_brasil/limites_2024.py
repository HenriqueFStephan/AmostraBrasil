"""
Municipality boundaries from IBGE BR_Municipios_2024 (malhas 2024).
Download once, cache on disk and in memory; filter by CD_MUN (7-digit code) for one polygon.
"""

import logging
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

from .municipios import load_municipios, resolve_municipio

log = logging.getLogger(__name__)

# IBGE 2024 – todos os municípios do Brasil
BR_MUNICIPIOS_2024_URL = (
    "https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/"
    "malhas_municipais/municipio_2024/Brasil/BR_Municipios_2024.zip"
)

# In-memory cache: full GeoDataFrame after first load (keyed by cache_dir)
_gdf_cache: Optional[Any] = None
_cache_dir: Optional[Path] = None


def _default_cache_dir() -> Path:
    return Path(__file__).resolve().parent / "data" / "cache_limites"


def _download_zip(url: str, dest: Path, timeout: int = 300) -> None:
    import urllib.request
    log.info("Downloading %s to %s", url, dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "AmostraBrasil-Python/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        dest.write_bytes(resp.read())
    log.info("Download complete: %s", dest)


def _load_full_gdf(cache_dir: Path):
    """Load full BR_Municipios_2024 into a GeoDataFrame (from cache dir or download)."""
    import geopandas as gpd
    zip_path = cache_dir / "BR_Municipios_2024.zip"
    extract_dir = cache_dir / "BR_Municipios_2024"
    extract_dir.mkdir(parents=True, exist_ok=True)
    shps = list(extract_dir.rglob("*.shp"))
    if not shps:
        if not zip_path.exists():
            _download_zip(BR_MUNICIPIOS_2024_URL, zip_path)
        log.info("Extracting BR_Municipios_2024.zip ...")
        with zipfile.ZipFile(zip_path, "r") as z:
            z.extractall(extract_dir)
        shps = list(extract_dir.rglob("*.shp"))
    if not shps:
        raise FileNotFoundError("No .shp found in BR_Municipios_2024.zip")
    gdf = gpd.read_file(shps[0])
    if gdf.crs is None:
        gdf.set_crs("EPSG:4326", inplace=True)
    else:
        gdf = gdf.to_crs("EPSG:4326")
    return gdf


def _get_full_gdf(cache_dir: Optional[Path] = None) -> Any:
    """Return full municipalities GeoDataFrame, using cache if available."""
    global _gdf_cache, _cache_dir
    cache_dir = cache_dir or _default_cache_dir()
    if _gdf_cache is not None and _cache_dir == cache_dir:
        return _gdf_cache
    _gdf_cache = _load_full_gdf(cache_dir)
    _cache_dir = cache_dir
    return _gdf_cache


def _code_column(gdf) -> str:
    """Column that holds 7-digit municipality code (CD_MUN or similar)."""
    for col in ("CD_MUN", "CODIBGE", "code", "id"):
        if col in gdf.columns:
            return col
    return gdf.columns[0]


def get_municipio_limites_2024(
    codibge: str = "",
    municipio: str = "",
    municipios_df: Optional[pd.DataFrame] = None,
    cache_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Return the boundary of one municipality from BR_Municipios_2024 as GeoJSON-like dict.

    Parameters
    ----------
    codibge : str
        IBGE 7-digit code.
    municipio : str
        Municipality name (alternative to codibge).
    municipios_df : pandas.DataFrame, optional
        UF, MUNICIPIO, CODIBGE. If None, load_municipios() is used.
    cache_dir : Path, optional
        Where to store/read BR_Municipios_2024.zip and extracted files.

    Returns
    -------
    dict
        GeoJSON FeatureCollection with one polygon (or MultiPolygon) for the municipio.
        Keys: type, features. Suitable for JSON response and Leaflet GeoJSON layer.
    """
    import geopandas as gpd
    if municipios_df is None:
        municipios_df = load_municipios()
    mun = resolve_municipio(codibge=codibge, municipio=municipio, municipios_df=municipios_df)
    if len(mun) == 0:
        raise ValueError(f"Município não encontrado: codibge={codibge!r}, municipio={municipio!r}")
    if len(mun) > 1:
        raise ValueError("Múltiplos municípios; use codibge para identificar.")
    codibge = str(mun.iloc[0]["CODIBGE"]).zfill(7)
    gdf = _get_full_gdf(cache_dir)
    code_col = _code_column(gdf)
    gdf["_code_str"] = gdf[code_col].astype(str).str.zfill(7)
    one = gdf[gdf["_code_str"] == codibge]
    if len(one) == 0:
        raise ValueError(f"Município {codibge} não encontrado no shapefile BR_Municipios_2024.")
    one = one.drop(columns=["_code_str"], errors="ignore")
    # Return as GeoJSON FeatureCollection (one feature)
    return one.__geo_interface__
