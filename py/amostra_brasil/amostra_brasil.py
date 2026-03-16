"""
Main entry point: generate IBGE census household sample for a Brazilian municipality.
"""

import os
import zipfile
from io import BytesIO
from pathlib import Path
from typing import List, Optional, Union

import pandas as pd

from .municipios import load_municipios, resolve_municipio
from .dir_ftp import dir_ftp, DEFAULT_FTP_BASE
from .geocode import set_lat_long
from .ibge_shp import get_ibge_mun_shp
from .dentro_fora import set_dentro_fora


def _parse_ibge_address_line(line: str, codibge: str) -> dict:
    """Parse one fixed-width line from IBGE address TXT (2010 format)."""
    def s(a: int, b: int) -> str:
        return line[a - 1 : b].strip() if len(line) >= b else ""
    setor = (
        s(8, 9).replace(" ", "0") + s(10, 11).replace(" ", "0") + s(12, 15).replace(" ", "0")
    )
    urbrur = s(16, 16)
    espend = s(472, 473)
    # CEP: special case São Paulo 3550308
    if codibge == "3550308" and line:
        cep_part = "0" + s(551, 554) + "-" + s(555, 557)
    else:
        cep_part = s(551, 555) + "-" + s(556, 558)
    endIBGE = (
        s(17, 36) + " "
        + (s(37, 66) + " " if s(37, 66) else "")
        + s(67, 126) + ", "
        + s(127, 134) + " "
        + cep_part
    )
    return {"setor": setor, "urbrur": urbrur, "espend": espend, "endIBGE": endIBGE}


def _download_zip(url: str) -> bytes:
    """Download ZIP from URL (FTP or HTTP)."""
    import urllib.request
    with urllib.request.urlopen(url, timeout=60) as resp:
        return resp.read()


def _fetch_dados_ibge(
    uf: str,
    codibge: str,
    municipio: str,
    base_url: str = DEFAULT_FTP_BASE,
) -> pd.DataFrame:
    """Download and parse all address TXT files for the municipality from IBGE FTP."""
    my_url = f"{base_url.rstrip('/')}/{uf}/"
    try:
        file_list = dir_ftp(my_url=my_url, codibge=codibge)
    except Exception as e:
        raise RuntimeError(
            "Failed to list IBGE FTP. Census address base URL may have changed (see REMOTE_DATA.md)."
        ) from e
    if not file_list:
        return pd.DataFrame(columns=["setor", "urbrur", "espend", "endIBGE"])

    all_dfs = []
    for i, filename in enumerate(file_list):
        zip_url = my_url + filename
        try:
            zip_bytes = _download_zip(zip_url)
        except Exception as e:
            raise RuntimeError(f"Failed to download {zip_url}") from e
        # TXT name: first 11 chars of ZIP name + .TXT
        txt_name = filename[:11] + ".TXT" if not filename.upper().endswith(".TXT") else filename
        with zipfile.ZipFile(BytesIO(zip_bytes), "r") as z:
            try:
                with z.open(txt_name) as f:
                    lines = f.read().decode("latin-1").splitlines()
            except KeyError:
                names = [n for n in z.namelist() if n.upper().endswith(".TXT")]
                if not names:
                    continue
                with z.open(names[0]) as f:
                    lines = f.read().decode("latin-1").splitlines()
        rows = []
        for line in lines:
            if len(line) < 470:
                continue
            row = _parse_ibge_address_line(line, codibge)
            if row["espend"] not in ("01", "02"):
                continue
            rows.append(row)
        if rows:
            all_dfs.append(pd.DataFrame(rows))
    if not all_dfs:
        return pd.DataFrame(columns=["setor", "urbrur", "espend", "endIBGE"])
    dados = pd.concat(all_dfs, ignore_index=True)
    dados["endIBGE"] = dados["endIBGE"] + ", " + municipio + " - " + uf + ", Brasil"
    return dados


