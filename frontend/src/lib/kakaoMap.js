// 카카오맵 JS SDK를 한 번만 불러온다. 키는 루트 .env의 VITE_KAKAO_JS_KEY.
let loading

export function loadKakaoMap() {
  if (window.kakao?.maps?.LatLng) return Promise.resolve(window.kakao)
  if (loading) return loading

  const key = import.meta.env.VITE_KAKAO_JS_KEY
  if (!key) return Promise.reject(new Error('VITE_KAKAO_JS_KEY가 .env에 없습니다.'))

  loading = new Promise((resolve, reject) => {
    const script = document.createElement('script')
    script.src = `https://dapi.kakao.com/v2/maps/sdk.js?appkey=${key}&autoload=false`
    script.onload = () => window.kakao.maps.load(() => resolve(window.kakao))
    script.onerror = () => {
      loading = undefined
      reject(new Error('카카오맵 SDK를 불러오지 못했습니다. 키와 등록된 도메인을 확인하세요.'))
    }
    document.head.appendChild(script)
  })
  return loading
}
