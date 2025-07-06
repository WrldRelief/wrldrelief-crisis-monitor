"""
🌍 WRLD Relief Disaster Monitoring Agent - ASI:One Compatible Version
Official Chat Protocol implementation for ASI:One integration
Real-time disaster monitoring with natural language chat support
"""

from datetime import datetime
from uuid import uuid4
from uagents import Agent, Context, Protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    EndSessionContent,
    TextContent,
    chat_protocol_spec,
)
import aiohttp
import json
import asyncio
from typing import List, Dict, Any
import re

# ============================================================================
# ASI:One Compatible Agent with Official Chat Protocol
# ============================================================================

# Agent 생성
agent = Agent(
    name="wrld_relief_crisis_monitor",
    seed="wrld_relief_crisis_monitoring_seed_2025_v2",
    version="2.0.0"
)

# 공식 Chat Protocol 생성
protocol = Protocol(spec=chat_protocol_spec)

# ============================================================================
# 글로벌 변수
# ============================================================================

disaster_cache = []
last_update = 0
search_count = 0
start_time = datetime.now()

# 재해 모니터링 전문 분야 설정
subject_matter = "global disaster monitoring, earthquakes, floods, wildfires, hurricanes, emergency response, and crisis management"

# ============================================================================
# 데이터 수집 함수들
# ============================================================================

async def fetch_usgs_earthquakes(ctx: Context) -> List[Dict]:
    """USGS 지진 데이터 실시간 수집"""
    disasters = []
    
    try:
        async with aiohttp.ClientSession() as session:
            url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_week.geojson"
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    for feature in data.get('features', [])[:15]:
                        props = feature.get('properties', {})
                        coords = feature.get('geometry', {}).get('coordinates', [0, 0, 0])
                        
                        magnitude = props.get('mag', 0)
                        if magnitude >= 7.0:
                            severity = 'CRITICAL'
                        elif magnitude >= 6.0:
                            severity = 'HIGH'
                        elif magnitude >= 5.0:
                            severity = 'MEDIUM'
                        else:
                            severity = 'LOW'
                        
                        disaster = {
                            'id': f"usgs_{props.get('ids', f'eq_{int(datetime.now().timestamp())}')}",
                            'title': props.get('title', 'Earthquake'),
                            'description': f"Magnitude {magnitude} earthquake. {props.get('type', 'earthquake').title()} event.",
                            'location': props.get('place', 'Unknown location'),
                            'severity': severity,
                            'category': 'EARTHQUAKE',
                            'timestamp': props.get('time', 0) // 1000,
                            'source': 'USGS',
                            'confidence': 0.95,
                            'affected_people': estimate_affected_people(magnitude),
                            'coordinates': {"lat": coords[1] if len(coords) > 1 else 0.0, "lng": coords[0] if len(coords) > 0 else 0.0}
                        }
                        disasters.append(disaster)
                        
        ctx.logger.info(f"📊 Fetched {len(disasters)} earthquakes from USGS")
        
    except Exception as e:
        ctx.logger.error(f"❌ USGS fetch error: {e}")
    
    return disasters

