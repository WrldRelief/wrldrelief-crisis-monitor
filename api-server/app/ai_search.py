"""
🤖 AI-powered Global Disaster Search Engine
Real-time disaster monitoring with USGS, RSS feeds, and OpenAI integration
"""

import asyncio
import aiohttp
import feedparser
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import os
from dataclasses import dataclass, asdict
import re
import hashlib

# Import data quality enhancer
from data_quality import DataQualityEnhancer

logger = logging.getLogger(__name__)

@dataclass
class DisasterInfo:
    """Disaster information data class"""
    id: str
    title: str
    description: str
    location: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    category: str  # EARTHQUAKE, WILDFIRE, FLOOD, HURRICANE, etc.
    timestamp: int
    source: str
    confidence: float
    affected_people: Optional[int] = None
    damage_estimate: Optional[str] = None
    coordinates: Optional[Dict[str, float]] = None

class DisasterSearchEngine:
    """AI-powered global disaster search engine"""
    
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")
        
        # Initialize data quality enhancer
        self.quality_enhancer = DataQualityEnhancer()
        
        # RSS news feeds (no API key required) - EXPANDED FOR CONFLICTS
        self.news_feeds = [
            # General world news
            "http://feeds.bbci.co.uk/news/world/rss.xml",
            "http://rss.cnn.com/rss/edition.rss", 
            "https://feeds.reuters.com/reuters/topNews",
            "https://www.aljazeera.com/xml/rss/all.xml",
            
            # Conflict-specific feeds
            "https://news.un.org/en/rss.xml",  # UN News
            "https://www.crisisgroup.org/crisiswatch/rss",  # Crisis Group
            "https://reliefweb.int/rss.xml",  # ReliefWeb RSS
            "https://www.bbc.com/news/world-europe-60506682/rss.xml",  # BBC Ukraine
            "https://english.alarabiya.net/rss.xml",  # Middle East
            "https://www.middleeasteye.net/rss",  # Middle East Eye
            
            # Regional conflict feeds
            "https://www.kyivpost.com/rss",  # Ukraine news
            "https://www.dawn.com/feeds/home",  # Pakistan/South Asia
            "https://www.thehindu.com/news/national/feeder/default.rss",  # India
            "https://allafrica.com/tools/headlines/rdf/latest/headlines.rdf",  # Africa
            "https://www.africanews.com/api/en/rss"  # African conflicts
        ]
        
        # USGS earthquake APIs (no API key required) - FILTERED FOR 4.0+
        self.usgs_apis = {
            "significant_week": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_week.geojson",
            "significant_month": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_month.geojson",  # 30일 커버
            "4.5_week": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_week.geojson",  # 4.5+ magnitude
            "4.5_month": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_month.geojson"   # 4.5+ 30일
        }
        
        # ReliefWeb API (UN Official Disaster Database - no API key required)
        self.reliefweb_api = "https://api.reliefweb.int/v1/disasters"
        
        # NASA FIRMS Fire API (no API key required)
        self.nasa_firms_api = "https://firms.modaps.eosdis.nasa.gov/data/active_fire/shapes/zips/MODIS_C6_1_Global_24h.zip"
        
        # GDACS Global Disaster Alert API (no API key required)
        self.gdacs_api = "https://www.gdacs.org/xml/rss.xml"
        
        # Disaster + Conflict keywords for filtering (EXPANDED)
        self.disaster_keywords = [
            # Natural disasters
            "earthquake", "tsunami", "flood", "hurricane", "typhoon", "cyclone",
            "wildfire", "volcano", "landslide", "drought", "tornado", "blizzard",
            "emergency", "disaster", "crisis", "evacuation", "casualties", "damage",
            
            # War & Conflict
            "war", "conflict", "fighting", "battle", "combat", "warfare",
            "invasion", "occupation", "siege", "offensive", "ceasefire",
            
            # Attacks & Violence
            "attack", "bombing", "airstrike", "missile", "rocket", "drone",
            "explosion", "blast", "shooting", "gunfire", "artillery", "shelling",
            
            # Terrorism & Security
            "terrorism", "terrorist", "security", "violence", "insurgency",
            "militia", "rebel", "coup", "protest", "riot", "unrest",
            
            # Humanitarian Crisis
            "refugee", "displacement", "humanitarian", "killed", "wounded", 
            "missing", "civilian", "victim", "injured", "dead", "death",
            
            # Specific conflicts
            "ukraine", "russia", "syria", "gaza", "israel", "palestine",
            "yemen", "afghanistan", "iraq", "sudan", "myanmar", "ethiopia"
        ]
        
        # Enhanced location patterns
        self.location_patterns = [
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',  # City, Country
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:in|near)\s+([A-Z][a-z]+)\b',  # Location in Country
            r'\b([A-Z][a-z]+)\s+(?:state|province|region)\b',  # State/Province
        ]

    async def get_initial_disasters(self, days: int = 30) -> List[DisasterInfo]:
        """Get initial disaster data for the last N days"""
        try:
            logger.info(f"🔍 Loading initial disasters from last {days} days...")
            
            # Parallel data collection from multiple sources
            tasks = [
                self._get_usgs_all_earthquakes(),  # ALL earthquakes (not just significant)
                self._get_reliefweb_disasters(days),  # UN Official disaster database
                self._get_gdacs_alerts(),  # EU Global disaster alerts
                self._get_week_news_disasters(),
            ]
            
            # Add AI search if API key available
            if self.openai_api_key:
                tasks.append(self._get_ai_week_disasters(days))
            
            # Collect all results
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Combine results
            all_disasters = []
            for result in results:
                if isinstance(result, list):
                    all_disasters.extend(result)
                elif isinstance(result, Exception):
                    logger.warning(f"Data source error: {result}")
            
            # Filter by date range
            cutoff_time = datetime.now() - timedelta(days=days)
            cutoff_timestamp = int(cutoff_time.timestamp())
            
            recent_disasters = [
                d for d in all_disasters 
                if d.timestamp >= cutoff_timestamp
            ]
            
            # Remove duplicates and sort
            unique_disasters = self._deduplicate_disasters(recent_disasters)
            sorted_disasters = sorted(unique_disasters, key=lambda x: x.timestamp, reverse=True)
            
            # Enhance data quality
            enhanced_disasters = [self._enhance_disaster_data(d) for d in sorted_disasters]
            
            logger.info(f"✅ Loaded {len(enhanced_disasters)} disasters from last {days} days")
            return enhanced_disasters
            
        except Exception as e:
            logger.error(f"❌ Initial load failed: {e}")
            return self._get_fallback_data()

    async def search_disasters(self, query: str = "global disasters today", max_results: int = 20) -> List[DisasterInfo]:
        """Search for disasters with specific query"""
        try:
            logger.info(f"🔍 Searching disasters: {query}")
            
            # Parallel search across sources
            tasks = [
                self._search_usgs_earthquakes(),
                self._search_news_feeds(query),
            ]
            
            # Add AI search if available
            if self.openai_api_key:
                tasks.append(self._search_with_openai(query))
            
            # Collect results
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Combine and process
            all_disasters = []
            for result in results:
                if isinstance(result, list):
                    all_disasters.extend(result)
                elif isinstance(result, Exception):
                    logger.warning(f"Search error: {result}")
            
            # Remove duplicates and sort
            unique_disasters = self._deduplicate_disasters(all_disasters)
            sorted_disasters = sorted(unique_disasters, key=lambda x: x.timestamp, reverse=True)
            
            # Enhance data quality
            enhanced_disasters = [self._enhance_disaster_data(d) for d in sorted_disasters]
            
            logger.info(f"✅ Found {len(enhanced_disasters)} disasters")
            return enhanced_disasters[:max_results]
            
        except Exception as e:
            logger.error(f"❌ Search failed: {e}")
            return self._get_fallback_data()

    async def _get_usgs_week_earthquakes(self) -> List[DisasterInfo]:
        """Get earthquakes from USGS for the past week"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.usgs_apis["week"]) as response:
                    if response.status == 200:
                        data = await response.json()
                        earthquakes = []
                        
                        for feature in data.get('features', []):
                            props = feature.get('properties', {})
                            coords = feature.get('geometry', {}).get('coordinates', [])
                            
                            if len(coords) >= 2:
                                # Clean location name
                                place = props.get('place', '')
                                location = self._clean_location(place) if place else f"Lat: {coords[1]:.2f}, Lon: {coords[0]:.2f}"
                                
                                earthquake = DisasterInfo(
                                    id=f"usgs_{props.get('ids', hashlib.md5(str(props).encode()).hexdigest()[:8])}",
                                    title=f"Magnitude {props.get('mag', 'Unknown')} Earthquake",
                                    description=props.get('title', 'Earthquake detected by USGS monitoring network'),
                                    location=location,
                                    severity=self._get_earthquake_severity(props.get('mag', 0)),
                                    category="EARTHQUAKE",
                                    timestamp=int(props.get('time', 0) / 1000),
                                    source="USGS",
                                    confidence=0.95,
                                    affected_people=self._estimate_affected_people(props.get('mag', 0)),
                                    coordinates={"lat": coords[1], "lng": coords[0]} if len(coords) >= 2 else None
                                )
                                earthquakes.append(earthquake)
                        
                        logger.info(f"📊 USGS: Found {len(earthquakes)} earthquakes (week)")
                        return earthquakes
                        
        except Exception as e:
            logger.warning(f"USGS week search failed: {e}")
            return []

    async def _get_week_news_disasters(self) -> List[DisasterInfo]:
        """Get disaster news from RSS feeds for the past week"""
        disasters = []
        
        for feed_url in self.news_feeds:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(feed_url) as response:
                        if response.status == 200:
                            content = await response.text()
                            feed = feedparser.parse(content)
                            
                            # Check more entries for week data
                            for entry in feed.entries[:20]:  # Check more entries
                                full_text = entry.title + " " + entry.get('summary', '')
                                
                                # Use enhanced disaster filtering
                                if self.quality_enhancer.is_actual_disaster(entry.title, entry.get('summary', '')):
                                    # Parse entry date
                                    entry_time = self._parse_entry_time(entry)
                                    
                                    # Only include if within last week
                                    week_ago = datetime.now() - timedelta(days=7)
                                    if entry_time >= week_ago:
                                        # Create disaster with enhanced location and coordinates
                                        raw_location = self._extract_location_enhanced(full_text)
                                        cleaned_location = self.quality_enhancer.clean_location(raw_location)
                                        coordinates = self.quality_enhancer.get_coordinates(cleaned_location)
                                        
                                        disaster = DisasterInfo(
                                            id=f"news_{hashlib.md5(entry.link.encode()).hexdigest()[:8]}",
                                            title=entry.title,
                                            description=self._clean_description(entry.get('summary', entry.title)),
                                            location=cleaned_location,
                                            severity=self._analyze_severity(full_text),
                                            category=self._categorize_disaster(full_text),
                                            timestamp=int(entry_time.timestamp()),
                                            source=f"News-{feed.feed.get('title', 'Unknown')}",
                                            confidence=0.75,
                                            affected_people=self._estimate_people_from_text(full_text),
                                            coordinates=coordinates
                                        )
                                        disasters.append(disaster)
                            
            except Exception as e:
                logger.warning(f"News feed {feed_url} failed: {e}")
                continue
        
        logger.info(f"📰 News: Found {len(disasters)} disaster news (week)")
        return disasters

    async def _get_ai_week_disasters(self, days: int = 7) -> List[DisasterInfo]:
        """Get disasters from AI analysis for the past week"""
        if not self.openai_api_key:
            return []
            
        try:
            prompt = f"""
            Analyze major disasters and emergencies from the last {days} days worldwide. 
            Focus on significant events with clear impact and location data.
            
            Return a JSON array with this exact format:
            [
                {{
                    "title": "Specific disaster title (e.g., 'Magnitude 7.2 Earthquake Strikes Turkey')",
                    "description": "Detailed 2-sentence description with impact details",
                    "location": "Specific City, Country (never 'Unknown' - use your knowledge)",
                    "severity": "LOW|MEDIUM|HIGH|CRITICAL",
                    "category": "EARTHQUAKE|WILDFIRE|FLOOD|HURRICANE|VOLCANO|TORNADO|DROUGHT|OTHER",
                    "source": "Specific news source or agency",
                    "confidence": 0.8,
                    "affected_people": estimated_number_or_null,
                    "damage_estimate": "specific amount like '$50 million' or 'TBD'",
                    "coordinates": {{"lat": 0.0, "lng": 0.0}}
                }}
            ]
            
            Requirements:
            - Only include real, verified disasters from last {days} days
            - Always provide specific location (city, country)
            - Include estimated impact numbers when possible
            - Focus on major events with significant impact
            - Maximum 15 disasters
            """
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.openai_api_key}",
                    "Content-Type": "application/json"
                }
                
                data = {
                    "model": "gpt-3.5-turbo",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 2000,
                    "temperature": 0.2
                }
                
                async with session.post("https://api.openai.com/v1/chat/completions", 
                                      headers=headers, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        content = result['choices'][0]['message']['content']
                        
                        # Extract JSON from response
                        try:
                            # Find JSON array in response
                            start = content.find('[')
                            end = content.rfind(']') + 1
                            if start != -1 and end != 0:
                                json_str = content[start:end]
                                disasters_data = json.loads(json_str)
                                
                                disasters = []
                                for item in disasters_data:
                                    disaster = DisasterInfo(
                                        id=f"ai_{hashlib.md5(item.get('title', '').encode()).hexdigest()[:8]}",
                                        title=item.get('title', 'Unknown Disaster'),
                                        description=item.get('description', ''),
                                        location=item.get('location', 'Location TBD'),
                                        severity=item.get('severity', 'MEDIUM'),
                                        category=item.get('category', 'OTHER'),
                                        timestamp=int(datetime.now().timestamp()) - (24 * 3600),  # Assume 1 day ago
                                        source=f"AI-{item.get('source', 'Analysis')}",
                                        confidence=item.get('confidence', 0.8),
                                        affected_people=item.get('affected_people'),
                                        damage_estimate=item.get('damage_estimate'),
                                        coordinates=item.get('coordinates')
                                    )
                                    disasters.append(disaster)
                                
                                logger.info(f"🤖 OpenAI: Found {len(disasters)} disasters (week)")
                                return disasters
                                
                        except json.JSONDecodeError as e:
                            logger.warning(f"OpenAI JSON parsing failed: {e}")
                            
        except Exception as e:
            logger.warning(f"OpenAI week search failed: {e}")
            
        return []

    async def _get_usgs_all_earthquakes(self) -> List[DisasterInfo]:
        """Get earthquakes 4.0+ from USGS for 30 days"""
        earthquakes = []
        
        # Use only filtered feeds for 4.0+ earthquakes and 30-day coverage
        feeds_to_try = ["significant_week", "significant_month", "4.5_week", "4.5_month"]
        
        for feed_name in feeds_to_try:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(self.usgs_apis[feed_name]) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            for feature in data.get('features', []):
                                props = feature.get('properties', {})
                                coords = feature.get('geometry', {}).get('coordinates', [])
                                magnitude = props.get('mag', 0)
                                
                                # FILTER: Only include earthquakes 4.0 and above
                                if magnitude >= 4.0 and len(coords) >= 2:
                                    # Clean location name
                                    place = props.get('place', '')
                                    location = self._clean_location(place) if place else f"Lat: {coords[1]:.2f}, Lon: {coords[0]:.2f}"
                                    
                                    earthquake = DisasterInfo(
                                        id=f"usgs_{feed_name}_{props.get('ids', hashlib.md5(str(props).encode()).hexdigest()[:8])}",
                                        title=f"Magnitude {magnitude} Earthquake",
                                        description=props.get('title', 'Earthquake detected by USGS monitoring network'),
                                        location=location,
                                        severity=self._get_earthquake_severity(magnitude),
                                        category="EARTHQUAKE",
                                        timestamp=int(props.get('time', 0) / 1000),
                                        source=f"USGS-{feed_name.upper()}",
                                        confidence=0.95,
                                        affected_people=self._estimate_affected_people(magnitude),
                                        coordinates={"lat": coords[1], "lng": coords[0]} if len(coords) >= 2 else None
                                    )
                                    earthquakes.append(earthquake)
                            
                            logger.info(f"📊 USGS-{feed_name}: Found {len([f for f in data.get('features', []) if f.get('properties', {}).get('mag', 0) >= 4.0])} earthquakes (4.0+)")
                            
            except Exception as e:
                logger.warning(f"USGS {feed_name} search failed: {e}")
                continue
        
        logger.info(f"📊 USGS Total: Found {len(earthquakes)} earthquakes (4.0+ magnitude)")
        return earthquakes

    async def _get_reliefweb_disasters(self, days: int = 7) -> List[DisasterInfo]:
        """Get disasters from ReliefWeb (UN Official Database)"""
        try:
            # Calculate date filter for last N days
            cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            # Corrected ReliefWeb API parameters format
            params = {
                'appname': 'crisis-monitor',
                'limit': 50,
                'sort[]': 'date:desc',
                'fields[include][]': ['id', 'title', 'body', 'country', 'date', 'disaster_type'],
                'filter[field]': 'date.created',
                'filter[value][from]': cutoff_date
            }
            
            headers = {
                'User-Agent': 'Crisis-Monitor/1.0 (https://github.com/crisis-monitor)',
                'Accept': 'application/json'
            }
            
            timeout = aiohttp.ClientTimeout(total=30)
            
            async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
                logger.info(f"🌍 ReliefWeb: Requesting disasters from {cutoff_date}")
                
                async with session.get(self.reliefweb_api, params=params) as response:
                    logger.info(f"🌍 ReliefWeb: Response status {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        disasters = []
                        
                        total_count = data.get('totalCount', 0)
                        items = data.get('data', [])
                        logger.info(f"🌍 ReliefWeb: API returned {len(items)} items (total: {total_count})")
                        
                        for item in items:
                            fields = item.get('fields', {})
                            
                            # Extract location
                            countries = fields.get('country', [])
                            if countries and isinstance(countries, list):
                                location = ', '.join([c.get('name', '') for c in countries if isinstance(c, dict)])
                            else:
                                location = 'Global'
                            
                            # Extract disaster type and map to category
                            disaster_types = fields.get('disaster_type', [])
                            category = self._map_reliefweb_type(disaster_types)
                            
                            # Parse date
                            date_info = fields.get('date', {})
                            if isinstance(date_info, dict):
                                date_str = date_info.get('created', '')
                            else:
                                date_str = ''
                            timestamp = self._parse_reliefweb_date(date_str)
                            
                            # Get title and description
                            title = fields.get('title', 'Unknown Disaster')
                            body = fields.get('body', '')
                            description = self._clean_description(body) if body else 'No description available'
                            
                            disaster = DisasterInfo(
                                id=f"reliefweb_{item.get('id', hashlib.md5(str(fields).encode()).hexdigest()[:8])}",
                                title=title,
                                description=description,
                                location=location,
                                severity=self._analyze_severity(description),
                                category=category,
                                timestamp=timestamp,
                                source="ReliefWeb-UN",
                                confidence=0.90,
                                affected_people=self._estimate_people_from_text(description)
                            )
                            disasters.append(disaster)
                        
                        logger.info(f"🌍 ReliefWeb: Successfully processed {len(disasters)} disasters")
                        return disasters
                    else:
                        error_text = await response.text()
                        logger.error(f"🌍 ReliefWeb: HTTP {response.status} - {error_text[:200]}")
                        return []
                        
        except asyncio.TimeoutError:
            logger.warning("🌍 ReliefWeb: Request timeout")
            return []
        except Exception as e:
            logger.error(f"🌍 ReliefWeb: Unexpected error - {type(e).__name__}: {e}")
            return []

    async def _get_gdacs_alerts(self) -> List[DisasterInfo]:
        """Get alerts from GDACS (Global Disaster Alert and Coordination System)"""
        try:
            headers = {
                'User-Agent': 'Crisis-Monitor/1.0 (https://github.com/crisis-monitor)',
                'Accept': 'application/rss+xml, application/xml, text/xml'
            }
            
            timeout = aiohttp.ClientTimeout(total=30)
            
            # Try with SSL verification disabled for GDACS
            connector = aiohttp.TCPConnector(ssl=False)
            
            async with aiohttp.ClientSession(
                timeout=timeout, 
                headers=headers,
                connector=connector
            ) as session:
                logger.info("🚨 GDACS: Requesting global disaster alerts...")
                
                async with session.get(self.gdacs_api) as response:
                    logger.info(f"🚨 GDACS: Response status {response.status}")
                    
                    if response.status == 200:
                        content = await response.text()
                        feed = feedparser.parse(content)
                        disasters = []
                        
                        logger.info(f"🚨 GDACS: RSS feed parsed, found {len(feed.entries)} entries")
                        
                        for entry in feed.entries:
                            # Parse GDACS specific data
                            title = entry.title
                            description = entry.get('summary', entry.title)
                            
                            # Extract severity from GDACS alert levels
                            severity = self._parse_gdacs_severity(title, description)
                            
                            # Extract location from title/description
                            location = self._extract_location_enhanced(title + " " + description)
                            
                            # Parse entry time
                            entry_time = self._parse_entry_time(entry)
                            
                            disaster = DisasterInfo(
                                id=f"gdacs_{hashlib.md5(entry.link.encode()).hexdigest()[:8]}",
                                title=title,
                                description=self._clean_description(description),
                                location=location,
                                severity=severity,
                                category=self._categorize_disaster(title + " " + description),
                                timestamp=int(entry_time.timestamp()),
                                source="GDACS-EU",
                                confidence=0.85,
                                affected_people=self._estimate_people_from_text(description)
                            )
                            disasters.append(disaster)
                        
                        logger.info(f"🚨 GDACS: Successfully processed {len(disasters)} alerts")
                        return disasters
                    else:
                        error_text = await response.text()
                        logger.error(f"🚨 GDACS: HTTP {response.status} - {error_text[:200]}")
                        return []
                        
        except asyncio.TimeoutError:
            logger.warning("🚨 GDACS: Request timeout")
            return []
        except Exception as e:
            logger.error(f"🚨 GDACS: Unexpected error - {type(e).__name__}: {e}")
            return []

    async def _search_usgs_earthquakes(self) -> List[DisasterInfo]:
        """Search current USGS earthquakes"""
        return await self._get_usgs_all_earthquakes()

    async def _search_news_feeds(self, query: str) -> List[DisasterInfo]:
        """Search news feeds with query"""
        return await self._get_week_news_disasters()

    async def _search_with_openai(self, query: str) -> List[DisasterInfo]:
        """Search with OpenAI using specific query"""
        if not self.openai_api_key:
            return []
            
        try:
            prompt = f"""
            Search for recent disasters related to: "{query}"
            
            Return JSON array of current/recent disasters:
            [
                {{
                    "title": "Specific disaster title",
                    "description": "Detailed description",
                    "location": "City, Country",
                    "severity": "LOW|MEDIUM|HIGH|CRITICAL",
                    "category": "EARTHQUAKE|WILDFIRE|FLOOD|HURRICANE|OTHER",
                    "source": "News source",
                    "confidence": 0.8,
                    "affected_people": number_or_null
                }}
            ]
            
            Focus on real, current events only.
            """
            
            # Similar implementation to _get_ai_week_disasters but with query focus
            # ... (implementation similar to above)
            
        except Exception as e:
            logger.warning(f"OpenAI query search failed: {e}")
            
        return []

    def generate_blockchain_data(self, disaster: DisasterInfo) -> Dict:
        """Generate blockchain-ready data for a single disaster"""
        return {
            "id": disaster.id,
            "name": disaster.title,
            "description": disaster.description,
            "location": disaster.location,
            "start_date": disaster.timestamp,
            "end_date": 0,  # Ongoing or unknown
            "image_url": "",  # Could be enhanced later
            "external_source": disaster.source,
            "status": 0,  # Active
            "created_at": int(datetime.now().timestamp()),
            "updated_at": int(datetime.now().timestamp()),
            "created_by": "0x0000000000000000000000000000000000000000",
            "severity": disaster.severity,
            "category": disaster.category,
            "confidence": disaster.confidence,
            "affected_people": disaster.affected_people or 0,
            "damage_estimate": disaster.damage_estimate or "TBD",
            "coordinates": disaster.coordinates or {"lat": 0.0, "lng": 0.0}
        }

    def _enhance_disaster_data(self, disaster: DisasterInfo) -> DisasterInfo:
        """Enhance disaster data quality"""
        # Clean and enhance location
        if disaster.location == "Unknown Location" or not disaster.location:
            disaster.location = self._infer_location_from_title(disaster.title)
        
        # Ensure damage estimate
        if not disaster.damage_estimate:
            disaster.damage_estimate = self._estimate_damage(disaster.severity, disaster.affected_people)
        
        # Ensure affected people estimate
        if not disaster.affected_people:
            disaster.affected_people = self._estimate_people_from_severity(disaster.severity)
        
        return disaster

    def _clean_location(self, place: str) -> str:
        """Clean USGS place string to readable location"""
        if not place:
            return "Location TBD"
        
        # Remove distance and direction info
        place = re.sub(r'^\d+km\s+[NSEW]+\s+of\s+', '', place)
        place = re.sub(r'^\d+\.\d+km\s+[NSEW]+\s+of\s+', '', place)
        
        return place.strip()

    def _extract_location_enhanced(self, text: str) -> str:
        """Enhanced location extraction from text"""
        # Try regex patterns first
        for pattern in self.location_patterns:
            matches = re.findall(pattern, text)
            if matches:
                if isinstance(matches[0], tuple):
                    return f"{matches[0][0]}, {matches[0][1]}"
                else:
                    return matches[0]
        
        # Fallback to keyword matching
        countries = [
            "Afghanistan", "Albania", "Algeria", "Argentina", "Armenia", "Australia",
            "Austria", "Azerbaijan", "Bangladesh", "Belgium", "Bolivia", "Brazil",
            "Bulgaria", "Cambodia", "Canada", "Chile", "China", "Colombia", "Croatia",
            "Czech Republic", "Denmark", "Ecuador", "Egypt", "Finland", "France",
            "Germany", "Greece", "Guatemala", "Hungary", "Iceland", "India", "Indonesia",
            "Iran", "Iraq", "Ireland", "Israel", "Italy", "Japan", "Jordan", "Kazakhstan",
            "Kenya", "South Korea", "Lebanon", "Malaysia", "Mexico", "Morocco", "Nepal",
            "Netherlands", "New Zealand", "Norway", "Pakistan", "Peru", "Philippines",
            "Poland", "Portugal", "Romania", "Russia", "Saudi Arabia", "Serbia",
            "Singapore", "Slovakia", "Slovenia", "South Africa", "Spain", "Sri Lanka",
            "Sweden", "Switzerland", "Syria", "Taiwan", "Thailand", "Turkey", "Ukraine",
            "United Kingdom", "United States", "USA", "Venezuela", "Vietnam"
        ]
        
        text_lower = text.lower()
        for country in countries:
            if country.lower() in text_lower:
                return country
        
        return "Location TBD"

    def _parse_entry_time(self, entry) -> datetime:
        """Parse RSS entry time"""
        try:
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                return datetime(*entry.published_parsed[:6])
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                return datetime(*entry.updated_parsed[:6])
        except:
            pass
        
        return datetime.now()

    def _clean_description(self, description: str) -> str:
        """Clean and truncate description"""
        if not description:
            return "No description available"
        
        # Remove HTML tags
        description = re.sub(r'<[^>]+>', '', description)
        
        # Truncate to reasonable length
        if len(description) > 200:
            description = description[:197] + "..."
        
        return description.strip()

    def _estimate_people_from_text(self, text: str) -> Optional[int]:
        """Estimate affected people from text"""
        # Look for numbers followed by people-related words
        patterns = [
            r'(\d+(?:,\d+)*)\s+(?:people|persons|residents|evacuated|affected|displaced)',
            r'(\d+(?:,\d+)*)\s+(?:dead|killed|casualties|injured|missing)',
            r'(\d+(?:,\d+)*)\s+(?:thousand|million)\s+(?:people|affected)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text.lower())
            if matches:
                try:
                    number = int(matches[0].replace(',', ''))
                    return number
                except:
                    continue
        
        return None

    def _estimate_damage(self, severity: str, affected_people: Optional[int]) -> str:
        """Estimate damage based on severity and affected people"""
        if severity == "CRITICAL":
            return "Over $1 billion"
        elif severity == "HIGH":
            return "$100 million - $1 billion"
        elif severity == "MEDIUM":
            return "$10 million - $100 million"
        else:
            return "Under $10 million"

    def _estimate_people_from_severity(self, severity: str) -> int:
        """Estimate affected people from severity"""
        if severity == "CRITICAL":
            return 100000
        elif severity == "HIGH":
            return 50000
        elif severity == "MEDIUM":
            return 10000
        else:
            return 1000

    def _infer_location_from_title(self, title: str) -> str:
        """Infer location from disaster title"""
        return self._extract_location_enhanced(title)

    def _is_disaster_news(self, text: str) -> bool:
        """Check if text is disaster-related news"""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.disaster_keywords)

    def _analyze_severity(self, text: str) -> str:
        """Analyze severity from text"""
        text_lower = text.lower()
        
        critical_words = ["catastrophic", "devastating", "major", "massive", "deadly", "fatal"]
        high_words = ["severe", "significant", "serious", "dangerous", "critical"]
        medium_words = ["moderate", "considerable", "notable"]
        
        if any(word in text_lower for word in critical_words):
            return "CRITICAL"
        elif any(word in text_lower for word in high_words):
            return "HIGH"
        elif any(word in text_lower for word in medium_words):
            return "MEDIUM"
        else:
            return "LOW"

    def _categorize_disaster(self, text: str) -> str:
        """Categorize disaster from text"""
        text_lower = text.lower()
        
        categories = {
            "EARTHQUAKE": ["earthquake", "quake", "seismic", "tremor"],
            "WILDFIRE": ["fire", "wildfire", "blaze", "burn"],
            "FLOOD": ["flood", "flooding", "deluge", "inundation"],
            "HURRICANE": ["hurricane", "typhoon", "cyclone", "storm"],
            "VOLCANO": ["volcano", "volcanic", "eruption", "lava"],
            "TORNADO": ["tornado", "twister"],
            "DROUGHT": ["drought", "dry", "water shortage"]
        }
        
        for category, keywords in categories.items():
            if any(keyword in text_lower for keyword in keywords):
                return category
        
        return "OTHER"

    def _get_earthquake_severity(self, magnitude: float) -> str:
        """Get earthquake severity from magnitude"""
        if magnitude >= 7.0:
            return "CRITICAL"
        elif magnitude >= 6.0:
            return "HIGH"
        elif magnitude >= 5.0:
            return "MEDIUM"
        else:
            return "LOW"

    def _estimate_affected_people(self, magnitude: float) -> int:
        """Estimate affected people from earthquake magnitude"""
        if magnitude >= 7.0:
            return 100000
        elif magnitude >= 6.0:
            return 50000
        elif magnitude >= 5.0:
            return 10000
        else:
            return 1000

    def _deduplicate_disasters(self, disasters: List[DisasterInfo]) -> List[DisasterInfo]:
        """Remove duplicate disasters"""
        seen_titles = set()
        unique_disasters = []
        
        for disaster in disasters:
            # Create a normalized key for comparison
            title_key = re.sub(r'[^\w\s]', '', disaster.title.lower()).strip()
            title_key = ' '.join(title_key.split())  # Normalize whitespace
            
            if title_key not in seen_titles and len(title_key) > 5:  # Avoid very short titles
                seen_titles.add(title_key)
                unique_disasters.append(disaster)
        
        return unique_disasters

    def _map_reliefweb_type(self, disaster_types: List[Dict]) -> str:
        """Map ReliefWeb disaster types to our categories"""
        if not disaster_types:
            return "OTHER"
        
        type_mapping = {
            "earthquake": "EARTHQUAKE",
            "flood": "FLOOD", 
            "drought": "DROUGHT",
            "cyclone": "HURRICANE",
            "hurricane": "HURRICANE",
            "typhoon": "HURRICANE",
            "wildfire": "WILDFIRE",
            "fire": "WILDFIRE",
            "volcano": "VOLCANO",
            "landslide": "LANDSLIDE",
            "tsunami": "TSUNAMI"
        }
        
        for disaster_type in disaster_types:
            type_name = disaster_type.get('name', '').lower()
            for key, category in type_mapping.items():
                if key in type_name:
                    return category
        
        return "OTHER"

    def _parse_reliefweb_date(self, date_str: str) -> int:
        """Parse ReliefWeb date string to timestamp"""
        try:
            if date_str:
                # ReliefWeb uses ISO format: 2025-01-01T00:00:00+00:00
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                return int(dt.timestamp())
        except:
            pass
        
        return int(datetime.now().timestamp())

    def _parse_gdacs_severity(self, title: str, description: str) -> str:
        """Parse GDACS alert severity levels"""
        text = (title + " " + description).lower()
        
        if any(word in text for word in ["red", "extreme", "very high"]):
            return "CRITICAL"
        elif any(word in text for word in ["orange", "high", "severe"]):
            return "HIGH"
        elif any(word in text for word in ["yellow", "medium", "moderate"]):
            return "MEDIUM"
        else:
            return "LOW"

    def _get_fallback_data(self) -> List[DisasterInfo]:
        """Fallback data when all sources fail"""
        return [
            DisasterInfo(
                id="fallback_001",
                title="System Monitoring Active",
                description="Disaster monitoring system is active and searching for global events.",
                location="Global",
                severity="LOW",
                category="SYSTEM",
                timestamp=int(datetime.now().timestamp()),
                source="System",
                confidence=1.0,
                affected_people=0,
                damage_estimate="N/A"
            )
        ]
