"""
🤖 AI Search Agent
Perplexity, OpenAI 등을 활용한 실시간 재해 검색 및 스마트 좌표 시스템
"""

import aiohttp
import json
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import os
import hashlib
import re

logger = logging.getLogger(__name__)

class AISearchAgent:
    """AI 기반 재해 검색 에이전트"""
    
    def __init__(self):
        self.perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        # 7일 최적화된 검색 쿼리 (토큰 절약)
        self.search_queries = {
            "global": [
                "major earthquakes magnitude 5+ last 7 days worldwide",
                "natural disasters floods hurricanes typhoons past week",
                "breaking news disasters emergency alerts 7 days"
            ],
            "conflicts": [
                "armed conflicts war casualties past week worldwide",
                "terrorist attacks bombings last 7 days global",
                "refugee crisis displacement breaking news recent"
            ],
            "comprehensive": [
                "volcano eruptions landslides tsunamis past week",
                "industrial accidents chemical spills explosions 7 days",
                "humanitarian crisis famine epidemic recent"
            ]
        }
        
        # 포괄적 카테고리 시스템 (30+ 카테고리)
        self.disaster_categories = {
            # 자연재해
            "EARTHQUAKE": ["earthquake", "quake", "seismic", "tremor", "magnitude"],
            "TSUNAMI": ["tsunami", "tidal wave", "sea wave"],
            "VOLCANO": ["volcano", "volcanic", "eruption", "lava", "ash"],
            "LANDSLIDE": ["landslide", "mudslide", "rockslide", "avalanche"],
            
            # 기상재해
            "HURRICANE": ["hurricane", "typhoon", "cyclone", "tropical storm"],
            "TORNADO": ["tornado", "twister", "funnel cloud"],
            "FLOOD": ["flood", "flooding", "deluge", "inundation", "flash flood"],
            "DROUGHT": ["drought", "water shortage", "dry spell", "arid"],
            "WILDFIRE": ["wildfire", "forest fire", "bushfire", "blaze"],
            "BLIZZARD": ["blizzard", "snowstorm", "ice storm"],
            "HEATWAVE": ["heatwave", "extreme heat", "heat dome"],
            "COLDWAVE": ["cold wave", "freeze", "frost", "arctic blast"],
            
            # 분쟁/전쟁
            "WAR": ["war", "warfare", "military operation", "invasion"],
            "ARMED_CONFLICT": ["armed conflict", "fighting", "battle", "combat"],
            "CIVIL_WAR": ["civil war", "internal conflict", "insurgency"],
            "BORDER_CONFLICT": ["border conflict", "territorial dispute"],
            
            # 테러/폭력
            "TERRORISM": ["terrorism", "terrorist attack", "bomb", "bombing"],
            "SHOOTING": ["shooting", "gunfire", "gunman", "shooter", "mass shooting"],
            "HOSTAGE": ["hostage", "kidnapping", "abduction"],
            "ASSASSINATION": ["assassination", "targeted killing"],
            
            # 인도적 위기
            "REFUGEE_CRISIS": ["refugee", "displaced", "asylum seeker", "migration"],
            "FAMINE": ["famine", "hunger", "starvation", "food crisis"],
            "EPIDEMIC": ["epidemic", "outbreak", "disease", "virus", "pandemic"],
            "DISPLACEMENT": ["displacement", "evacuation", "forced migration"],
            
            # 산업/기술 재해
            "INDUSTRIAL_ACCIDENT": ["industrial accident", "factory explosion", "plant fire"],
            "CHEMICAL_LEAK": ["chemical leak", "toxic spill", "gas leak", "contamination"],
            "NUCLEAR_ACCIDENT": ["nuclear accident", "radiation leak", "reactor"],
            "OIL_SPILL": ["oil spill", "petroleum leak", "environmental disaster"],
            "BUILDING_COLLAPSE": ["building collapse", "structure collapse", "construction accident"],
            "BRIDGE_COLLAPSE": ["bridge collapse", "infrastructure failure"],
            "TRAIN_ACCIDENT": ["train accident", "railway crash", "derailment"],
            "PLANE_CRASH": ["plane crash", "aircraft crash", "aviation accident"],
            "SHIP_ACCIDENT": ["ship accident", "maritime disaster", "vessel sinking"],
            
            # 사회/정치 위기
            "POLITICAL_CRISIS": ["political crisis", "government crisis", "constitutional crisis"],
            "COUP": ["coup", "military takeover", "overthrow", "putsch"],
            "PROTEST": ["protest", "demonstration", "rally", "march", "uprising"],
            "RIOT": ["riot", "unrest", "violence", "clashes", "civil disorder"],
            "ETHNIC_CONFLICT": ["ethnic conflict", "sectarian violence", "communal violence"],
            
            # 기타
            "CYBER_ATTACK": ["cyber attack", "hacking", "data breach", "ransomware"],
            "INFRASTRUCTURE_FAILURE": ["power outage", "blackout", "grid failure"],
            "ECONOMIC_CRISIS": ["economic crisis", "financial collapse", "market crash"]
        }

    async def search_global_disasters_7days(self) -> List[Dict]:
        """7일치 글로벌 재해 검색 (토큰 최적화)"""
        return await self._batch_ai_search_optimized()

    async def search_with_query(self, query: str, max_results: int = 15) -> List[Dict]:
        """사용자 쿼리로 검색"""
        return await self._search_with_ai(query, max_results)

    async def _batch_ai_search_optimized(self) -> List[Dict]:
        """배치 처리로 토큰 효율성 극대화"""
        
        # 단일 프롬프트로 모든 카테고리 검색 (토큰 절약)
        batch_prompt = f"""
        최근 7일간 전 세계 주요 재해/분쟁 사건들을 검색해서 다음 JSON 형식으로 반환해주세요:
        
        [
            {{
                "title": "구체적 사건명",
                "location": "정확한 도시명, 국가명",
                "category": "카테고리코드",
                "severity": "HIGH|MEDIUM|LOW",
                "description": "간단한 설명 (1-2문장)",
                "date": "2025-01-XX",
                "source": "뉴스출처",
                "affected_people": 숫자_또는_null,
                "coordinates": {{"lat": 위도, "lng": 경도}}
            }}
        ]
        
        카테고리별 요청:
        1. 자연재해: 지진(5.0+), 홍수, 허리케인, 화산, 산불 등
        2. 분쟁/전쟁: 무력충돌, 테러공격, 폭격 등
        3. 인도적위기: 난민, 기근, 전염병 등
        4. 산업재해: 폭발, 화학유출, 건물붕괴 등
        5. 기타재해: 사이버공격, 정치위기 등
        
        조건:
        - 최근 7일 내 실제 발생 사건만
        - 도시 수준의 정확한 위치 필수
        - 각 카테고리당 6-8개씩, 총 40개 사건
        - 전 세계 고르게 분포 (아시아, 중동, 아프리카, 유럽, 아메리카)
        - 실제 좌표 포함 (추정 가능)
        """
        
        # Perplexity 우선 시도 (실시간 검색 최강)
        if self.perplexity_api_key:
            try:
                return await self._search_with_perplexity(batch_prompt)
            except Exception as e:
                logger.warning(f"Perplexity search failed: {e}")
        
        # OpenAI 대체
        if self.openai_api_key:
            try:
                return await self._search_with_openai_batch(batch_prompt)
            except Exception as e:
                logger.warning(f"OpenAI search failed: {e}")
        
        return []

    async def _search_with_perplexity(self, prompt: str) -> List[Dict]:
        """Perplexity로 실시간 검색"""
        
        headers = {
            "Authorization": f"Bearer {self.perplexity_api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "llama-3.1-sonar-large-128k-online",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 3000,
            "temperature": 0.2
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.perplexity.ai/chat/completions",
                    headers=headers,
                    json=data
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        content = result['choices'][0]['message']['content']
                        disasters = self._parse_ai_response(content)
                        
                        # 좌표 보강
                        enhanced_disasters = []
                        for disaster in disasters:
                            enhanced = await self._enhance_with_coordinates(disaster)
                            enhanced_disasters.append(enhanced)
                        
                        logger.info(f"🤖 Perplexity: Found {len(enhanced_disasters)} disasters")
                        return enhanced_disasters
        except Exception as e:
            logger.error(f"Perplexity API error: {e}")
            raise

    async def _search_with_openai_batch(self, prompt: str) -> List[Dict]:
        """OpenAI로 배치 검색"""
        
        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 3000,
            "temperature": 0.2
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=data
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        content = result['choices'][0]['message']['content']
                        disasters = self._parse_ai_response(content)
                        
                        # 좌표 보강
                        enhanced_disasters = []
                        for disaster in disasters:
                            enhanced = await self._enhance_with_coordinates(disaster)
                            enhanced_disasters.append(enhanced)
                        
                        logger.info(f"🤖 OpenAI: Found {len(enhanced_disasters)} disasters")
                        return enhanced_disasters
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise

    async def _search_with_ai(self, query: str, max_results: int) -> List[Dict]:
        """단일 쿼리 AI 검색"""
        
        prompt = f"""
        다음 키워드에 대한 최근 7일간 재해/분쟁 정보를 검색해주세요: "{query}"
        
        JSON 형식으로 {max_results}개 결과:
        [
            {{
                "title": "구체적 사건명",
                "location": "도시명, 국가명",
                "category": "적절한_카테고리",
                "severity": "HIGH|MEDIUM|LOW",
                "description": "간단한 설명",
                "date": "2025-01-XX",
                "source": "뉴스출처",
                "affected_people": 숫자_또는_null,
                "coordinates": {{"lat": 위도, "lng": 경도}}
            }}
        ]
        
        조건: 최근 7일, 실제 사건만, 정확한 위치
        """
        
        # Perplexity 우선
        if self.perplexity_api_key:
            try:
                return await self._search_with_perplexity(prompt)
            except Exception as e:
                logger.warning(f"Perplexity query search failed: {e}")
        
        # OpenAI 대체
        if self.openai_api_key:
            try:
                return await self._search_with_openai_batch(prompt)
            except Exception as e:
                logger.warning(f"OpenAI query search failed: {e}")
        
        return []

    def _parse_ai_response(self, content: str) -> List[Dict]:
        """AI 응답을 파싱해서 재해 데이터로 변환"""
        try:
            # JSON 추출
            start = content.find('[')
            end = content.rfind(']') + 1
            if start != -1 and end != 0:
                json_str = content[start:end]
                disasters_data = json.loads(json_str)
                
                # 데이터 정제 및 변환
                processed_disasters = []
                for item in disasters_data:
                    if isinstance(item, dict) and item.get('title'):
                        # 카테고리 정제
                        category = self._categorize_disaster_ai(
                            item.get('title', ''), 
                            item.get('description', '')
                        )
                        
                        disaster = {
                            "id": f"ai_{hashlib.md5(item.get('title', '').encode()).hexdigest()[:8]}",
                            "title": item.get('title', 'Unknown Disaster'),
                            "description": item.get('description', ''),
                            "location": item.get('location', 'Location TBD'),
                            "severity": item.get('severity', 'MEDIUM'),
                            "category": category,
                            "timestamp": self._parse_ai_timestamp(item.get('date')),
                            "source": f"AI-{item.get('source', 'Search')}",
                            "confidence": 0.8,
                            "affected_people": item.get('affected_people'),
                            "coordinates": item.get('coordinates', {"lat": 0.0, "lng": 0.0})
                        }
                        processed_disasters.append(disaster)
                
                return processed_disasters
                
        except json.JSONDecodeError as e:
            logger.error(f"AI response JSON parsing failed: {e}")
        except Exception as e:
            logger.error(f"AI response parsing error: {e}")
        
        return []

    def _categorize_disaster_ai(self, title: str, description: str) -> str:
        """AI 응답의 재해를 정확한 카테고리로 분류"""
        text = (title + " " + description).lower()
        
        # 키워드 매칭으로 카테고리 결정
        for category, keywords in self.disaster_categories.items():
            if any(keyword in text for keyword in keywords):
                return category
        
        return "OTHER"

    def _parse_ai_timestamp(self, date_str: str) -> int:
        """AI 응답의 날짜를 타임스탬프로 변환"""
        try:
            if date_str:
                # 다양한 날짜 형식 처리
                if "2025-" in date_str:
                    dt = datetime.strptime(date_str, "%Y-%m-%d")
                    return int(dt.timestamp())
        except:
            pass
        
        # 기본값: 1일 전
        return int((datetime.now() - timedelta(days=1)).timestamp())

    async def _enhance_with_coordinates(self, disaster: Dict) -> Dict:
        """재해 데이터에 정확한 좌표 추가"""
        
        # 이미 좌표가 있고 유효하면 그대로 사용
        coords = disaster.get('coordinates', {})
        if coords and coords.get('lat', 0) != 0 and coords.get('lng', 0) != 0:
            return disaster
        
        # 위치 기반으로 좌표 획득
        location = disaster.get('location', '')
        if location and location != 'Location TBD':
            try:
                # OpenStreetMap Nominatim으로 지오코딩
                precise_coords = await self._geocode_location(location)
                if precise_coords:
                    disaster['coordinates'] = precise_coords
                    return disaster
            except Exception as e:
                logger.warning(f"Geocoding failed for {location}: {e}")
        
        # AI로 좌표 추정 (최후 수단)
        if self.openai_api_key:
            try:
                estimated_coords = await self._ai_estimate_coordinates(location)
                disaster['coordinates'] = estimated_coords
            except Exception as e:
                logger.warning(f"AI coordinate estimation failed: {e}")
                disaster['coordinates'] = {"lat": 0.0, "lng": 0.0}
        
        return disaster

    async def _geocode_location(self, location: str) -> Optional[Dict[str, float]]:
        """OpenStreetMap으로 무료 지오코딩"""
        
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": location,
            "format": "json",
            "limit": 1,
            "addressdetails": 1
        }
        
        headers = {
            "User-Agent": "WrldRelief-Crisis-Monitor/1.0"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data:
                            return {
                                "lat": float(data[0]["lat"]),
                                "lng": float(data[0]["lon"])
                            }
        except Exception as e:
            logger.warning(f"Nominatim geocoding failed: {e}")
        
        return None

    async def _ai_estimate_coordinates(self, location: str) -> Dict[str, float]:
        """AI로 좌표 추정"""
        
        prompt = f"""
        다음 위치의 정확한 위도(latitude)와 경도(longitude)를 알려주세요:
        위치: {location}
        
        다음 JSON 형식으로만 답변하세요:
        {{"lat": 위도숫자, "lng": 경도숫자}}
        
        예시:
        - Istanbul, Turkey → {{"lat": 41.0082, "lng": 28.9784}}
        - Kyiv, Ukraine → {{"lat": 50.4501, "lng": 30.5234}}
        - Manila, Philippines → {{"lat": 14.5995, "lng": 120.9842}}
        """
        
        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 100,
            "temperature": 0.1
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=data
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        content = result['choices'][0]['message']['content']
                        
                        # JSON 파싱
                        coords_data = json.loads(content.strip())
                        return {
                            "lat": float(coords_data["lat"]),
                            "lng": float(coords_data["lng"])
                        }
        except Exception as e:
            logger.error(f"AI coordinate estimation failed: {e}")
        
        return {"lat": 0.0, "lng": 0.0}
