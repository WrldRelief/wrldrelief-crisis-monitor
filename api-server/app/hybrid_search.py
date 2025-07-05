"""
🔄 Hybrid Disaster Search Engine
기본 API + AI 검색을 결합한 하이브리드 엔진 (7일 최적화)
"""

import asyncio
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
import hashlib

from ai_search import DisasterSearchEngine, DisasterInfo
from ai_agent import AISearchAgent
from data_quality import DataQualityEnhancer

logger = logging.getLogger(__name__)

class HybridDisasterEngine:
    """하이브리드 재해 검색 엔진 (API + AI)"""
    
    def __init__(self):
        # 기존 API 엔진 (신뢰할 수 있는 기본 데이터)
        self.legacy_engine = DisasterSearchEngine()
        
        # AI 에이전트 (풍부한 보강 데이터)
        self.ai_agent = AISearchAgent()
        
        # 품질 개선기
        self.quality_enhancer = DataQualityEnhancer()
        
        # 7일 최적화 설정
        self.data_range_days = 7
        
    async def get_initial_disasters(self, days: int = 7) -> List[DisasterInfo]:
        """하이브리드 방식으로 7일치 재해 데이터 수집"""
        
        logger.info(f"🔄 Starting hybrid disaster collection for last {days} days...")
        
        try:
            # 1. 기본 신뢰할 수 있는 소스 (API 기반 - 80% 데이터)
            logger.info("📊 Collecting reliable API data...")
            reliable_tasks = [
                self.legacy_engine._get_usgs_all_earthquakes(),
                self.legacy_engine._get_reliefweb_disasters(days),
                self.legacy_engine._get_gdacs_alerts(),
                self.legacy_engine._get_week_news_disasters()
            ]
            
            # 2. AI 검색으로 최신 정보 보강 (20% 보강 데이터)
            logger.info("🤖 Enhancing with AI search...")
            ai_tasks = [
                self.ai_agent.search_global_disasters_7days()
            ]
            
            # 3. 병렬 실행으로 속도 최적화
            logger.info("⚡ Running parallel data collection...")
            reliable_results = await asyncio.gather(*reliable_tasks, return_exceptions=True)
            ai_results = await asyncio.gather(*ai_tasks, return_exceptions=True)
            
            # 4. 결과 병합
            all_disasters = []
            
            # API 데이터 추가
            for result in reliable_results:
                if isinstance(result, list):
                    all_disasters.extend(result)
                    logger.info(f"✅ Added {len(result)} disasters from API source")
                elif isinstance(result, Exception):
                    logger.warning(f"⚠️ API source failed: {result}")
            
            # AI 데이터 추가 및 변환
            for result in ai_results:
                if isinstance(result, list):
                    # AI 결과를 DisasterInfo로 변환
                    ai_disasters = [self._convert_ai_to_disaster_info(item) for item in result]
                    all_disasters.extend(ai_disasters)
                    logger.info(f"🤖 Added {len(ai_disasters)} disasters from AI search")
                elif isinstance(result, Exception):
                    logger.warning(f"⚠️ AI search failed: {result}")
            
            # 5. 7일 필터링
            cutoff_time = datetime.now() - timedelta(days=days)
            cutoff_timestamp = int(cutoff_time.timestamp())
            
            recent_disasters = [
                d for d in all_disasters 
                if d.timestamp >= cutoff_timestamp
            ]
            
            logger.info(f"📅 Filtered to {len(recent_disasters)} disasters from last {days} days")
            
            # 6. 중복 제거 및 품질 개선
            unique_disasters = self._deduplicate_disasters(recent_disasters)
            logger.info(f"🔄 Deduplicated to {len(unique_disasters)} unique disasters")
            
            # 7. 좌표 및 위치 정보 보강
            enhanced_disasters = []
            for disaster in unique_disasters:
                enhanced = await self._enhance_disaster_with_coordinates(disaster)
                enhanced_disasters.append(enhanced)
            
            # 8. 시간순 정렬 (최신순)
            sorted_disasters = sorted(enhanced_disasters, key=lambda x: x.timestamp, reverse=True)
            
            logger.info(f"✅ Hybrid collection complete: {len(sorted_disasters)} disasters")
            return sorted_disasters
            
        except Exception as e:
            logger.error(f"❌ Hybrid collection failed: {e}")
            return self._get_fallback_data()

    async def search_disasters(self, query: str, max_results: int = 20) -> List[DisasterInfo]:
        """하이브리드 검색 (API + AI)"""
        
        logger.info(f"🔍 Hybrid search for: {query}")
        
        try:
            # API 검색 + AI 검색 병렬 실행
            tasks = [
                self.legacy_engine.search_disasters(query, max_results//2),
                self._ai_search_with_query(query, max_results//2)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 결과 병합
            all_disasters = []
            for result in results:
                if isinstance(result, list):
                    all_disasters.extend(result)
                elif isinstance(result, Exception):
                    logger.warning(f"Search component failed: {result}")
            
            # 중복 제거 및 정렬
            unique_disasters = self._deduplicate_disasters(all_disasters)
            sorted_disasters = sorted(unique_disasters, key=lambda x: x.timestamp, reverse=True)
            
            # 좌표 보강
            enhanced_disasters = []
            for disaster in sorted_disasters[:max_results]:
                enhanced = await self._enhance_disaster_with_coordinates(disaster)
                enhanced_disasters.append(enhanced)
            
            logger.info(f"✅ Hybrid search complete: {len(enhanced_disasters)} results")
            return enhanced_disasters
            
        except Exception as e:
            logger.error(f"❌ Hybrid search failed: {e}")
            return self._get_fallback_data()

    async def _ai_search_with_query(self, query: str, max_results: int) -> List[DisasterInfo]:
        """AI 검색 결과를 DisasterInfo로 변환"""
        try:
            ai_results = await self.ai_agent.search_with_query(query, max_results)
            return [self._convert_ai_to_disaster_info(item) for item in ai_results]
        except Exception as e:
            logger.warning(f"AI query search failed: {e}")
            return []

    def _convert_ai_to_disaster_info(self, ai_item: Dict) -> DisasterInfo:
        """AI 검색 결과를 DisasterInfo 객체로 변환"""
        return DisasterInfo(
            id=ai_item.get('id', f"ai_{hashlib.md5(str(ai_item).encode()).hexdigest()[:8]}"),
            title=ai_item.get('title', 'Unknown Disaster'),
            description=ai_item.get('description', ''),
            location=ai_item.get('location', 'Location TBD'),
            severity=ai_item.get('severity', 'MEDIUM'),
            category=ai_item.get('category', 'OTHER'),
            timestamp=ai_item.get('timestamp', int(datetime.now().timestamp())),
            source=ai_item.get('source', 'AI-Search'),
            confidence=ai_item.get('confidence', 0.8),
            affected_people=ai_item.get('affected_people'),
            damage_estimate=ai_item.get('damage_estimate'),
            coordinates=ai_item.get('coordinates', {"lat": 0.0, "lng": 0.0})
        )

    async def _enhance_disaster_with_coordinates(self, disaster: DisasterInfo) -> DisasterInfo:
        """재해 데이터에 정확한 좌표 및 위치 정보 보강"""
        
        # 이미 유효한 좌표가 있으면 그대로 사용
        if (disaster.coordinates and 
            disaster.coordinates.get('lat', 0) != 0 and 
            disaster.coordinates.get('lng', 0) != 0):
            return disaster
        
        # 위치 정보가 부족하면 AI로 보강
        if disaster.location in ['Location TBD', 'Unknown Location', '']:
            try:
                # AI로 위치 추출 시도
                enhanced_location = await self._ai_extract_location(disaster)
                if enhanced_location != 'Location TBD':
                    disaster.location = enhanced_location
            except Exception as e:
                logger.warning(f"AI location extraction failed: {e}")
        
        # 좌표 정보 보강
        if disaster.location != 'Location TBD':
            try:
                # OpenStreetMap으로 지오코딩
                coords = await self.ai_agent._geocode_location(disaster.location)
                if coords:
                    disaster.coordinates = coords
                else:
                    # AI로 좌표 추정
                    coords = await self.ai_agent._ai_estimate_coordinates(disaster.location)
                    disaster.coordinates = coords
            except Exception as e:
                logger.warning(f"Coordinate enhancement failed for {disaster.location}: {e}")
                disaster.coordinates = {"lat": 0.0, "lng": 0.0}
        
        return disaster

    async def _ai_extract_location(self, disaster: DisasterInfo) -> str:
        """AI로 재해 정보에서 정확한 위치 추출"""
        
        if not self.ai_agent.openai_api_key:
            return disaster.location
        
        prompt = f"""
        다음 재해 정보에서 가장 정확하고 구체적인 위치를 추출해주세요:
        
        제목: {disaster.title}
        설명: {disaster.description}
        현재 위치: {disaster.location}
        카테고리: {disaster.category}
        
        요구사항:
        1. 도시 수준의 구체적인 위치 (예: "Istanbul, Turkey")
        2. 재해 맥락을 고려한 정확한 지명
        3. "Unknown" 또는 "TBD" 사용 금지
        4. 추정이라도 가장 가능성 높은 구체적 위치
        
        형식: "도시명, 국가명"으로만 답변하세요.
        """
        
        try:
            import aiohttp
            
            headers = {
                "Authorization": f"Bearer {self.ai_agent.openai_api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 50,
                "temperature": 0.1
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=data
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        location = result['choices'][0]['message']['content'].strip()
                        
                        # 유효성 검증
                        if len(location) > 3 and ',' in location:
                            return location
                        
        except Exception as e:
            logger.warning(f"AI location extraction failed: {e}")
        
        return disaster.location

    def _deduplicate_disasters(self, disasters: List[DisasterInfo]) -> List[DisasterInfo]:
        """중복 제거 (기존 로직 재사용 + 개선)"""
        seen_keys = set()
        unique_disasters = []
        
        for disaster in disasters:
            # 제목 + 위치 + 날짜 기반 중복 키 생성
            title_normalized = disaster.title.lower().strip()
            location_normalized = disaster.location.lower().strip()
            date_key = datetime.fromtimestamp(disaster.timestamp).strftime('%Y-%m-%d')
            
            duplicate_key = f"{title_normalized}_{location_normalized}_{date_key}"
            duplicate_key = ''.join(c for c in duplicate_key if c.isalnum() or c == '_')
            
            if duplicate_key not in seen_keys and len(title_normalized) > 5:
                seen_keys.add(duplicate_key)
                unique_disasters.append(disaster)
            else:
                logger.debug(f"Duplicate filtered: {disaster.title[:50]}")
        
        return unique_disasters

    def generate_blockchain_data(self, disaster: DisasterInfo) -> Dict:
        """블록체인 호환 데이터 생성 (좌표 포함)"""
        return {
            "id": disaster.id,
            "name": disaster.title,
            "description": disaster.description,
            "location": disaster.location,
            "coordinates": disaster.coordinates or {"lat": 0.0, "lng": 0.0},
            "start_date": disaster.timestamp,
            "end_date": 0,  # 진행중
            "image_url": "",
            "external_source": disaster.source,
            "status": 0,  # 활성
            "created_at": int(datetime.now().timestamp()),
            "updated_at": int(datetime.now().timestamp()),
            "created_by": "0x0000000000000000000000000000000000000000",
            "severity": disaster.severity,
            "category": disaster.category,
            "confidence": disaster.confidence,
            "affected_people": disaster.affected_people or 0,
            "damage_estimate": disaster.damage_estimate or "TBD"
        }

    def _get_fallback_data(self) -> List[DisasterInfo]:
        """폴백 데이터"""
        return [
            DisasterInfo(
                id="hybrid_fallback_001",
                title="Hybrid System Monitoring Active",
                description="Hybrid disaster monitoring system (API + AI) is active and searching for global events.",
                location="Global",
                severity="LOW",
                category="SYSTEM",
                timestamp=int(datetime.now().timestamp()),
                source="Hybrid-System",
                confidence=1.0,
                affected_people=0,
                damage_estimate="N/A",
                coordinates={"lat": 0.0, "lng": 0.0}
            )
        ]
