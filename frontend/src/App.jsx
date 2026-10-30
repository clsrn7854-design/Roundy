import { useEffect, useRef, useState } from 'react'
import { loadKakaoMap } from './lib/kakaoMap.js'
import './App.css'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'
// MVP 대상 지역인 송파구의 석촌호수
const START_CENTER = { lat: 37.5096, lng: 127.1028 }

function App() {
  const mapRef = useRef(null)
  const mapCreated = useRef(false)
  const [mapError, setMapError] = useState(null)
  const [health, setHealth] = useState(null)

  useEffect(() => {
    // 개발 모드(StrictMode)는 effect를 두 번 실행하므로 지도는 한 번만 만든다.
    if (mapCreated.current) return
    mapCreated.current = true
    loadKakaoMap()
      .then((kakao) => {
        const center = new kakao.maps.LatLng(START_CENTER.lat, START_CENTER.lng)
        const map = new kakao.maps.Map(mapRef.current, { center, level: 5 })
        new kakao.maps.Marker({ map, position: center })
      })
      .catch((e) => setMapError(e.message))
  }, [])

  useEffect(() => {
    fetch(`${API_BASE_URL}/health`)
      .then((res) => res.json())
      .then(setHealth)
      .catch(() => setHealth({ status: 'unreachable', services: {} }))
  }, [])

  return (
    <div className="app">
      <header className="app-header">
        <h1>Roundy</h1>
        <p>오늘 뛰기 좋은 우리 동네 한 바퀴</p>
      </header>

      <main className="map-area">
        <div ref={mapRef} className="map" />
        {mapError && <p className="map-error">{mapError}</p>}

        <aside className={`health health-${health?.status ?? 'loading'}`}>
          <strong>API {health ? health.status : '확인 중'}</strong>
          {health &&
            Object.entries(health.services).map(([name, state]) => (
              <span key={name}>
                {name}: {state}
              </span>
            ))}
        </aside>
      </main>
    </div>
  )
}

export default App
