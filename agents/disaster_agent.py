"""
🤖 WRLD Relief Disaster Monitoring uAgent
ASI Alliance 통합을 위한 재해 모니터링 에이전트
기존 AI 검색 시스템을 uAgent로 래핑
"""

import asyncio
import logging
import sys
import os
from typing import List, Dict, Any
from datetime import datetime

# uAgents 라이브러리
from uagents import Agent, Context, Model
from uagents.setup import fund_agent_if_low

# 기존 프로젝트 모듈 import를 위한 경로 설정
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'api-server', 'app'))

try:
    from ai_agent import AISearchAgent
    from ai_search import DisasterInfo
    import json
    from pathlib import Path
except ImportError as e:
    logging.error(f"Failed to import existing modules: {e}")
    logging.error("Make sure you're running from the project root directory")
    sys.exit(1)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 메시지 모델 정의
class DisasterQuery(Model):
    """재해 검색 쿼리 메시지"""
    query: str = "global disasters today"
    max_results: int = 10
    requester: str = "user"

class DisasterResult(Model):
    """개별 재해 결과"""
    id: str
    title: str
    description: str
    location: str
    severity: str
    category: str
    timestamp: int
    source: str
    confidence: float
    affected_people: int = 0
    coordinates: Dict[str, float] = {"lat": 0.0, "lng": 0.0}

class DisasterResults(Model):
    """재해 검색 결과 리스트"""
    disasters: List[DisasterResult]
    total_count: int
    query: str
    searched_at: int
    agent_name: str = "WRLD Relief Disaster Agent"

class AgentStatus(Model):
    """에이전트 상태 정보"""
    status: str = "online"
    last_search: str = ""
    total_searches: int = 0
    uptime: str = ""

# uAgent 생성 (로컬 전용, Almanac 등록 비활성화)
agent = Agent(
    name="wrld_relief_disaster_agent",
    seed="wrld_relief_disaster_monitoring_seed_2025",
    port=8001,
    endpoint=["http://localhost:8001/submit"],
    mailbox=False  # Almanac 등록 문제 해결을 위해 비활성화
)

# 글로벌 변수
search_engine = None
search_count = 0
start_time = datetime.now()

@agent.on_event("startup")
async def startup_handler(ctx: Context):
    """에이전트 시작 시 초기화"""
    global search_engine
    
    logger.info(f"🚀 WRLD Relief Disaster Agent starting...")
    logger.info(f"🔗 Agent address: {agent.address}")
    logger.info(f"🌐 Agent endpoint: {agent._endpoints}")
    
    # AI 검색 엔진 초기화
    try:
        search_engine = AISearchAgent()
        logger.info("✅ AI Search Engine initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize AI Search Engine: {e}")
        search_engine = None
    
    # 에이전트 자금 확인 (테스트넷용)
    try:
        await fund_agent_if_low(agent.wallet.address())
        logger.info("💰 Agent funding checked")
    except Exception as e:
        logger.warning(f"⚠️ Funding check failed: {e}")
    
    logger.info("✅ WRLD Relief Disaster Agent ready for disaster monitoring!")

def load_cached_disasters():
    """캐시된 재해 데이터 로드"""
    try:
        cache_path = Path(__file__).parent.parent / "api-server" / "data" / "disasters_cache.json"
        if cache_path.exists():
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('disasters', [])
    except Exception as e:
        logger.error(f"Failed to load cached disasters: {e}")
    return []

def search_disasters_by_query(disasters_data: List[Dict], query: str, max_results: int = 10) -> List[Dict]:
    """쿼리에 따라 재해 데이터 검색"""
    query_lower = query.lower()
    matched_disasters = []
    
    # 키워드 매칭
    for disaster in disasters_data:
        title = disaster.get('title', '').lower()
        description = disaster.get('description', '').lower()
        location = disaster.get('location', '').lower()
        category = disaster.get('category', '').lower()
        
        # 검색 점수 계산
        score = 0
        
        # 쿼리 키워드들로 분할
        query_words = query_lower.split()
        
        for word in query_words:
            if word in title:
                score += 3  # 제목에서 발견시 높은 점수
            if word in description:
                score += 2  # 설명에서 발견시 중간 점수
            if word in location:
                score += 2  # 위치에서 발견시 중간 점수
            if word in category:
                score += 1  # 카테고리에서 발견시 낮은 점수
        
        # 특별 키워드 처리
        if any(word in ['earthquake', 'seismic', '지진'] for word in query_words):
            if disaster.get('category') == 'EARTHQUAKE':
                score += 5
        
        if any(word in ['flood', 'flooding', '홍수'] for word in query_words):
            if disaster.get('category') == 'FLOOD':
                score += 5
                
        if any(word in ['fire', 'wildfire', '산불'] for word in query_words):
            if disaster.get('category') == 'WILDFIRE':
                score += 5
                
        if any(word in ['hurricane', 'typhoon', 'cyclone', '태풍', '허리케인'] for word in query_words):
            if disaster.get('category') == 'HURRICANE':
                score += 5
                
        if any(word in ['volcano', 'volcanic', '화산'] for word in query_words):
            if disaster.get('category') == 'VOLCANO':
                score += 5
                
        if any(word in ['war', 'conflict', 'attack', '전쟁', '분쟁'] for word in query_words):
            if disaster.get('category') == 'OTHER' and any(word in description for word in ['attack', 'killed', 'war', 'conflict']):
                score += 5
        
        # 지역별 검색
        if any(word in ['japan', 'japanese', '일본'] for word in query_words):
            if 'japan' in location:
                score += 4
                
        if any(word in ['china', 'chinese', '중국'] for word in query_words):
            if 'china' in location:
                score += 4
                
        if any(word in ['usa', 'america', 'united states', '미국'] for word in query_words):
            if any(word in location for word in ['united states', 'usa', 'america']):
                score += 4
        
        if score > 0:
            disaster_copy = disaster.copy()
            disaster_copy['search_score'] = score
            matched_disasters.append(disaster_copy)
    
    # 점수순으로 정렬하고 최대 결과 수만큼 반환
    matched_disasters.sort(key=lambda x: x.get('search_score', 0), reverse=True)
    return matched_disasters[:max_results]

