"""
AmostraBrasil - Python port.

Generates samples or full list of Brazilian IBGE census household addresses,
with optional geocoding (Google Maps) and shapefile output.

Main entry point: amostra_brasil()
"""

from .amostra_brasil import amostra_brasil
from .dir_ftp import dir_ftp
from .geocode import get_geo_code_cs, set_lat_long
from .ibge_shp import get_ibge_mun_shp
from .dentro_fora import set_dentro_fora
from .municipios import load_municipios, resolve_municipio, MUNICIPIOS_IBGE
from .cnefe2022 import fetch_municipio_coords_2022

__all__ = [
    "amostra_brasil",
    "dir_ftp",
    "get_geo_code_cs",
    "set_lat_long",
    "get_ibge_mun_shp",
    "set_dentro_fora",
    "load_municipios",
    "resolve_municipio",
    "MUNICIPIOS_IBGE",
    "fetch_municipio_coords_2022",
]
