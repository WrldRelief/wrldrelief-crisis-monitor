"""
🧪 WRLD Relief Disaster Agent 테스트 클라이언트
에이전트와 통신하여 재해 검색 기능을 테스트
"""

import asyncio
import logging
from uagents import Agent, Context, Model
from disaster_agent import DisasterQuery, DisasterResults, AgentStatus

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 테스트 클라이언트 에이전트 (로컬 전용)
test_agent = Agent(
    name="disaster_test_client",
    seed="test_client_seed_2025",
    port=8002,
    endpoint=["http://localhost:8002/submit"],
    mailbox=False  # Almanac 등록 문제 해결을 위해 비활성화
)

# 재해 모니터링 에이전트 주소
DISASTER_AGENT_ADDRESS = "agent1qwk8pf2gd5fnl6u6v7ete60stm3jve9yv0u6c9a8q45deslf4hdxx06dk63"

@test_agent.on_event("startup")
async def startup_handler(ctx: Context):
    """테스트 클라이언트 시작"""
    logger.info("🧪 Test client started")
    logger.info(f"🔗 Test client address: {test_agent.address}")
    
    # 3초 후 테스트 시작
    await asyncio.sleep(3)
    await run_tests(ctx)

async def run_tests(ctx: Context):
    """실제 데이터를 활용한 테스트 실행"""
    logger.info("🚀 Starting disaster agent tests with REAL DATA...")
    
    # 테스트 1: 상태 확인
    logger.info("📊 Test 1: Agent Status Check")
    status_query = AgentStatus()
    await ctx.send(DISASTER_AGENT_ADDRESS, status_query)
    
    await asyncio.sleep(2)
    
    # 테스트 2: 일본 지진 검색 (실제 데이터에 많음)
    logger.info("🗾 Test 2: Japan Earthquake Search (Real Data)")
    japan_query = DisasterQuery(
        query="earthquake japan",
        max_results=5,
        requester="test_client"
    )
    await ctx.send(DISASTER_AGENT_ADDRESS, japan_query)
    
    await asyncio.sleep(3)
    
    # 테스트 3: 텍사스 홍수 검색 (실제 데이터에 있음)
    logger.info("🌊 Test 3: Texas Flood Search (Real Data)")
    texas_query = DisasterQuery(
        query="texas flood",
        max_results=3,
        requester="test_client"
    )
    await ctx.send(DISASTER_AGENT_ADDRESS, texas_query)
    
    await asyncio.sleep(3)
    
    # 테스트 4: 산불 검색 (호주, 캐나다 등)
    logger.info("🔥 Test 4: Wildfire Search (Real Data)")
    fire_query = DisasterQuery(
        query="wildfire fire",
        max_results=3,
        requester="test_client"
    )
    await ctx.send(DISASTER_AGENT_ADDRESS, fire_query)
    
    await asyncio.sleep(3)
    
    # 테스트 5: 분쟁 검색 (이스라엘 등)
    logger.info("⚔️ Test 5: Conflict Search (Real Data)")
    conflict_query = DisasterQuery(
        query="attack conflict israel",
        max_results=3,
        requester="test_client"
    )
    await ctx.send(DISASTER_AGENT_ADDRESS, conflict_query)
    
    await asyncio.sleep(3)
    
    # 테스트 6: 태풍/허리케인 검색
    logger.info("🌀 Test 6: Hurricane/Typhoon Search (Real Data)")
    hurricane_query = DisasterQuery(
        query="hurricane typhoon cyclone",
        max_results=3,
        requester="test_client"
    )
    await ctx.send(DISASTER_AGENT_ADDRESS, hurricane_query)

@test_agent.on_message(model=AgentStatus)
async def handle_status_response(ctx: Context, sender: str, msg: AgentStatus):
    """상태 응답 처리"""
    logger.info(f"📊 Status Response from {sender}:")
    logger.info(f"   Status: {msg.status}")
    logger.info(f"   Last Search: {msg.last_search}")
    logger.info(f"   Total Searches: {msg.total_searches}")
    logger.info(f"   Uptime: {msg.uptime}")

@test_agent.on_message(model=DisasterResults)
async def handle_disaster_results(ctx: Context, sender: str, msg: DisasterResults):
    """재해 검색 결과 처리"""
    logger.info(f"🔍 Disaster Results from {sender}:")
    logger.info(f"   Query: '{msg.query}'")
    logger.info(f"   Total Count: {msg.total_count}")
    logger.info(f"   Agent: {msg.agent_name}")
    
    if msg.disasters:
        logger.info(f"   Found {len(msg.disasters)} disasters:")
        for i, disaster in enumerate(msg.disasters[:3], 1):  # 처음 3개만 표시
            logger.info(f"   {i}. {disaster.title}")
            logger.info(f"      Location: {disaster.location}")
            logger.info(f"      Severity: {disaster.severity}")
            logger.info(f"      Category: {disaster.category}")
            logger.info(f"      Source: {disaster.source}")
    else:
        logger.info("   No disasters found")
    
    logger.info("   " + "="*50)

if __name__ == "__main__":
    logger.info("🧪 Starting Disaster Agent Test Client...")
    logger.info("🎯 Will test disaster monitoring functionality")
    
    # 테스트 클라이언트 실행
    test_agent.run()