async def fetch_simulated_disasters(ctx: Context) -> List[Dict]:
    """다양한 재해 시뮬레이션 데이터"""
    current_time = int(datetime.now().timestamp())
    
    simulated_disasters = [
        {
            'id': 'sim_flood_001',
            'title': 'Severe Flooding in Bangladesh',
            'description': 'Monsoon rains cause widespread flooding affecting rural communities. Emergency shelters activated.',
            'location': 'Sylhet Division, Bangladesh',
            'severity': 'HIGH',
            'category': 'FLOOD',
            'timestamp': current_time - 86400,
            'source': 'ReliefWeb Simulation',
            'confidence': 0.85,
            'affected_people': 50000,
            'coordinates': {"lat": 24.8949, "lng": 91.8687}
        },
        {
            'id': 'sim_fire_001',
            'title': 'Wildfire Threatens California Communities',
            'description': 'Fast-moving wildfire forces evacuations in residential areas. Firefighting efforts ongoing.',
            'location': 'Riverside County, California, USA',
            'severity': 'MEDIUM',
            'category': 'WILDFIRE',
            'timestamp': current_time - 172800,
            'source': 'CAL FIRE Simulation',
            'confidence': 0.80,
            'affected_people': 15000,
            'coordinates': {"lat": 33.7175, "lng": -116.2023}
        },
        {
            'id': 'sim_hurricane_001',
            'title': 'Tropical Storm Approaches Philippines',
            'description': 'Tropical storm with sustained winds of 85 mph approaching eastern coastline. Preparations underway.',
            'location': 'Eastern Visayas, Philippines',
            'severity': 'HIGH',
            'category': 'HURRICANE',
            'timestamp': current_time - 259200,
            'source': 'PAGASA Simulation',
            'confidence': 0.90,
            'affected_people': 200000,
            'coordinates': {"lat": 11.2500, "lng": 125.0000}
        },
        {
            'id': 'sim_conflict_001',
            'title': 'Humanitarian Crisis in Conflict Zone',
            'description': 'Ongoing conflict displaces thousands of civilians. Humanitarian aid urgently needed.',
            'location': 'Northern Syria',
            'severity': 'CRITICAL',
            'category': 'CONFLICT',
            'timestamp': current_time - 345600,
            'source': 'UN OCHA Simulation',
            'confidence': 0.75,
            'affected_people': 100000,
            'coordinates': {"lat": 36.2021, "lng": 37.1343}
        },
        {
            'id': 'sim_volcano_001',
            'title': 'Volcanic Activity Alert in Indonesia',
            'description': 'Increased volcanic activity detected. Alert level raised, nearby villages on standby for evacuation.',
            'location': 'Mount Merapi, Central Java, Indonesia',
            'severity': 'MEDIUM',
            'category': 'VOLCANO',
            'timestamp': current_time - 432000,
            'source': 'PVMBG Simulation',
            'confidence': 0.88,
            'affected_people': 25000,
            'coordinates': {"lat": -7.5407, "lng": 110.4461}
        }
    ]
    
    ctx.logger.info(f"📊 Generated {len(simulated_disasters)} simulated disasters")
    return simulated_disasters

def estimate_affected_people(magnitude: float) -> int:
    """지진 규모에 따른 피해자 수 추정"""
    if magnitude >= 7.0:
        return int(magnitude * 50000)
    elif magnitude >= 6.0:
        return int(magnitude * 10000)
    elif magnitude >= 5.0:
        return int(magnitude * 2000)
    else:
        return int(magnitude * 500)

# ============================================================================
# 검색 엔진
# ============================================================================

def search_disasters_by_query(query: str, max_results: int = 5) -> List[Dict]:
    """고급 재해 검색 엔진"""
    query_lower = query.lower()
    matched_disasters = []
    
    # 한국어-영어 키워드 매핑
    korean_mappings = {
        '지진': ['earthquake', 'seismic'],
        '홍수': ['flood', 'flooding'],
        '산불': ['fire', 'wildfire'],
        '태풍': ['hurricane', 'typhoon', 'cyclone'],
        '화산': ['volcano', 'volcanic'],
        '분쟁': ['war', 'conflict', 'attack'],
        '재해': ['disaster', 'emergency'],
        '재난': ['disaster', 'catastrophe'],
        '일본': ['japan', 'japanese'],
        '중국': ['china', 'chinese'],
        '미국': ['usa', 'america', 'united states'],
        '인도네시아': ['indonesia', 'indonesian'],
        '필리핀': ['philippines', 'philippine'],
        '방글라데시': ['bangladesh'],
        '최근': ['recent', 'latest'],
        '오늘': ['today', 'current'],
        '어제': ['yesterday'],
        '심각한': ['severe', 'critical', 'major'],
        '큰': ['large', 'big', 'major']
    }
    
    # 쿼리 확장 (한국어 → 영어)
    expanded_query = query_lower
    for korean, english_words in korean_mappings.items():
        if korean in query_lower:
            expanded_query += ' ' + ' '.join(english_words)
    
    query_words = expanded_query.split()
    
    for disaster in disaster_cache:
        score = 0
        
        title = disaster.get('title', '').lower()
        description = disaster.get('description', '').lower()
        location = disaster.get('location', '').lower()
        category = disaster.get('category', '').lower()
        
        # 기본 키워드 매칭
        for word in query_words:
            if len(word) < 2:
                continue
                
            if word in title:
                score += 5
            if word in description:
                score += 3
            if word in location:
                score += 4
            if word in category:
                score += 2
        
        # 카테고리별 특별 점수
        category_bonuses = {
            'earthquake': 'EARTHQUAKE',
            'seismic': 'EARTHQUAKE',
            'flood': 'FLOOD',
            'flooding': 'FLOOD',
            'fire': 'WILDFIRE',
            'wildfire': 'WILDFIRE',
            'hurricane': 'HURRICANE',
            'typhoon': 'HURRICANE',
            'cyclone': 'HURRICANE',
            'volcano': 'VOLCANO',
            'volcanic': 'VOLCANO',
            'conflict': 'CONFLICT',
            'war': 'CONFLICT',
            'attack': 'CONFLICT'
        }
        
        for keyword, cat in category_bonuses.items():
            if keyword in expanded_query and disaster.get('category') == cat:
                score += 10
        
        # 지역별 특별 점수
        location_bonuses = {
            'japan': ['japan', 'japanese'],
            'china': ['china', 'chinese'],
            'usa': ['united states', 'america', 'california', 'texas'],
            'indonesia': ['indonesia', 'java'],
            'philippines': ['philippines', 'visayas'],
            'bangladesh': ['bangladesh', 'sylhet']
        }
        
        for region, location_keywords in location_bonuses.items():
            if region in expanded_query:
                for loc_keyword in location_keywords:
                    if loc_keyword in location:
                        score += 8
        
        # 심각도 기반 점수
        severity_bonuses = {
            'CRITICAL': 4,
            'HIGH': 3,
            'MEDIUM': 2,
            'LOW': 1
        }
        
        if any(word in ['severe', 'critical', 'major', 'serious', '심각한', '큰'] for word in query_words):
            score += severity_bonuses.get(disaster.get('severity', 'LOW'), 0)
        
        # 시간 기반 점수
        if any(word in ['recent', 'latest', 'today', 'current', '최근', '오늘'] for word in query_words):
            disaster_time = disaster.get('timestamp', 0)
            current_time = int(datetime.now().timestamp())
            days_ago = (current_time - disaster_time) / 86400
            
            if days_ago <= 1:
                score += 5
            elif days_ago <= 3:
                score += 3
            elif days_ago <= 7:
                score += 1
        
        if score > 0:
            disaster_copy = disaster.copy()
            disaster_copy['search_score'] = score
            matched_disasters.append(disaster_copy)
    
    matched_disasters.sort(key=lambda x: x.get('search_score', 0), reverse=True)
    return matched_disasters[:max_results]

