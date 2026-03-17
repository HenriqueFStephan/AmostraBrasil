"""
FastAPI backend for Amostra Brasil.
Serves real 2022 CNEFE coordinates; frontend can fall back to mock on error.
"""

import logging
import sys
from pathlib import Path

# Allow importing amostra_brasil when running from repo root or backend/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "py"))

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

app = FastAPI(title="Amostra Brasil API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://127.0.0.1:5173", "http://127.0.0.1:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/amostra")
def get_amostra(
    municipio: str = Query(..., description="Nome do município (ex: São Paulo, Pindoba)"),
    n: int = Query(50, ge=1, le=500, description="Número de pontos na amostra (1–500)"),
    codibge: str | None = Query(
        None,
        min_length=7,
        max_length=7,
        description="Código de município IBGE (7 dígitos, opcional)",
    ),
):
    """
    Return a sample of address coordinates for the given municipality.
    Uses IBGE Censo 2022 – Coordenadas dos Endereços (ZIP/CSV per municipio).

    Prefer using codibge when available to evitar ambiguidade de nomes.
    """
    log.info("GET /api/amostra municipio=%r codibge=%r n=%s", municipio, codibge, n)
    try:
        from amostra_brasil import fetch_municipio_coords_2022
        points = fetch_municipio_coords_2022(
            codibge=codibge or "",
            municipio=municipio,
            n_sample=n,
        )
    except ValueError as e:
        log.warning("amostra 404: municipio=%r error=%s", municipio, e)
        detail = str(e)
        # Suggest similar names for typos (e.g. Pindona -> Pindoba)
        try:
            from amostra_brasil.municipios import load_municipios, _normalize_name
            df = load_municipios()
            q = _normalize_name(municipio)
            if len(q) >= 3:
                norm = df["MUNICIPIO"].astype(str).apply(_normalize_name)
                starts = df[norm.str.startswith(q[:4])]
                contains = df[norm.str.contains(q[:4], na=False)]
                suggest = starts.head(3) if len(starts) else contains.head(3)
                if len(suggest):
                    names = [f"{r['MUNICIPIO']} ({r['UF']})" for _, r in suggest.iterrows()]
                    detail += f" Sugestão: {', '.join(names)}"
        except Exception:
            pass
        raise HTTPException(status_code=404, detail=detail)
    except Exception as e:
        log.exception("amostra 502: municipio=%r", municipio)
        raise HTTPException(status_code=502, detail=f"Erro ao obter dados do IBGE: {e}")
    if not points:
        log.warning("amostra 404: municipio=%r retornou 0 pontos", municipio)
        raise HTTPException(status_code=404, detail="Nenhum endereço encontrado para este município.")
    log.info("amostra OK: municipio=%r points=%s", municipio, len(points))
    # Normalize for frontend: ensure endIBGE-like and setor for popup
    out = []
    for i, p in enumerate(points):
        row = {
            "lat": p["lat"],
            "lng": p["lng"],
            "tipo": p.get("tipo"),
            "endIBGE": p.get("endereco") or p.get("endereco_completo") or f"Endereço {i + 1}, {municipio}",
            "setor": p.get("setor") or p.get("cod_setor"),
            "Status": "OK",
        }
        out.append(row)
    return {"municipio": municipio, "points": out, "source": "cnefe2022", "total": len(out)}


@app.get("/api/municipio/limites")
def get_limites(
    municipio: str = Query(..., description="Nome do município (ex: Hortolândia, São Paulo)"),
):
    """
    Return the boundary of the municipality as GeoJSON (from BR_Municipios_2024).
    Used to highlight the selected municipio polygon on the map.
    First call may take a while (download ~199MB shapefile); then cached.
    """
    log.info("GET /api/municipio/limites municipio=%r", municipio)
    cache_dir = Path(__file__).resolve().parent.parent / "py" / "amostra_brasil" / "data" / "cache_limites"
    try:
        from amostra_brasil.limites_2024 import get_municipio_limites_2024
        geojson = get_municipio_limites_2024(municipio=municipio, cache_dir=cache_dir)
    except ValueError as e:
        log.warning("limites 404: municipio=%r error=%s", municipio, e)
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        log.exception("limites 502: municipio=%r", municipio)
        raise HTTPException(status_code=502, detail=f"Erro ao obter limites: {e}")
    return geojson


def _normalize_municipio_name(name: str) -> str:
    """Normalize for comparison (no accents, upper, strip)."""
    import unicodedata
    if not name:
        return ""
    nfd = unicodedata.normalize("NFD", name.upper().strip())
    return "".join(c for c in nfd if unicodedata.category(c) != "Mn")


@app.get("/api/municipio/extra-layer")
def get_extra_layer(
    municipio: str = Query(..., description="Nome do município (ex: Campinas)"),
):
    """
    Return extra map layer (parks, forests, lakes) as GeoJSON when available for the municipality.
    Currently only Campinas has data (parques, bosques, mata); other municipalities return 404.
    Data source: Prefeitura de Campinas (metadados geoespaciais); static file for now.
    """
    log.info("GET /api/municipio/extra-layer municipio=%r", municipio)
    norm = _normalize_municipio_name(municipio)
    if norm != "CAMPINAS":
        raise HTTPException(
            status_code=404,
            detail="Camada extra (parques, lagos, bosques) disponível apenas para Campinas no momento.",
        )
    data_dir = Path(__file__).resolve().parent / "data" / "campinas"
    geojson_path = data_dir / "areas_verdes.geojson"
    if not geojson_path.is_file():
        log.warning("extra-layer: file not found %s", geojson_path)
        raise HTTPException(status_code=404, detail="Dados de áreas verdes de Campinas não encontrados.")
    import json
    try:
        geojson = json.loads(geojson_path.read_text(encoding="utf-8"))
    except Exception as e:
        log.exception("extra-layer: read error")
        raise HTTPException(status_code=502, detail=f"Erro ao ler GeoJSON: {e}")
    return geojson


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/municipios")
def list_municipios():
    """
    Return list of municipalities (UF, MUNICIPIO, CODIBGE) for frontend autocomplete.
    Uses cached IBGE localidades API when available; falls back to bundled CSV.
    """
    try:
        from amostra_brasil.municipios import load_municipios

        try:
            df = load_municipios(use_api=True)
        except Exception:
            df = load_municipios(use_api=False)

        rows = []
        for _, r in df.iterrows():
            uf = str(r.get("UF", "")).strip()
            mun = str(r.get("MUNICIPIO", "")).strip()
            codibge = str(r.get("CODIBGE", "")).zfill(7)
            if not uf or not mun:
                continue
            rows.append({"uf": uf, "municipio": mun, "codibge": codibge})
        return JSONResponse(content=rows)
    except Exception as e:
        log.exception("erro ao listar municipios")
        raise HTTPException(status_code=502, detail=f"Erro ao listar municípios: {e}")
