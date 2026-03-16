# Amostra Brasil – Frontend

React app: top bar (município input) + map showing a **mocked** distribution of `amostra_brasil`-style points in Brazil.

## Run

From **project root** (after installing frontend deps once):

```bash
npm run install:frontend
npm start
```

Or from this folder:

```bash
npm install
npm start
```

Opens at **http://localhost:5173** (or next free port). Enter a municipality name (e.g. *Pindoba*, *São Paulo*) and click **Gerar amostra** to see mock points on the map. Data is fully mocked; no Python backend or real IBGE/geocoding calls.
