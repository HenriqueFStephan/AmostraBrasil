/**
 * Mock result of amostra_brasil(municipio, N, geocod=true).
 * Returns points within Brazilian territory (approx lat -33.7 to 5.2, lng -73.9 to -34.8).
 * Distribution is deterministic per municipio name so the map looks consistent.
 */

// Brazilian bounding box (mainland + common view)
const BR_BOUNDS = {
  latMin: -33.75,
  latMax: 5.27,
  lngMin: -73.99,
  lngMax: -34.79,
}

// Rough center per state (for clustering mock by UF)
const STATE_CENTERS = {
  AC: [-9.02, -70.81],
  AL: [-9.57, -36.78],
  AM: [-3.47, -65.1],
  AP: [1.41, -51.77],
  BA: [-12.96, -38.51],
  CE: [-3.72, -38.53],
  DF: [-15.83, -47.86],
  ES: [-19.19, -40.34],
  GO: [-15.98, -49.86],
  MA: [-2.53, -44.3],
  MG: [-18.1, -44.38],
  MS: [-20.51, -54.54],
  MT: [-12.64, -55.42],
  PA: [-1.45, -48.49],
  PB: [-7.28, -35.03],
  PE: [-8.38, -37.86],
  PI: [-5.09, -42.8],
  PR: [-24.89, -51.55],
  RJ: [-22.25, -42.66],
  RN: [-5.81, -35.21],
  RO: [-10.83, -63.34],
  RR: [1.99, -61.33],
  RS: [-30.17, -53.5],
  SC: [-27.45, -50.95],
  SE: [-10.57, -37.45],
  SP: [-22.19, -48.79],
  TO: [-9.46, -48.26],
}

function hashStr(str) {
  let h = 0
  for (let i = 0; i < str.length; i++) {
    h = (h << 5) - h + str.charCodeAt(i)
    h |= 0
  }
  return Math.abs(h)
}

/**
 * Generate N mock points for a given municipio.
 * Points are scattered in Brazil; if we recognize the name we cluster near a state center.
 */
export function getMockAmostra(municipio, N = 50) {
  const name = (municipio || '').trim() || 'Brasil'
  const seed = hashStr(name)
  const count = Math.min(Math.max(1, N), 200)

  // Pick a rough center: try to match known cities to state
  let center = [-14.24, -51.93] // Brazil center
  const upper = name.toUpperCase()
  for (const [uf, [lat, lng]] of Object.entries(STATE_CENTERS)) {
    if (upper.includes(uf) || upper.includes('SÃO PAULO') || upper.includes('SAO PAULO')) {
      if (uf === 'SP') {
        center = [-23.55, -46.63]
        break
      }
      if (uf === 'RJ') {
        center = [-22.90, -43.17]
        break
      }
      center = [lat, lng]
      break
    }
  }
  // Known city names -> fixed center
  const cityCenters = {
    PINDOBA: [-9.37, -36.29],
    'SÃO PAULO': [-23.55, -46.63],
    'SAO PAULO': [-23.55, -46.63],
    'RIO DE JANEIRO': [-22.90, -43.17],
    'BELO HORIZONTE': [-19.92, -43.94],
    SALVADOR: [-12.97, -38.51],
    CURITIBA: [-25.43, -49.27],
    'PORTO ALEGRE': [-30.03, -51.22],
    BRASÍLIA: [-15.83, -47.86],
    BRASILIA: [-15.83, -47.86],
    MACEIÓ: [-9.67, -35.74],
    MACEIO: [-9.67, -35.74],
  }
  const key = Object.keys(cityCenters).find((k) => upper.includes(k.replace('Ó', 'O')) || upper === k)
  if (key) center = cityCenters[key]

  const spread = 2.5 + (seed % 30) / 10 // spread in degrees
  const points = []
  const rnd = (s) => {
    s = (s * 9301 + 49297) % 233280
    return s / 233280
  }
  let s = seed
  for (let i = 0; i < count; i++) {
    s = (s * 9301 + 49297) % 233280
    const lat = center[0] + (rnd(s) - 0.5) * spread
    s = (s * 9301 + 49297) % 233280
    const lng = center[1] + (rnd(s) - 0.5) * spread
    const latClamp = Math.max(BR_BOUNDS.latMin, Math.min(BR_BOUNDS.latMax, lat))
    const lngClamp = Math.max(BR_BOUNDS.lngMin, Math.min(BR_BOUNDS.lngMax, lng))
    points.push({
      lat: latClamp,
      lng: lngClamp,
      endIBGE: `Endereço mock ${i + 1}, ${name} - Brasil`,
      setor: String(1000 + (seed % 9000)),
      Status: 'OK',
    })
  }
  return points
}

export { BR_BOUNDS, STATE_CENTERS }
