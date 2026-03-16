import React, { useState } from 'react'
import './TopBar.css'

export default function TopBar({ onSearch, loading }) {
  const [municipio, setMunicipio] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    onSearch(municipio.trim() || 'Brasil')
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
          <button type="submit" className="topbar-btn" disabled={loading}>
            {loading ? 'Gerando…' : 'Gerar amostra'}
          </button>
        </form>
      </div>
    </header>
  )
}