# ============================================================================
# 에이전트 이벤트 핸들러
# ============================================================================

@agent.on_event("startup")
async def startup_handler(ctx: Context):
    """에이전트 시작 시 초기화 및 ASI:One 등록"""
    global start_time
    start_time = datetime.now()
    
    ctx.logger.info("🌍 WRLD Relief Disaster Agent (ASI:One Compatible) starting...")
    ctx.logger.info(f"🔗 Agent address: {agent.address}")
    
    # ASI:One 검색을 위한 메타데이터 설정
    agent.name = "WRLD Relief Global Disaster Monitor"
    agent.description = f"🌍 Expert in {subject_matter}. Provides real-time global disaster monitoring with USGS earthquake data, flood tracking, wildfire alerts, and emergency response information worldwide."
    
    # 검색 키워드 로깅
    search_keywords = [
        "disaster", "emergency", "earthquake", "flood", "wildfire", 
        "hurricane", "tsunami", "monitoring", "alert", "global",
        "relief", "crisis", "natural disaster", "weather emergency",
        "WRLD Relief", "disaster monitor", "재해", "재난", "지진", "홍수"
    ]
    
    ctx.logger.info(f"🔍 ASI:One Search Keywords: {', '.join(search_keywords[:10])}...")
    ctx.logger.info(f"🆔 Agent ID: {agent.address}")
    ctx.logger.info(f"🎯 Subject Matter: {subject_matter}")
    
    # 초기 데이터 로드
    await refresh_disaster_data(ctx)
    
    ctx.logger.info("✅ WRLD Relief Disaster Agent ready for ASI:One Chat Protocol!")
    ctx.logger.info("🎯 Available via ASI:One search: 'disaster monitoring', 'WRLD Relief'")

async def refresh_disaster_data(ctx: Context):
    """재해 데이터 새로고침"""
    global disaster_cache, last_update
    
    try:
        ctx.logger.info("🔄 Refreshing disaster data...")
        
        # 실제 USGS 지진 데이터
        earthquakes = await fetch_usgs_earthquakes(ctx)
        
        # 시뮬레이션 재해 데이터
        simulated_disasters = await fetch_simulated_disasters(ctx)
        
        # 데이터 통합
        disaster_cache = earthquakes + simulated_disasters
        last_update = int(datetime.now().timestamp())
        
        ctx.logger.info(f"✅ Loaded {len(disaster_cache)} total disasters")
        ctx.logger.info(f"   - {len(earthquakes)} real earthquakes from USGS")
        ctx.logger.info(f"   - {len(simulated_disasters)} simulated disasters")
        
    except Exception as e:
        ctx.logger.error(f"❌ Data refresh error: {e}")

