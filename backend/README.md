# Amostra Brasil – API

Serves **real** address coordinates from [IBGE Censo 2022 – Coordenadas dos Endereços](https://ftp.ibge.gov.br/Cadastro_Nacional_de_Enderecos_para_Fins_Estatisticos/Censo_Demografico_2022/Coordenadas_enderecos/Municipio/): one ZIP per municipality (e.g. `35_SP/3550308.zip`) containing CSV with `LATITUDE`, `LONGITUDE`, `COD_ESPECIE` (tipo de domicílio), etc.

## Run

From **project root**:

```powershell
# Install deps once
pip install -r py/requirements.txt
pip install fastapi uvicorn

# Start API (PowerShell)
npm run start:api
# or directly:
.\backend\start.ps1
```

Or manually: `$env:PYTHONPATH = "py"; uvicorn backend.main:app --reload --port 8000`

Then open the frontend (`npm start`); it will call `http://localhost:8000/api/amostra?municipio=...&n=50`. If the API is down or returns an error, the frontend falls back to **mock** data.

## Endpoints

- **GET /api/amostra?municipio=...&n=50** – Returns `{ municipio, points: [{ lat, lng, tipo, endIBGE, setor, Status }], source: "cnefe2022", total }`. Uses IBGE 2022 ZIP/CSV for the given municipality and samples up to `n` points.
- **GET /api/health** – Health check.

## CORS

Allowed origins include `http://localhost:5173` and `http://localhost:5174` so the Vite frontend can call the API.
