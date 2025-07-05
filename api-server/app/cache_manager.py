"""
📦 Simple File-based Disaster Cache Manager
가벼운 JSON 파일 기반 캐싱 시스템 (DB 없이)
"""

import json
import os
from datetime import datetime, timedelta
from typing import List
import asyncio
import logging
from dataclasses import asdict

from ai_search import DisasterInfo

logger = logging.getLogger(__name__)

class SimpleDisasterCache:
    """파일 기반 재해 데이터 캐시 매니저"""
    
    def __init__(self):
        self.cache_dir = "data"
        self.cache_file = f"{self.cache_dir}/disasters_cache.json"
        self.meta_file = f"{self.cache_dir}/cache_meta.json"
        
        # 디렉토리 생성
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # 메모리 캐시
        self.memory_cache = []
        self.last_update = None
        
    async def initialize(self):
        """시작시 파일에서 로드"""
        await self._load_from_file()
        
    async def get_disasters(self, days=7) -> List[DisasterInfo]:
        """캐시된 재해 데이터 반환 (7일 필터링)"""
        if not self.memory_cache:
            await self._load_from_file()
            
        # 7일 필터링
        cutoff_time = datetime.now() - timedelta(days=days)
        cutoff_timestamp = int(cutoff_time.timestamp())
        
        filtered = [
            d for d in self.memory_cache 
            if d.timestamp >= cutoff_timestamp
        ]
        
        return sorted(filtered, key=lambda x: x.timestamp, reverse=True)
    
    async def update_cache(self, new_disasters: List[DisasterInfo]) -> int:
        """캐시 업데이트 (중복 제거 + 자동 정리)"""
        
        # 기존 데이터 ID 세트
        existing_ids = {d.id for d in self.memory_cache}
        
        # 새로운 데이터만 추가
        added_count = 0
        for disaster in new_disasters:
            if disaster.id not in existing_ids:
                self.memory_cache.append(disaster)
                added_count += 1
        
        # 7일 이상 된 데이터 자동 정리
        cutoff_time = datetime.now() - timedelta(days=7)
        cutoff_timestamp = int(cutoff_time.timestamp())
        
        before_count = len(self.memory_cache)
        self.memory_cache = [
            d for d in self.memory_cache 
            if d.timestamp >= cutoff_timestamp
        ]
        cleaned_count = before_count - len(self.memory_cache)
        
        # 파일에 저장
        await self._save_to_file()
        
        self.last_update = datetime.now()
        
        logger.info(f"📦 Cache updated: +{added_count} new, -{cleaned_count} old, total: {len(self.memory_cache)}")
        
        return added_count
    
    async def _load_from_file(self):
        """파일에서 캐시 로드"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # DisasterInfo 객체로 변환
                disasters_data = data.get("disasters", [])
                self.memory_cache = []
                
                for item in disasters_data:
                    try:
                        # 좌표 데이터 처리
                        if 'coordinates' in item and item['coordinates']:
                            coords = item['coordinates']
                            if isinstance(coords, dict):
                                item['coordinates'] = coords
                            else:
                                item['coordinates'] = {"lat": 0.0, "lng": 0.0}
                        else:
                            item['coordinates'] = {"lat": 0.0, "lng": 0.0}
                        
                        disaster = DisasterInfo(**item)
                        self.memory_cache.append(disaster)
                    except Exception as e:
                        logger.warning(f"Failed to load disaster item: {e}")
                        continue
                
                # 메타데이터 로드
                if os.path.exists(self.meta_file):
                    with open(self.meta_file, 'r') as f:
                        meta = json.load(f)
                        last_update_str = meta.get("last_update")
                        if last_update_str:
                            self.last_update = datetime.fromisoformat(last_update_str)
                
                logger.info(f"📂 Loaded {len(self.memory_cache)} disasters from cache file")
            else:
                logger.info("📂 No cache file found, starting fresh")
                self.memory_cache = []
                
        except Exception as e:
            logger.error(f"❌ Failed to load cache: {e}")
            self.memory_cache = []
    
    async def _save_to_file(self):
        """캐시를 파일에 저장"""
        try:
            # 재해 데이터를 딕셔너리로 변환
            disasters_dict = []
            for disaster in self.memory_cache:
                disaster_dict = asdict(disaster)
                # 좌표 데이터 정리
                if not disaster_dict.get('coordinates'):
                    disaster_dict['coordinates'] = {"lat": 0.0, "lng": 0.0}
                disasters_dict.append(disaster_dict)
            
            # 캐시 데이터 저장
            cache_data = {
                "disasters": disasters_dict,
                "total_count": len(self.memory_cache),
                "saved_at": datetime.now().isoformat(),
                "version": "1.0"
            }
            
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            
            # 메타데이터 저장
            meta_data = {
                "last_update": self.last_update.isoformat() if self.last_update else datetime.now().isoformat(),
                "total_disasters": len(self.memory_cache),
                "cache_file_size": os.path.getsize(self.cache_file) if os.path.exists(self.cache_file) else 0
            }
            
            with open(self.meta_file, 'w') as f:
                json.dump(meta_data, f, indent=2)
                
            logger.debug(f"💾 Saved {len(self.memory_cache)} disasters to cache file")
            
        except Exception as e:
            logger.error(f"❌ Failed to save cache: {e}")
    
    def should_update(self, interval_minutes=10) -> bool:
        """업데이트가 필요한지 확인"""
        if not self.last_update:
            return True
            
        time_diff = datetime.now() - self.last_update
        return time_diff.total_seconds() > (interval_minutes * 60)
    
    def get_cache_stats(self) -> dict:
        """캐시 통계 정보"""
        return {
            "total_disasters": len(self.memory_cache),
            "last_update": self.last_update.isoformat() if self.last_update else None,
            "cache_file_exists": os.path.exists(self.cache_file),
            "cache_file_size": os.path.getsize(self.cache_file) if os.path.exists(self.cache_file) else 0,
            "oldest_disaster": min([d.timestamp for d in self.memory_cache]) if self.memory_cache else None,
            "newest_disaster": max([d.timestamp for d in self.memory_cache]) if self.memory_cache else None
        }
    
    async def force_refresh(self) -> int:
        """강제 캐시 새로고침"""
        from hybrid_search import HybridDisasterEngine
        
        logger.info("🔄 Force refreshing cache...")
        
        # 새로운 엔진 인스턴스로 데이터 수집
        engine = HybridDisasterEngine()
        fresh_disasters = await engine.get_initial_disasters(days=7)
        
        # 기존 캐시 클리어
        self.memory_cache = []
        
        # 새 데이터로 업데이트
        added_count = await self.update_cache(fresh_disasters)
        
        logger.info(f"✅ Force refresh complete: {added_count} disasters loaded")
        return added_count
    
    async def cleanup_old_data(self, days=7):
        """오래된 데이터 정리"""
        cutoff_time = datetime.now() - timedelta(days=days)
        cutoff_timestamp = int(cutoff_time.timestamp())
        
        before_count = len(self.memory_cache)
        self.memory_cache = [
            d for d in self.memory_cache 
            if d.timestamp >= cutoff_timestamp
        ]
        cleaned_count = before_count - len(self.memory_cache)
        
        if cleaned_count > 0:
            await self._save_to_file()
            logger.info(f"🧹 Cleaned up {cleaned_count} old disasters")
        
        return cleaned_count
