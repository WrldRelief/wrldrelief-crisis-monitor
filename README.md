# 🌍 WRLD Relief Crisis Monitor

**AI 기반 실시간 재난 모니터링 대시보드**

[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.6-green.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📋 프로젝트 개요

WRLD Relief Crisis Monitor는 AI 기반으로 전 세계 재난 정보를 실시간으로 수집, 분석하고 블록체인 저장용 데이터로 변환하는 **간단하고 효율적인 대시보드 시스템**입니다.

### 🎯 핵심 기능

- 🔍 **실시간 AI 재난 검색**: USGS, RSS 뉴스, OpenAI API 통합
- 📊 **웹 대시보드**: 한 페이지 테이블 형태 재난 현황 표시
- 📤 **블록체인 데이터 내보내기**: 온체인 저장용 JSON 포맷 생성
- 🤖 **자동 분류**: 재난 유형, 심각도, 신뢰도 자동 분석

## 🚀 빠른 시작

### 1. 설치
```bash
git clone https://github.com/WrldRelief/wrldrelief_crisis_monitor.git
cd wrldrelief_crisis_monitor/api-server
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

### 2. 환경 설정 (선택사항)
```bash
# OpenAI API 키 설정 (AI 검색 강화용)
export OPENAI_API_KEY="your_openai_api_key_here"
```

### 3. 서버 실행
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. 대시보드 접속
- **웹 대시보드**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs

## 🏗️ 시스템 아키텍처

```
📊 Crisis Monitor Dashboard
├── 🤖 AI 검색 엔진
│   ├── USGS 지진 API (키 불필요)
│   ├── RSS 뉴스 피드 (BBC, CNN, Reuters)
│   └── OpenAI API (선택사항)
├── 📱 웹 대시보드 (1페이지)
│   ├── 검색 입력창
│   ├── 재난 데이터 테이블
│   └── 블록체인 내보내기 버튼
└── 🔗 API (3개 엔드포인트)
    ├── GET / (대시보드)
    ├── POST /api/search (AI 검색)
    └── GET /api/export (블록체인 데이터)
```

## 📁 프로젝트 구조 (90% 간소화!)

```
wrldrelief_crisis_monitor/
├── README.md                 # 프로젝트 문서
├── LICENSE                   # MIT 라이선스
├── .gitignore               # Git 무시 파일
└── api-server/              # FastAPI 백엔드
    ├── .env                 # 환경 변수
    ├── requirements.txt     # 최소 의존성 (7개만!)
    └── app/                 # 애플리케이션
        ├── __init__.py      # 패키지 초기화
        ├── main.py          # FastAPI 앱 + 웹 대시보드 (200줄)
        └── ai_search.py     # AI 검색 엔진 (300줄)
```

## 🎯 사용 방법

### 1. 웹 대시보드 사용
1. http://localhost:8000 접속
2. 검색창에 재난 키워드 입력 (예: "earthquake japan", "flood texas")
3. "🔍 재난 검색" 버튼 클릭
4. 실시간 재난 정보 테이블에서 확인
5. "📤 블록체인 데이터 내보내기" 버튼으로 JSON 다운로드

### 2. API 직접 사용
```bash
# 재난 검색
curl -X POST "http://localhost:8000/api/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "global disasters today", "max_results": 10}'

# 블록체인 데이터 내보내기
curl "http://localhost:8000/api/export"
```

## 📊 데이터 소스

### 자동 수집 (키 불필요)
- **USGS 지진 API**: 실시간 지진 데이터
- **BBC World News RSS**: 글로벌 뉴스
- **CNN RSS**: 국제 뉴스
- **Reuters RSS**: 통신사 뉴스
- **Al Jazeera RSS**: 중동/아프리카 뉴스

### AI 강화 (선택사항)
- **OpenAI GPT**: 뉴스 분석 및 분류 강화

## 🔧 기술 스택

### 최소 의존성 (7개만!)
```
fastapi==0.115.6          # 웹 프레임워크
uvicorn[standard]==0.32.1 # ASGI 서버
pydantic==2.10.4          # 데이터 검증
aiohttp==3.10.11          # 비동기 HTTP 클라이언트
httpx==0.28.1             # HTTP 클라이언트
feedparser==6.0.11        # RSS 파싱
python-dotenv==1.0.1      # 환경 변수
```

### 내장 라이브러리 활용
- `asyncio` - 비동기 처리
- `json` - JSON 처리
- `datetime` - 시간 처리
- `logging` - 로깅
- `typing` - 타입 힌팅

## 📈 실제 테스트 결과

### ✅ 성공적으로 수집된 재난 데이터
```json
{
  "title": "At least 24 dead and up to 25 children missing in 'terrible' Texas floods",
  "location": "Texas, USA",
  "severity": "CRITICAL",
  "category": "FLOOD",
  "confidence": 75.0,
  "timestamp": 1751691269,
  "source": "News-BBC News"
}
```

### 📊 실시간 성능
- **검색 속도**: 평균 2-3초
- **데이터 소스**: 4개 RSS 피드 + USGS API
- **AI 분류**: 자동 심각도/카테고리 분류
- **중복 제거**: 제목 기반 자동 중복 제거

## 🌟 주요 특징

### 🎯 사용자 중심 설계
- **원클릭 검색**: 검색어 입력 → 버튼 클릭 → 즉시 결과
- **실시간 업데이트**: 타임스탬프 기반 최신 정보
- **직관적 UI**: 테이블 형태로 한눈에 파악

### ⚡ 성능 최적화
- **비동기 처리**: 여러 API 동시 호출
- **최소 의존성**: 7개 패키지만 사용
- **경량 구조**: 총 500줄 미만 코드

### 🔒 안정성
- **Fallback 시스템**: API 실패시 대체 데이터
- **에러 처리**: 모든 외부 API 호출 예외 처리
- **로깅**: 상세한 작업 로그

## 🚀 확장 가능성

### 현재 구현
- ✅ 실시간 재난 검색
- ✅ 웹 대시보드
- ✅ 블록체인 데이터 내보내기
- ✅ AI 자동 분류

### 향후 추가 가능
- 🔄 주기적 자동 검색 (cron job)
- 📱 모바일 반응형 UI
- 🗺️ 지도 시각화
- 📧 이메일/SMS 알림
- 🔗 실제 블록체인 연동

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## 👥 팀

- **WRLD Relief Team** - [GitHub](https://github.com/WrldRelief)

## 🔗 관련 링크

- [FastAPI 문서](https://fastapi.tiangolo.com/)
- [USGS 지진 API](https://earthquake.usgs.gov/earthquakes/feed/)
- [OpenAI API](https://platform.openai.com/docs/)

---

**🌍 함께 더 안전한 세상을 만들어갑시다!**

### 📞 지원

문제가 발생하거나 질문이 있으시면 [Issues](https://github.com/WrldRelief/wrldrelief_crisis_monitor/issues)를 통해 문의해 주세요.
# crisis-monitor
