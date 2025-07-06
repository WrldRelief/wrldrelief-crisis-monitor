# 🤖 WRLD Relief Disaster Monitoring Agent

## 개요
WRLD Relief Disaster Monitoring Agent는 전 세계 재해와 분쟁을 실시간으로 모니터링하고 분석하는 AI 에이전트입니다. ASI Alliance 생태계의 일부로서, 다른 에이전트들과 협업하여 재해 대응을 지원합니다.

## 주요 기능

### 🔍 실시간 재해 모니터링
- 지진, 홍수, 허리케인, 화산 폭발 등 자연재해 감지
- 전쟁, 테러, 분쟁 등 인위적 재해 모니터링
- 30+ 카테고리의 포괄적 재해 분류

### 🧠 AI 기반 분석
- Perplexity, OpenAI 등 최신 AI 모델 활용
- 재해 심각도 자동 평가 (HIGH/MEDIUM/LOW)
- 피해 규모 및 영향 범위 예측

### 🌍 글로벌 커버리지
- 전 세계 모든 지역 모니터링
- 정확한 지리적 좌표 제공
- 다국어 뉴스 소스 통합

### ⛓️ 블록체인 통합
- 재해 데이터 온체인 저장
- 투명하고 변조 불가능한 기록
- 월드코인 미니앱 연동 준비

## 메시지 프로토콜

### DisasterQuery
재해 검색을 요청하는 메시지
```python
{
    "query": "global disasters today",
    "max_results": 10,
    "requester": "user"
}
```

### DisasterResults
재해 검색 결과를 반환하는 메시지
```python
{
    "disasters": [...],
    "total_count": 5,
    "query": "earthquake japan",
    "searched_at": 1704067200,
    "agent_name": "WRLD Relief Disaster Agent"
}
```

### AgentStatus
에이전트 상태 정보를 요청/반환하는 메시지
```python
{
    "status": "online",
    "last_search": "Search count: 42",
    "total_searches": 42,
    "uptime": "1d 5h 30m"
}
```

## 사용 방법

### ASI:One에서 검색
1. [ASI:One](https://asi1.ai)에 접속
2. "disaster monitoring" 또는 "WRLD Relief" 검색
3. 에이전트와 직접 대화

### 다른 에이전트에서 호출
```python
from uagents import Agent, Context
from agents.disaster_agent import DisasterQuery

# 재해 검색 요청
query = DisasterQuery(
    query="earthquake turkey",
    max_results=5
)
await ctx.send("agent1q...", query)
```

## 실제 사용 사례

### 🚨 긴급 재해 대응
- 실시간 재해 감지 시 자동 알림
- 피해 규모 예측으로 대응 우선순위 결정
- 관련 기관에 즉시 정보 전달

### 📊 재해 분석 및 연구
- 과거 재해 데이터 분석
- 재해 패턴 및 트렌드 파악
- 예방 및 대비책 수립 지원

### 🌐 글로벌 모니터링
- 전 세계 재해 상황 통합 모니터링
- 지역별 위험도 평가
- 국제 협력 및 지원 조정

## 기술 스택
- **uAgents Framework**: ASI Alliance 에이전트 프레임워크
- **Python**: 메인 개발 언어
- **FastAPI**: 웹 API 서버
- **AI APIs**: Perplexity, OpenAI 등
- **Web3**: 블록체인 연동
- **Docker**: 컨테이너화 배포

## 연락처
- **GitHub**: https://github.com/GoGetShitDone/crisis-monitor
- **프로젝트**: WRLD Relief Crisis Monitor
- **목적**: ETH Global Cannes 2025 - ASI Alliance Track

---

*이 에이전트는 실제 재해 상황에서 생명을 구하고 피해를 최소화하는 것을 목표로 합니다.*
