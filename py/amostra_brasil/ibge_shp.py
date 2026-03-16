"""
Download municipality boundary shapefile from IBGE and return as GeoDataFrame.
REMOTE DATA NOTE: FTP path and layer names may have changed since censo_2010.
"""

import os
import tempfile
import zipfile
from pathlib import Path
from typing import Optional, Union

import pandas as pd

# Shapefile URL template (2010 census sectors) - may be outdated
IBGE_SHP_URL_TEMPLATE = (
    "https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/"
    "malhas_de_setores_censitarios__divisoes_intramunicipais/censo_2010/"
    "setores_censitarios_shp/{uf_lower}/{uf_lower}_municipios.zip"
)
# Fallback FTP (some mirrors still use FTP)
IBGE_SHP_FTP_TEMPLATE = (
    "ftp://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/"
    "malhas_de_setores_censitarios__divisoes_intramunicipais/censo_2010/"
    "setores_censitarios_shp/{uf_lower}/{uf_lower}_municipios.zip"
)


def get_ibge_mun_shp(
    codibge: str = "",
    nomemun: str = "",
    municipios_df: Optional[pd.DataFrame] = None,
    out_dir: Optional[Union[str, Path]] = None,
):
    """
    Download municipality boundary (shapefile) from IBGE and return as GeoDataFrame.

    Parameters
    ----------
    codibge : str
        IBGE 7-digit municipality code.
    nomemun : str
        Municipality name (alternative to codibge); used for lookup and output filename.
    municipios_df : pandas.DataFrame, optional
        Table with UF, MUNICIPIO, CODIBGE. If None, load_municipios() is called.
    out_dir : str or Path, optional
        Where to write {nomemun}_lmts.shp. Default: current directory.

    Returns
    -------
    geopandas.GeoDataFrame
        One polygon (or multi) for the municipality, CRS WGS84.

    Remote data note
    ----------------
    URL and zip contents (layer name like 35MUE250GC_SIR) may have changed.
    If download fails, check https://www.ibge.gov.br/ for current malhas.
    """
    import geopandas as gpd

    from .municipios import load_municipios, resolve_municipio

    if municipios_df is None:
        municipios_df = load_municipios()
    mun = resolve_municipio(codibge=codibge, municipio=nomemun, municipios_df=municipios_df)
    if len(mun) == 0:
        raise ValueError(f"Municipality not found: codibge={codibge!r}, nomemun={nomemun!r}")
    if len(mun) > 1:
        raise ValueError(
            f"Multiple municipalities match. Use codibge. Matches:\n{mun.to_string()}"
        )
    row = mun.iloc[0]
    codibge = str(row["CODIBGE"]).zfill(7)
    nomemun = row["MUNICIPIO"]
    uf = row["UF"]
    uf_lower = uf.lower()
    uf_code = codibge[:2]

    url = IBGE_SHP_URL_TEMPLATE.format(uf_lower=uf_lower)
    try:
        import urllib.request
        req = urllib.request.Request(url, headers={"User-Agent": "AmostraBrasil-Python/1.0"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            zip_bytes = resp.read()
    except Exception:
        url_ftp = IBGE_SHP_FTP_TEMPLATE.format(uf_lower=uf_lower)
        import urllib.request
        with urllib.request.urlopen(url_ftp, timeout=120) as resp:
            zip_bytes = resp.read()

    out_dir = Path(out_dir or os.getcwd())
    with tempfile.TemporaryDirectory() as tmp:
        zpath = Path(tmp) / "mun.zip"
        zpath.write_bytes(zip_bytes)
        with zipfile.ZipFile(zpath, "r") as z:
            z.extractall(tmp)
        # Layer name in 2010 format: {uf_code}MUE250GC_SIR (e.g. 35MUE250GC_SIR for SP)
        layer = f"{uf_code}MUE250GC_SIR"
        shp_path = Path(tmp) / f"{layer}.shp"
        if not shp_path.exists():
            # Try first .shp found
            shps = list(Path(tmp).rglob("*.shp"))
            if not shps:
                raise FileNotFoundError(
                    f"No .shp found in zip. IBGE may have changed layer names (expected {layer})."
                )
            shp_path = shps[0]
        gdf = gpd.read_file(shp_path)
        # Subset by municipality code (column name may vary: CD_GEOCODM or similar)
        code_col = None
        for c in ("CD_GEOCODM", "CD_GEOCODU", "codibge", "id"):
            if c in gdf.columns:
                code_col = c
                break
        if code_col is None:
            code_col = gdf.columns[0]
        gdf = gdf[gdf[code_col].astype(str).str.zfill(7) == codibge].copy()
        if gdf.crs is None:
            gdf.set_crs("EPSG:4618", inplace=True)  # SIRGAS 2000 Brazil
        gdf = gdf.to_crs("EPSG:4326")
        out_shp = out_dir / f"{nomemun}_lmts.shp"
        gdf.to_file(out_shp, driver="ESRI Shapefile")
    return gdf
