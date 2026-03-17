import React, { useState, useCallback, useEffect } from 'react'
import TopBar from './components/TopBar'
import MapView from './components/MapView'
import { getMockAmostra } from './data/mockAmostra'
import './App.css'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function App() {
  const [points, setPoints] = useState([])
  const [municipio, setMunicipio] = useState('')
  const [loading, setLoading] = useState(false)
  const [source, setSource] = useState(null) // 'cnefe2022' | 'mock'
  const [limitesGeoJson, setLimitesGeoJson] = useState(null) // boundary polygon for selected municipio
  const [extraLayerGeoJson, setExtraLayerGeoJson] = useState(null) // parks, forests, lakes (e.g. Campinas)
  const [municipiosOptions, setMunicipiosOptions] = useState([])

  useEffect(() => {
    let cancelled = false
    const fetchMunicipios = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/municipios`)
        if (!res.ok) return
        const data = await res.json()
        if (!cancelled && Array.isArray(data)) {
          // Sort by UF then MUNICIPIO for a nicer list
          const sorted = [...data].sort((a, b) => {
            const ufA = (a.uf || '').localeCompare(b.uf || '')
            if (ufA !== 0) return ufA
            return (a.municipio || '').localeCompare(b.municipio || '')
          })
          setMunicipiosOptions(sorted)
        }
      } catch {
        // Ignore; user can still digitar o nome manualmente
      }
    }
    fetchMunicipios()
    return () => {
      cancelled = true
    }
  }, [])

  const handleSearch = useCallback(async (mun, n = 50, codibge = null) => {
    setLoading(true)
    setMunicipio(mun)
    setSource(null)
    setLimitesGeoJson(null)
    setExtraLayerGeoJson(null)
    const sampleSize = Math.min(500, Math.max(1, Number(n) || 50))
    try {
      const params = new URLSearchParams({
        municipio: mun,
        n: String(sampleSize),
      })
      if (codibge) {
        params.append('codibge', String(codibge))
      }
      const res = await fetch(`${API_BASE}/api/amostra?${params.toString()}`)
      if (res.ok) {
        const data = await res.json()
        setPoints(data.points || [])
        setSource(data.source || 'cnefe2022')
        // Fetch municipality boundary to highlight on map (BR_Municipios_2024)
        try {
          const limRes = await fetch(
            `${API_BASE}/api/municipio/limites?municipio=${encodeURIComponent(mun)}`
          )
          if (limRes.ok) {
            const geojson = await limRes.json()
            setLimitesGeoJson(geojson)
          }
        } catch {
          // ignore; map will show points without boundary highlight
        }
        // Extra layer (parks, lakes, forests) — only available for Campinas for now
        try {
          const extraRes = await fetch(
            `${API_BASE}/api/municipio/extra-layer?municipio=${encodeURIComponent(mun)}`
          )
          if (extraRes.ok) {
            const geojson = await extraRes.json()
            setExtraLayerGeoJson(geojson)
          }
        } catch {
          // ignore; no extra layer for this municipio
        }
      } else {
        const result = getMockAmostra(mun, sampleSize)
        setPoints(result)
        setSource('mock')
      }
    } catch {
      const result = getMockAmostra(mun, sampleSize)
      setPoints(result)
      setSource('mock')
    } finally {
      setLoading(false)
    }
  }, [])

  return (
    <div className="app">
      <TopBar
        onSearch={handleSearch}
        loading={loading}
        municipiosOptions={municipiosOptions}
      />
      <div className="app-map-rect">
        <MapView
          points={points}
          municipio={municipio}
          source={source}
          limitesGeoJson={limitesGeoJson}
          extraLayerGeoJson={extraLayerGeoJson}
        />
      </div>
    </div>
  )
}
