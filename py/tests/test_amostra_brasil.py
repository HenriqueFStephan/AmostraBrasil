"""
Tests for amostra_brasil (Python port).
Run: pytest py/tests/ -v
Or run individual examples below without network (except where noted).
"""

import os
import sys

import pytest

# Add py/ so "amostra_brasil" package is importable (run from repo root: pytest py/tests/)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def test_load_municipios():
    """Load municipalities from IBGE API (requires network)."""
    from amostra_brasil import load_municipios
    df = load_municipios()
    assert "UF" in df.columns and "MUNICIPIO" in df.columns and "CODIBGE" in df.columns
    assert len(df) > 5000
    pindoba = df[df["MUNICIPIO"].str.upper() == "PINDOBA"]
    assert len(pindoba) >= 1
    assert pindoba.iloc[0]["UF"] == "AL"


def test_resolve_municipio():
    """Resolve by name and by code."""
    from amostra_brasil.municipios import load_municipios, resolve_municipio
    load_municipios()
    r = resolve_municipio(municipio="Pindoba")
    assert len(r) >= 1
    cod = r.iloc[0]["CODIBGE"]
    r2 = resolve_municipio(codibge=cod)
    assert len(r2) == 1 and r2.iloc[0]["MUNICIPIO"] == r.iloc[0]["MUNICIPIO"]


def test_get_geo_code_cs_skip_without_key():
    """Without API key, get_geo_code_cs should raise."""
    from amostra_brasil import get_geo_code_cs
    key = os.environ.pop("GOOGLE_GEOCODING_API_KEY", None)
    try:
        with pytest.raises(ValueError, match="API key"):
            get_geo_code_cs("Rua Augusta, São Paulo, Brasil")
    finally:
        if key is not None:
            os.environ["GOOGLE_GEOCODING_API_KEY"] = key


def test_set_dentro_fora():
    """Point-in-polygon without network (synthetic geometry)."""
    import geopandas as gpd
    from shapely.geometry import Point, Polygon
    from amostra_brasil import set_dentro_fora
    poly = Polygon([(0, 0), (2, 0), (2, 2), (0, 2)])
    limites = gpd.GeoDataFrame({"id": [1]}, geometry=[poly], crs="EPSG:4326")
    pts = gpd.GeoDataFrame(
        {"name": ["inside", "outside"]},
        geometry=[Point(1, 1), Point(5, 5)],
        crs="EPSG:4326",
    )
    out = set_dentro_fora(pts, limites, plot=False)
    assert out["DENTRO"].iloc[0] is True
    assert out["DENTRO"].iloc[1] is False


@pytest.mark.skipif(
    not os.environ.get("GOOGLE_GEOCODING_API_KEY"),
    reason="GOOGLE_GEOCODING_API_KEY not set",
)
def test_geocode_one():
    """Geocode one address (requires API key)."""
    from amostra_brasil import get_geo_code_cs
    r = get_geo_code_cs("Rua Augusta, São Paulo, Brasil")
    assert r["Status"] == "OK"
    assert -24 < r["Lat"] < -23 and -47 < r["Lng"] < -46


# Optional: integration test that hits IBGE FTP (slow, may fail if FTP changed)
@pytest.mark.skip(reason="Requires IBGE FTP; run manually if needed")
def test_dir_ftp():
    """List files on IBGE FTP for one municipality."""
    from amostra_brasil import dir_ftp
    url = "ftp://ftp.ibge.gov.br/Censos/Censo_Demografico_2010/Cadastro_Nacional_de_Enderecos_Fins_Estatisticos/AL/"
    files = dir_ftp(my_url=url, codibge="2704302")
    assert isinstance(files, list)
    # May be empty if path changed
    for f in files:
        assert f.startswith("2704302")
