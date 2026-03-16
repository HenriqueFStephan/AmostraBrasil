"""
Municipality lookup: UF, MUNICIPIO, CODIBGE.
Uses IBGE localidades API (modern) or optional static CSV fallback.
"""

import os
import unicodedata
from pathlib import Path
from typing import Optional

import pandas as pd


def _normalize_name(name: str) -> str:
    """Remove accents and normalize for comparison (e.g. 'São Paulo' and 'sao paulo' match)."""
    if not name:
        return ""
    nfd = unicodedata.normalize("NFD", name.upper().strip())
    return "".join(c for c in nfd if unicodedata.category(c) != "Mn")

# In-memory cache after first load
MUNICIPIOS_IBGE: Optional[pd.DataFrame] = None

# IBGE localidades API (current, recommended)
MUNICIPIOS_API_URL = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios"

# Bundled CSV fallback (valid Brazilian municipalities; geocoding will yield coordinates in Brazil)
_PACKAGE_DIR = Path(__file__).resolve().parent
DEFAULT_CSV_PATH = _PACKAGE_DIR / "data" / "municipios_ibge.csv"


def _safe_get_uf(m: dict) -> str:
    """Extract UF sigla from API item; API structure may have UF under microrregiao or regiao-imediata."""
    for key in ("microrregiao", "regiao-imediata"):
        branch = m.get(key)
        if not isinstance(branch, dict):
            continue
        for key2 in ("mesorregiao", "regiao-intermediaria"):
            branch2 = branch.get(key2)
            if not isinstance(branch2, dict):
                continue
            uf = branch2.get("UF")
            if isinstance(uf, dict):
                sigla = uf.get("sigla")
                if sigla:
                    return sigla
    return ""


def _parse_api_response(data: list) -> pd.DataFrame:
    """Parse JSON from IBGE localidades API into UF, MUNICIPIO, CODIBGE."""
    rows = []
    for m in data:
        if not isinstance(m, dict):
            continue
        uf_sigla = _safe_get_uf(m)
        codibge = str(m.get("id", ""))
        nome = m.get("nome", "") or ""
        rows.append({"UF": uf_sigla, "MUNICIPIO": nome, "CODIBGE": codibge})
    return pd.DataFrame(rows)


def load_municipios(
    use_api: bool = True,
    csv_path: Optional[str] = None,
    force_reload: bool = False,
) -> pd.DataFrame:
    """
    Load Brazilian municipalities (UF, MUNICIPIO, CODIBGE).

    Parameters
    ----------
    use_api : bool
        If True, fetch from IBGE localidades API.
    csv_path : str, optional
        If provided and use_api fails (or use_api=False), load from this CSV
        with columns UF, MUNICIPIO, CODIBGE.
    force_reload : bool
        If True, clear cache and reload.

    Returns
    -------
    pd.DataFrame
        Columns: UF, MUNICIPIO, CODIBGE (CODIBGE as string, 7 chars).
    """
    global MUNICIPIOS_IBGE
    if MUNICIPIOS_IBGE is not None and not force_reload:
        return MUNICIPIOS_IBGE

    if use_api:
        try:
            import requests
            r = requests.get(MUNICIPIOS_API_URL, timeout=30)
            r.raise_for_status()
            MUNICIPIOS_IBGE = _parse_api_response(r.json())
            return MUNICIPIOS_IBGE
        except Exception as e:
            if csv_path is None and DEFAULT_CSV_PATH.is_file():
                csv_path = str(DEFAULT_CSV_PATH)
            elif csv_path is None:
                raise RuntimeError(
                    "Failed to load municipalities from IBGE API and no csv_path provided."
                ) from e

    path_to_try = csv_path or (str(DEFAULT_CSV_PATH) if DEFAULT_CSV_PATH.is_file() else None)
    if path_to_try and os.path.isfile(path_to_try):
        MUNICIPIOS_IBGE = pd.read_csv(path_to_try)
        for col in ("UF", "MUNICIPIO", "CODIBGE"):
            if col not in MUNICIPIOS_IBGE.columns:
                raise ValueError(f"CSV must have columns UF, MUNICIPIO, CODIBGE; missing {col}")
        MUNICIPIOS_IBGE["CODIBGE"] = MUNICIPIOS_IBGE["CODIBGE"].astype(str).str.zfill(7)
        return MUNICIPIOS_IBGE

    raise FileNotFoundError("No municipality data: API failed and csv_path missing or invalid.")


def resolve_municipio(
    codibge: str = "",
    municipio: str = "",
    municipios_df: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """
    Resolve codibge or municipio to one or more rows (UF, MUNICIPIO, CODIBGE).

    Returns
    -------
    pd.DataFrame
        Matching rows. Caller should handle nrow==0 or nrow>1.
    """
    if municipios_df is None:
        municipios_df = load_municipios()
    codibge = (codibge or "").strip()
    municipio = (municipio or "").strip()
    if not codibge and not municipio:
        return pd.DataFrame()
    mask = True
    if codibge:
        mask = mask & (municipios_df["CODIBGE"].astype(str).str.zfill(7) == codibge.zfill(7))
    if municipio:
        # Compare normalized names so "sao paulo" matches "São Paulo"
        norm_query = _normalize_name(municipio)
        norm_col = municipios_df["MUNICIPIO"].astype(str).apply(_normalize_name)
        mask = mask & (norm_col == norm_query)
    return municipios_df.loc[mask].reset_index(drop=True)