def amostra_brasil(
    codibge: str = "",
    municipio: str = "",
    listasetor: Optional[List[str]] = None,
    N: int = 0,
    geocod: bool = False,
    shape: bool = False,
    saveall: bool = True,
    dados: Optional[pd.DataFrame] = None,
    out_dir: Optional[Union[str, Path]] = None,
    google_api_key: Optional[str] = None,
    municipio_index: Optional[int] = None,
) -> pd.DataFrame:
    """
    Generate Brazil IBGE household sample (or full list) for a municipality.

    Parameters
    ----------
    codibge : str
        IBGE 7-digit municipality code.
    municipio : str
        Municipality name (e.g. "Pindoba"). One of codibge or municipio required.
    listasetor : list of str, optional
        If provided, keep only addresses in these census sectors.
    N : int
        Sample size. If 0, return all addresses.
    geocod : bool
        If True, geocode addresses via Google Maps (requires API key).
    shape : bool
        If True and geocod True, create point shapefile and add DENTRO (inside polygon).
    saveall : bool
        If True, save full address list to CSV (Python port uses CSV instead of DBF).
    dados : pandas.DataFrame, optional
        Pre-loaded address data. If None, data is fetched from IBGE FTP.
    out_dir : str or Path, optional
        Output directory for saved files. Default: current directory.
    google_api_key : str, optional
        Google Geocoding API key. If not set, uses env GOOGLE_GEOCODING_API_KEY.
    municipio_index : int, optional
        If multiple municipalities match the name, use this 1-based index to choose.
        If None and multiple matches, raises ValueError (no interactive prompt in lib).

    Returns
    -------
    pandas.DataFrame
        Addresses (and Lat/Lng/Status if geocod). Returns empty DataFrame on error.
    """
    listasetor = listasetor or []
    out_dir = Path(out_dir or os.getcwd())
    mun_df = load_municipios()
    my_mun = resolve_municipio(codibge=codibge, municipio=municipio, municipios_df=mun_df)

    if len(my_mun) == 0:
        raise ValueError("Cidade não encontrada! Verifique o nome ou o código do município no IBGE.")
    if len(my_mun) > 1:
        if municipio_index is None:
            raise ValueError(
                f"Multiple municipalities named {municipio}. Pass municipio_index (1-based) or use codibge. "
                f"Options:\n{my_mun[['UF', 'CODIBGE']].to_string()}"
            )
        if municipio_index < 1 or municipio_index > len(my_mun):
            raise ValueError("Número inválido para municipio_index.")
        my_mun = my_mun.iloc[[municipio_index - 1]]
    row = my_mun.iloc[0]
    codibge = str(row["CODIBGE"]).zfill(7)
    municipio = row["MUNICIPIO"]
    uf = row["UF"]

    if dados is None or not isinstance(dados, pd.DataFrame):
        print(f"Aguarde! Conectando IBGE... Buscando dados de {municipio}/{uf} ({codibge})")
        dados = _fetch_dados_ibge(uf=uf, codibge=codibge, municipio=municipio)
        if dados.empty:
            return pd.DataFrame()
        print(f"Configurando o arquivo... {municipio}")
        n = len(dados)
        print(f"Gerados {n} registros com sucesso!")
        if saveall:
            out_path = out_dir / f"{municipio}_domicilios.csv"
            dados.to_csv(out_path, index=False, encoding="utf-8-sig")
    else:
        n = len(dados)

    if listasetor:
        dados = dados[dados["setor"].isin(listasetor)].copy()

    if N > 0 and len(dados) > 0:
        dados = dados.sample(n=min(N, len(dados)), replace=False).reset_index(drop=True)
        n = len(dados)

    if geocod:
        print("Aguarde... geocodificando endereços via Google Maps.")
        dados = set_lat_long(dados, dados["endIBGE"].tolist(), api_key=google_api_key)
        out_dir.mkdir(parents=True, exist_ok=True)
        dados.to_csv(out_dir / f"{municipio}_geo.csv", index=False, encoding="utf-8-sig")
        n_before = len(dados)
        dados = dados[dados["Status"] == "OK"].copy()
        print(f"Foram descartados {n_before - len(dados)} registros não geocodificados!")
        if dados.empty:
            print(f"Nenhum registro geocodificado! Verifique o arquivo {municipio}_geo.csv")
            return dados
        if shape and len(dados) > 0:
            import geopandas as gpd
            from shapely.geometry import Point
            lmts = get_ibge_mun_shp(codibge=codibge, out_dir=out_dir, municipios_df=mun_df)
            geom = [Point(lng, lat) for lng, lat in zip(dados["Lng"], dados["Lat"])]
            pts = gpd.GeoDataFrame(
                dados.assign(geometry=geom),
                geometry="geometry",
                crs="EPSG:4326",
            )
            pts = set_dentro_fora(pts, lmts, plot=False)
            out_shp = out_dir / f"{municipio}_pts.shp"
            pts.to_file(out_shp, driver="ESRI Shapefile")
            print(f"Foram criados o arquivo {municipio}_pts.shp e componentes em {out_dir}")

    return dados
