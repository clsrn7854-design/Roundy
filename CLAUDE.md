# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Roundy는 출발지와 거리를 정하면 출발지로 돌아오는 러닝 코스를 추천하고, 날씨·대기질로 러닝 지수를 알려주는 반응형 웹 서비스다. MVP 대상은 서울 송파구. 요구사항(FR-xx), 데이터 모델, API 초안, 핵심 로직은 모두 [docs/기획서.md](docs/기획서.md)에 있다. 사용자와는 한국어로 대화한다.

## 작업 규칙

- 기획서의 P0 기능만 구현한다. P1은 사용자가 요청할 때만 만든다.
- 새 라이브러리 설치, DB 스키마 변경, 데이터 삭제 전에는 반드시 먼저 묻는다.
- 외부 API와 LLM은 테스트에서 mock으로 대체한다. 실제 LLM API를 호출하는 테스트는 만들지 않는다.
- 외부 API를 반복문에서 호출하지 않는다. 개발 중에는 응답을 파일로 저장해 재사용한다. 크롤링은 하지 않는다.
- 코드를 작성한 뒤 핵심 로직을 짧게 설명한다. 사용자가 면접에서 설명할 수 있어야 한다.
- 커밋은 사용자가 요청할 때만 한다. 커밋 메시지는 `docs:`, `feat:`, `fix:` 같은 접두어와 한국어 설명을 쓴다.
- 기능 개발 순서: `docs/specs/_template.md`를 복사해 명세를 먼저 쓰고(SDD), 명세의 완료 조건을 테스트로 먼저 옮긴다(TDD). 단, 1주차 순환 코스 시제품 같은 실험 코드는 예외다.

## 명령어

백엔드는 **반드시 Docker 컨테이너 안에서** 실행한다. 이 PC는 Windows 스마트 앱 컨트롤이 켜져 있어 pip로 받은 네이티브 DLL(`pydantic_core` 등)이 차단된다. `backend/.venv`는 에디터 자동완성용일 뿐 실행되지 않는다.

```bash
docker compose up -d --build          # 백엔드 + PostgreSQL(PostGIS) + Neo4j + Redis
docker compose logs -f backend        # 백엔드 로그
docker compose exec backend pytest                                   # 전체 테스트
docker compose exec backend pytest tests/test_health.py::test_health_all_ok   # 테스트 하나
docker compose exec backend ruff check .
docker compose exec backend ruff format .

cd frontend
npm run dev      # http://localhost:5173
npm run build
npm run lint     # oxlint
```

- 백엔드 코드는 볼륨(`./backend:/app`)으로 연결돼 있고 `uvicorn --reload`가 polling으로 변경을 감지한다. 코드 수정은 재빌드가 필요 없다.
- 백엔드 패키지 추가: `backend/requirements.in`에 이름을 적고 `requirements.txt`에 `==` 버전으로 고정한 뒤 `docker compose up -d --build`. 개발 도구는 `requirements-dev.txt`.
- 이 셸에서 `docker`를 못 찾으면 PATH가 갱신되지 않은 것이다(Docker Desktop 설치 직후).
- 컨테이너 포트는 모두 `127.0.0.1`에만 열려 있다. **호스트에서 Docker PostgreSQL은 5433 포트**다. 5432는 이 PC에 따로 설치된 Windows PostgreSQL 16 서비스이므로 데이터 적재 스크립트나 DB 도구를 5432에 연결하지 않는다.

## 구조와 설정

- **환경 변수는 저장소 루트의 `.env` 하나**를 docker compose, 백엔드, 프론트엔드가 함께 쓴다. 새 변수는 `.env.example`에도 추가한다.
  - 백엔드: `backend/app/core/config.py`의 pydantic-settings `Settings`가 읽는다. 컨테이너 안에서는 `docker-compose.yml`의 `environment`가 `DATABASE_URL`, `NEO4J_URI`, `REDIS_URL`을 서비스 이름(`postgres`, `neo4j`, `redis`) 기준으로 덮어쓴다. `.env`의 `localhost` 값은 호스트에서 직접 접속할 때용이다.
  - 프론트엔드: `vite.config.js`의 `envDir: '..'`로 루트 `.env`를 읽고, `VITE_`로 시작하는 변수만 브라우저에 노출된다(`VITE_KAKAO_JS_KEY`). 카카오 REST 키 같은 비밀 키는 `VITE_`를 붙이지 않고 백엔드에서만 쓴다.
- **DB 연결**: `backend/app/db/connections.py`의 `Connections`가 PostgreSQL(SQLAlchemy async + asyncpg), Neo4j(async driver), Redis(redis.asyncio) 연결을 하나씩 만들고, `main.py`의 lifespan이 `app.state.connections`에 넣는다. 핸들러는 `request.app.state.connections`로 꺼내 쓴다.
- **테스트 패턴**: `tests/test_health.py`처럼 `app.state.connections`를 같은 메서드를 가진 가짜 객체로 바꿔서 실제 DB 없이 테스트한다.
- **브라우저는 FastAPI만 호출**한다. 외부 API(기상청, 에어코리아, 카카오 로컬, Claude) 호출과 DB 접근은 모두 백엔드가 맡는다. 카카오맵 JS SDK만 예외로 브라우저에서 불러온다(`frontend/src/lib/kakaoMap.js`).

## 데이터 저장 위치 (기획서 기준)

- PostgreSQL(+PostGIS): 회원, 코스, 공원, 화장실, 저장된 장소, LLM 호출 로그(JSONB 컬럼, 별도 로그 DB 없음)
- Neo4j: OSM 보행로 그래프와 지점별 고도. 순환 코스 탐색용. 1주차 검증에서 막히면 PostGIS + pgRouting으로 바꾼다.
- Redis: MVP에서는 기상청·에어코리아·기상특보 응답 캐시만 둔다. 다른 캐시는 성능을 측정한 뒤 추가한다.
- 공공데이터포털 API(기상청, 에어코리아, 두루누비)는 `DATA_GO_KR_SERVICE_KEY` 하나를 함께 쓴다.
- OSM, DEM 같은 원본 데이터는 `data/raw/`에 두고 Git에 올리지 않는다. 다운로드 스크립트만 올린다.

## 핵심 로직 원칙 (자세한 식과 예시는 기획서 "핵심 로직")

- **LLM은 코스를 만들지 않는다.** 자연어를 검색 조건(Pydantic 스키마로 고정한 JSON)으로 바꾸고, DB에서 찾은 결과를 설명하는 일만 한다. 설명 속 숫자는 원본 데이터와 대조하고, LLM 호출이 실패하면 일반 필터 검색으로 대신 처리한다. 기본 모델은 `LLM_MODEL`(claude-haiku-5-5), LangChain으로 호출한다.
- **러닝 지수**: 위험 조건(강수 중, 미세먼지 매우 나쁨, 폭염·한파 특보)을 먼저 검사하고, 해당하면 점수를 내지 않고 "실내 운동 권장"을 반환한다. 대기질은 PM10과 PM2.5 중 나쁜 등급을 쓴다. 기획서의 40.5점 예시는 단위 테스트로 고정한다.
- **순환 코스**: 그래프 탐색으로 출발지 → 경유지 2곳 → 출발지 경로를 만들고, 목표 거리 ±10%, 출발점 복귀, 왕복 비율 같은 필수 조건을 통과한 후보만 점수를 매겨 최대 3개를 추천한다.
