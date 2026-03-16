import React, { useState } from 'react'
import './TopBar.css'

const DEFAULT_N = 50
const MIN_N = 1
const MAX_N = 500

export default function TopBar({ onSearch, loading }) {
  const [municipio, setMunicipio] = useState('')
  const [n, setN] = useState(DEFAULT_N)

  const handleSubmit = (e) => {
    e.preventDefault()
    const mun = municipio.trim() || 'Brasil'
    const sampleSize = Math.min(MAX_N, Math.max(MIN_N, Number(n) || DEFAULT_N))
    onSearch(mun, sampleSize)
  }

  return (
    <header className="topbar">
      <div className="topbar-inner">
        <h1 className="topbar-title">Amostra Brasil</h1>
        <form className="topbar-form" onSubmit={handleSubmit}>
          <input
            type="text"
            className="topbar-input"
            placeholder="Município (ex: Pindoba, São Paulo)"
            value={municipio}
            onChange={(e) => setMunicipio(e.target.value)}
            disabled={loading}
            aria-label="Nome do município"
          />
          <label className="topbar-label-n">
            <span className="topbar-label-n-text">N</span>
            <input
              type="number"
              className="topbar-input-n"
              min={MIN_N}
              max={MAX_N}
              value={n}
              onChange={(e) => setN(e.target.value)}
              disabled={loading}
              aria-label="Tamanho da amostra (domicílios)"
              title={`Tamanho da amostra (${MIN_N}–${MAX_N} domicílios)`}
            />
          </label>
          <button type="submit" className="topbar-btn" disabled={loading}>
            {loading ? 'Gerando…' : 'Gerar amostra'}
          </button>
        </form>
      </div>
    </header>
  )
}