@agent.on_message(model=DisasterQuery)
async def handle_disaster_query(ctx: Context, sender: str, msg: DisasterQuery):
    """재해 검색 쿼리 처리 - 실제 캐시된 데이터 사용"""
    global search_count
    search_count += 1
    
    logger.info(f"🔍 Received disaster query from {sender}: '{msg.query}'")
    logger.info(f"📊 Search count: {search_count}")
    
    try:
        # 캐시된 실제 데이터 로드
        cached_disasters = load_cached_disasters()
        logger.info(f"📦 Loaded {len(cached_disasters)} cached disasters")
        
        # 쿼리에 따라 검색
        matched_disasters = search_disasters_by_query(
            cached_disasters, 
            msg.query, 
            msg.max_results
        )
        
        # DisasterResult 모델로 변환
        disaster_results = []
        for disaster in matched_disasters:
            disaster_result = DisasterResult(
                id=disaster.get('id', 'unknown'),
                title=disaster.get('title', 'Unknown Disaster'),
                description=disaster.get('description', ''),
                location=disaster.get('location', 'Unknown Location'),
                severity=disaster.get('severity', 'MEDIUM'),
                category=disaster.get('category', 'OTHER'),
                timestamp=disaster.get('timestamp', int(datetime.now().timestamp())),
                source=disaster.get('source', 'WRLD Relief Cache'),
                confidence=disaster.get('confidence', 0.8),
                affected_people=disaster.get('affected_people', 0) or 0,
                coordinates=disaster.get('coordinates', {"lat": 0.0, "lng": 0.0})
            )
            disaster_results.append(disaster_result)
        
        # 결과 메시지 생성
        results = DisasterResults(
            disasters=disaster_results,
            total_count=len(disaster_results),
            query=msg.query,
            searched_at=int(datetime.now().timestamp()),
            agent_name="WRLD Relief Disaster Agent"
        )
        
        logger.info(f"✅ Found {len(disaster_results)} disasters for query: '{msg.query}'")
        if disaster_results:
            logger.info(f"🎯 Top result: {disaster_results[0].title} ({disaster_results[0].category})")
        
        # 결과 전송
        await ctx.send(sender, results)
        
    except Exception as e:
        logger.error(f"❌ Error processing disaster query: {e}")
        
        # 에러 시 빈 결과 전송
        error_results = DisasterResults(
            disasters=[],
            total_count=0,
            query=msg.query,
            searched_at=int(datetime.now().timestamp()),
            agent_name="WRLD Relief Disaster Agent (Error)"
        )
        
        await ctx.send(sender, error_results)

@agent.on_message(model=AgentStatus)
async def handle_status_request(ctx: Context, sender: str, msg: AgentStatus):
    """에이전트 상태 요청 처리"""
    uptime = datetime.now() - start_time
    uptime_str = f"{uptime.days}d {uptime.seconds//3600}h {(uptime.seconds//60)%60}m"
    
    status = AgentStatus(
        status="online",
        last_search=f"Search count: {search_count}",
        total_searches=search_count,
        uptime=uptime_str
    )
    
    logger.info(f"📊 Status request from {sender}")
    await ctx.send(sender, status)

@agent.on_interval(period=300.0)  # 5분마다
async def periodic_health_check(ctx: Context):
    """주기적 상태 체크"""
    logger.info(f"💓 Health check - Searches: {search_count}, Uptime: {datetime.now() - start_time}")

# HTTP 상태 확인을 위한 간단한 엔드포인트 추가
from fastapi import FastAPI
from fastapi.responses import JSONResponse

# FastAPI 인스턴스 생성 (uAgent와 별도)
status_app = FastAPI(title="WRLD Relief Disaster Agent Status")

@status_app.get("/")
async def agent_status():
    """에이전트 상태 확인 엔드포인트"""
    uptime = datetime.now() - start_time
    return JSONResponse({
        "agent_name": "WRLD Relief Disaster Agent",
        "status": "online",
        "address": str(agent.address),
        "port": 8001,
        "search_count": search_count,
        "uptime": f"{uptime.days}d {uptime.seconds//3600}h {(uptime.seconds//60)%60}m",
        "ai_engine": "initialized" if search_engine else "not_initialized",
        "endpoints": agent._endpoints,
        "message": "Agent is running and ready for disaster monitoring!",
        "protocols": ["DisasterQuery", "DisasterResults", "AgentStatus"],
        "last_health_check": datetime.now().isoformat()
    })

@status_app.get("/health")
async def health_check():
    """간단한 헬스 체크"""
    return {"status": "healthy", "agent": "disaster_monitor", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    logger.info("🌍 Starting WRLD Relief Disaster Monitoring Agent...")
    logger.info("🎯 Ready to monitor global disasters and conflicts!")
    logger.info("🔗 Connect via ASI:One or send DisasterQuery messages")
    
    # 에이전트 실행
    agent.run()