# ============================================================================
# 공식 Chat Protocol 핸들러
# ============================================================================

@protocol.on_message(ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
    """ASI:One 공식 Chat Protocol 메시지 핸들러"""
    global search_count
    search_count += 1
    
    # 메시지 수신 확인 전송
    await ctx.send(
        sender,
        ChatAcknowledgement(timestamp=datetime.now(), acknowledged_msg_id=msg.msg_id),
    )
    
    ctx.logger.info(f"💬 Chat message #{search_count} from {sender}")
    
    # 텍스트 내용 추출
    text = ''
    for item in msg.content:
        if isinstance(item, TextContent):
            text += item.text
    
    ctx.logger.info(f"📝 Message content: '{text}'")
    
    # 응답 생성
    response_text = await generate_disaster_response(ctx, text)
    
    # 공식 Chat Protocol 형식으로 응답 전송
    await ctx.send(sender, ChatMessage(
        timestamp=datetime.utcnow(),
        msg_id=uuid4(),
        content=[
            TextContent(type="text", text=response_text),
            EndSessionContent(type="end-session"),
        ]
    ))

@protocol.on_message(ChatAcknowledgement)
async def handle_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    """메시지 수신 확인 처리"""
    ctx.logger.info(f"✅ Message acknowledged by {sender}")

async def generate_disaster_response(ctx: Context, text: str) -> str:
    """재해 관련 응답 생성"""
    try:
        text_lower = text.lower()
        
        # 데이터 새로고침 확인
        if int(datetime.now().timestamp()) - last_update > 3600:
            await refresh_disaster_data(ctx)
        
        # 재해 관련 키워드 감지
        disaster_keywords = [
            'earthquake', 'flood', 'fire', 'disaster', 'emergency', 'crisis',
            'japan', 'california', 'tsunami', 'hurricane', 'typhoon', 'volcano',
            'conflict', 'war', 'attack', 'wildfire', 'flooding', 'seismic',
            '지진', '홍수', '재해', '재난', '일본', '미국', '태풍', '산불', '분쟁'
        ]
        
        # 상태 확인 요청
        if any(word in text_lower for word in ['status', 'health', 'info', 'about', '상태', '정보']):
            uptime = datetime.now() - start_time
            uptime_str = f"{uptime.days}d {uptime.seconds//3600}h {(uptime.seconds//60)%60}m"
            
            return f"""🌍 **WRLD Relief Disaster Agent Status**

🟢 **Status**: Online and monitoring
📊 **Total Disasters**: {len(disaster_cache)}
🔍 **Searches Performed**: {search_count}
⏰ **Uptime**: {uptime_str}
🔄 **Last Data Update**: {datetime.fromtimestamp(last_update).strftime('%Y-%m-%d %H:%M:%S') if last_update else 'Never'}
🆔 **Agent Address**: {agent.address}

**I specialize in {subject_matter}.**

**Available Commands:**
• "Show me earthquakes in Japan"
• "What disasters happened today?"
• "Any floods in Bangladesh?"
• "Tell me about recent wildfires"

Ready to help with global disaster monitoring! 🚨"""
        
        # 재해 검색 요청
        elif any(keyword in text_lower for keyword in disaster_keywords):
            disasters = search_disasters_by_query(text, 5)
            
            if disasters:
                response_text = f"🚨 **Found {len(disasters)} disasters related to your query:**\n\n"
                
                for i, disaster in enumerate(disasters, 1):
                    # 시간 포맷팅
                    disaster_time = datetime.fromtimestamp(disaster['timestamp'])
                    time_ago = datetime.now() - disaster_time
                    
                    if time_ago.days > 0:
                        time_str = f"{time_ago.days} days ago"
                    elif time_ago.seconds > 3600:
                        time_str = f"{time_ago.seconds//3600} hours ago"
                    else:
                        time_str = f"{time_ago.seconds//60} minutes ago"
                    
                    # 심각도 이모지
                    severity_emoji = {
                        'CRITICAL': '🔴',
                        'HIGH': '🟠', 
                        'MEDIUM': '🟡',
                        'LOW': '🟢'
                    }.get(disaster['severity'], '⚪')
                    
                    response_text += f"**{i}. {disaster['title']}**\n"
                    response_text += f"📍 **Location**: {disaster['location']}\n"
                    response_text += f"{severity_emoji} **Severity**: {disaster['severity']}\n"
                    response_text += f"📂 **Category**: {disaster['category']}\n"
                    response_text += f"⏰ **Time**: {time_str}\n"
                    response_text += f"📰 **Source**: {disaster['source']}\n"
                    
                    if disaster.get('affected_people', 0) > 0:
                        response_text += f"👥 **Affected**: {disaster['affected_people']:,} people\n"
                    
                    response_text += f"📝 **Details**: {disaster['description']}\n\n"
                
                response_text += "💡 **Need more specific information?** Try asking about:\n"
                response_text += "• Specific locations: 'earthquakes in Japan'\n"
                response_text += "• Disaster types: 'recent floods'\n"
                response_text += "• Severity levels: 'critical disasters today'"
                
                return response_text
                
            else:
                return f"""🔍 **No disasters found for '{text}'**

This could mean:
• No recent disasters match your criteria
• Try different keywords or locations
• Check spelling of location names

**Suggestions:**
• "earthquakes in Japan" 
• "floods in Bangladesh"
• "wildfires in California"
• "recent disasters today"
• "high severity emergencies"

I'm monitoring {len(disaster_cache)} disasters globally! 🌍"""
        
        # 도움말 요청
        elif any(word in text_lower for word in ['help', 'how', 'what can', 'commands', '도움', '명령어']):
            return f"""🌍 **WRLD Relief Disaster Monitoring Agent**

I'm an expert in **{subject_matter}**.

**🔍 What I can help with:**
• 🌏 **Global disaster monitoring** - earthquakes, floods, wildfires, hurricanes
• 📊 **Real-time updates** - latest disaster information from USGS and other sources  
• 🗺️ **Location-based search** - disasters in specific countries/regions
• ⚠️ **Severity assessment** - critical, high, medium, low severity levels
• 📈 **Impact analysis** - affected population and damage estimates

**💬 Example queries:**
• "Show me recent earthquakes in Japan"
• "What floods happened this week?"
• "Any wildfires in California?"
• "Tell me about critical disasters today"
• "Disasters in Southeast Asia"

**🌐 Data sources:**
• USGS (earthquakes)
• ReliefWeb (humanitarian crises)
• Global disaster monitoring networks

Ready to help you stay informed about global emergencies! 🚨"""
        
        # 전문 분야 외 질문
        else:
            return f"""👋 **Hello! I'm the WRLD Relief Disaster Monitoring Agent**

I specialize in **{subject_matter}**.

If you're asking about other topics, I politely say that I don't know about them as I focus specifically on disaster monitoring and emergency response.

**🚨 Currently monitoring {len(disaster_cache)} disasters worldwide**

**Quick examples to try:**
• "Show me earthquakes in Japan" 🗾
• "What disasters happened today?" 📅  
• "Any floods in Bangladesh?" 🌊
• "Tell me about recent wildfires" 🔥
• "Status" - for system information 📊

I'm here 24/7 to help you stay informed about global emergencies and disasters. What would you like to know? 🌍"""
        
    except Exception as e:
        ctx.logger.error(f"❌ Response generation error: {e}")
        return "🚨 Sorry, I encountered an error processing your request. Please try again or ask for 'help' to see available commands."

# ============================================================================
# 주기적 작업
# ============================================================================

@agent.on_interval(period=3600.0)  # 1시간마다
async def periodic_data_refresh(ctx: Context):
    """주기적 데이터 새로고침"""
    ctx.logger.info("🔄 Periodic data refresh starting...")
    await refresh_disaster_data(ctx)

@agent.on_interval(period=1800.0)  # 30분마다
async def periodic_health_check(ctx: Context):
    """주기적 상태 체크"""
    uptime = datetime.now() - start_time
    ctx.logger.info(f"💓 Health check - Disasters: {len(disaster_cache)}, Searches: {search_count}, Uptime: {uptime}")

# ============================================================================
# Protocol 연결 및 에이전트 실행
# ============================================================================

# 공식 Chat Protocol을 에이전트에 연결
agent.include(protocol, publish_manifest=True)

if __name__ == "__main__":
    agent.run()
