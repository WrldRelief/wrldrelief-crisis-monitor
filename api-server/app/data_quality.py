"""
🔍 Data Quality Enhancement Module
Advanced filtering and validation for disaster data
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class QualityScore:
    """Data quality assessment"""
    title_score: float
    location_score: float
    coordinates_score: float
    description_score: float
    overall_score: float

class DataQualityEnhancer:
    """Enhanced data quality validation and improvement"""
    
    def __init__(self):
        # Exclude non-disaster content patterns
        self.exclude_patterns = [
            # Political/Economic news
            "political crisis", "economic crisis", "trade dispute", "election results", 
            "court decision", "business news", "stock market", "parliament", "senate",
            "minister", "president", "prime minister", "government", "policy",
            "budget", "tax", "law", "legal", "judicial", "constitutional",
            
            # General news
            "sports", "entertainment", "celebrity", "movie", "music", "fashion",
            "technology", "software", "app", "website", "social media", "internet",
            "cryptocurrency", "bitcoin", "blockchain", "nft",
            
            # Non-emergency events
            "meeting", "conference", "summit", "visit", "tour", "ceremony",
            "anniversary", "celebration", "festival", "award", "prize", "competition",
            "interview", "statement", "announcement", "launch", "opening"
        ]
        
        # Enhanced disaster context patterns
        self.disaster_context_patterns = [
            # Natural disasters with context
            "earthquake magnitude", "earthquake strikes", "earthquake hits", "seismic activity",
            "wildfire burns", "wildfire spreads", "fire destroys", "forest fire",
            "flood waters", "flooding affects", "flood victims", "flash flood",
            "hurricane winds", "hurricane makes landfall", "storm surge", "tropical storm",
            "tornado touches down", "tornado destroys", "twister",
            "volcano erupts", "volcanic ash", "lava flows", "volcanic activity",
            "landslide buries", "mudslide hits", "rockslide",
            "drought affects", "water shortage", "severe drought",
            "blizzard hits", "snowstorm", "ice storm",
            
            # Conflict/Violence with humanitarian impact
            "civilians killed", "civilian casualties", "bombing attack", "bomb blast",
            "airstrike hits", "missile strike", "explosion kills", "terrorist attack",
            "refugee crisis", "displaced persons", "humanitarian aid", "humanitarian crisis",
            "evacuation ordered", "emergency declared", "state of emergency",
            "casualties reported", "people killed", "people injured", "victims",
            "rescue operations", "search and rescue", "emergency response",
            "disaster zone", "affected area", "damage assessment",
            
            # Infrastructure disasters
            "building collapse", "bridge collapse", "dam failure", "power outage",
            "train derailment", "plane crash", "ship sinking", "oil spill",
            "chemical leak", "gas explosion", "industrial accident",
            
            # Health emergencies
            "disease outbreak", "epidemic", "pandemic", "health emergency",
            "contamination", "poisoning", "radiation leak"
        ]
        
        # Invalid location patterns to exclude
        self.invalid_location_patterns = [
            r"^(However|Meanwhile|According|The|A|An|This|That|It|He|She|They)\s+",  # Sentence starters
            r"^(January|February|March|April|May|June|July|August|September|October|November|December)",  # Month names
            r"^[A-Z][a-z]+\s+(said|reported|announced|stated|declared|confirmed)",  # Person + verb
            r"^(News|Dawn|BBC|CNN|Reuters|AP|AFP|Bloomberg|Guardian)",  # News sources
            r"^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)",  # Day names
            r"^(Today|Yesterday|Tomorrow|Now|Then|Here|There)",  # Time/place adverbs
            r"^(Mr|Mrs|Ms|Dr|Prof|President|Minister|Secretary)\s+",  # Titles + names
            r"^\d+\s+(people|persons|civilians|residents|victims)",  # Numbers + people
            r"^(Breaking|Latest|Update|Report|Analysis|Opinion)",  # News prefixes
        ]
        
        # Major world locations with coordinates
        self.location_coordinates = {
            # Major cities
            "New York, USA": {"lat": 40.7128, "lng": -74.0060},
            "London, UK": {"lat": 51.5074, "lng": -0.1278},
            "Tokyo, Japan": {"lat": 35.6762, "lng": 139.6503},
            "Seoul, South Korea": {"lat": 37.5665, "lng": 126.9780},
            "Beijing, China": {"lat": 39.9042, "lng": 116.4074},
            "Moscow, Russia": {"lat": 55.7558, "lng": 37.6176},
            "Kiev, Ukraine": {"lat": 50.4501, "lng": 30.5234},
            "Istanbul, Turkey": {"lat": 41.0082, "lng": 28.9784},
            "Tehran, Iran": {"lat": 35.6892, "lng": 51.3890},
            "Damascus, Syria": {"lat": 33.5138, "lng": 36.2765},
            "Baghdad, Iraq": {"lat": 33.3152, "lng": 44.3661},
            "Kabul, Afghanistan": {"lat": 34.5553, "lng": 69.2075},
            "Islamabad, Pakistan": {"lat": 33.6844, "lng": 73.0479},
            "New Delhi, India": {"lat": 28.6139, "lng": 77.2090},
            "Jakarta, Indonesia": {"lat": -6.2088, "lng": 106.8456},
            "Manila, Philippines": {"lat": 14.5995, "lng": 120.9842},
            "Bangkok, Thailand": {"lat": 13.7563, "lng": 100.5018},
            "Yangon, Myanmar": {"lat": 16.8661, "lng": 96.1951},
            "Dhaka, Bangladesh": {"lat": 23.8103, "lng": 90.4125},
            "Kathmandu, Nepal": {"lat": 27.7172, "lng": 85.3240},
            "Colombo, Sri Lanka": {"lat": 6.9271, "lng": 79.8612},
            
            # Countries (capital coordinates)
            "Ukraine": {"lat": 50.4501, "lng": 30.5234},
            "Russia": {"lat": 55.7558, "lng": 37.6176},
            "Syria": {"lat": 33.5138, "lng": 36.2765},
            "Iraq": {"lat": 33.3152, "lng": 44.3661},
            "Afghanistan": {"lat": 34.5553, "lng": 69.2075},
            "Pakistan": {"lat": 33.6844, "lng": 73.0479},
            "India": {"lat": 28.6139, "lng": 77.2090},
            "China": {"lat": 39.9042, "lng": 116.4074},
            "Japan": {"lat": 35.6762, "lng": 139.6503},
            "Turkey": {"lat": 41.0082, "lng": 28.9784},
            "Iran": {"lat": 35.6892, "lng": 51.3890},
            "Israel": {"lat": 31.7683, "lng": 35.2137},
            "Palestine": {"lat": 31.9522, "lng": 35.2332},
            "Lebanon": {"lat": 33.8547, "lng": 35.8623},
            "Yemen": {"lat": 15.5527, "lng": 48.5164},
            "Sudan": {"lat": 15.5007, "lng": 32.5599},
            "Ethiopia": {"lat": 9.1450, "lng": 40.4897},
            "Myanmar": {"lat": 16.8661, "lng": 96.1951},
            "Bangladesh": {"lat": 23.8103, "lng": 90.4125},
            "Nepal": {"lat": 27.7172, "lng": 85.3240},
            "Sri Lanka": {"lat": 6.9271, "lng": 79.8612},
            
            # US States
            "California, USA": {"lat": 36.7783, "lng": -119.4179},
            "Texas, USA": {"lat": 31.9686, "lng": -99.9018},
            "Florida, USA": {"lat": 27.7663, "lng": -82.6404},
            "New York, USA": {"lat": 40.7128, "lng": -74.0060},
        }

    def is_actual_disaster(self, title: str, description: str) -> bool:
        """Check if content is actually disaster-related"""
        full_text = (title + " " + description).lower()
        
        # First check exclusion patterns
        for pattern in self.exclude_patterns:
            if pattern in full_text:
                logger.debug(f"Excluded by pattern '{pattern}': {title[:50]}")
                return False
        
        # Then check for disaster context patterns
        for pattern in self.disaster_context_patterns:
            if pattern in full_text:
                logger.debug(f"Matched disaster pattern '{pattern}': {title[:50]}")
                return True
        
        # Additional checks for conflict/humanitarian keywords
        conflict_indicators = [
            "killed", "dead", "casualties", "injured", "wounded", "missing",
            "destroyed", "damaged", "collapsed", "evacuated", "displaced",
            "emergency", "crisis", "disaster", "catastrophe", "tragedy"
        ]
        
        # Need at least 2 conflict indicators for non-natural disasters
        conflict_count = sum(1 for indicator in conflict_indicators if indicator in full_text)
        if conflict_count >= 2:
            logger.debug(f"Matched {conflict_count} conflict indicators: {title[:50]}")
            return True
        
        logger.debug(f"No disaster patterns matched: {title[:50]}")
        return False

    def clean_location(self, location: str) -> str:
        """Clean and validate location string"""
        if not location or location.strip() == "":
            return "Location TBD"
        
        location = location.strip()
        
        # Check for invalid patterns
        for pattern in self.invalid_location_patterns:
            if re.match(pattern, location, re.IGNORECASE):
                logger.debug(f"Invalid location pattern: {location}")
                return "Location TBD"
        
        # Remove common prefixes that aren't locations
        prefixes_to_remove = [
            "According to", "However,", "Meanwhile,", "The", "A", "An",
            "Breaking:", "Update:", "Latest:", "Report:", "News:"
        ]
        
        for prefix in prefixes_to_remove:
            if location.startswith(prefix):
                location = location[len(prefix):].strip()
        
        # If location is too short or too long, mark as TBD
        if len(location) < 3 or len(location) > 100:
            return "Location TBD"
        
        # Check if it's a valid location format
        if self._is_valid_location_format(location):
            return location
        else:
            return "Location TBD"

    def _is_valid_location_format(self, location: str) -> bool:
        """Check if location follows valid geographic patterns"""
        # Valid patterns: "City, Country", "State, Country", "Country"
        valid_patterns = [
            r'^[A-Z][a-zA-Z\s]+,\s*[A-Z][a-zA-Z\s]+$',  # City, Country
            r'^[A-Z][a-zA-Z\s]+$',  # Single location
        ]
        
        for pattern in valid_patterns:
            if re.match(pattern, location):
                return True
        
        return False

    def get_coordinates(self, location: str) -> Dict[str, float]:
        """Get coordinates for a location"""
        if location == "Location TBD" or not location:
            return {"lat": 0.0, "lng": 0.0}
        
        # Direct lookup
        if location in self.location_coordinates:
            return self.location_coordinates[location]
        
        # Try partial matching for countries
        location_lower = location.lower()
        for loc_key, coords in self.location_coordinates.items():
            if any(part.lower() in location_lower for part in loc_key.split(", ")):
                logger.debug(f"Partial match: {location} -> {loc_key}")
                return coords
        
        # Default coordinates (center of world)
        return {"lat": 0.0, "lng": 0.0}

    def calculate_quality_score(self, title: str, location: str, description: str, coordinates: Dict) -> QualityScore:
        """Calculate comprehensive quality score"""
        
        # Title quality (30%)
        title_score = 0.0
        if title and len(title) > 10:
            title_score += 0.5
        if self.is_actual_disaster(title, description):
            title_score += 0.5
        
        # Location quality (25%)
        location_score = 0.0
        if location and location != "Location TBD":
            location_score += 0.5
        if self._is_valid_location_format(location):
            location_score += 0.5
        
        # Coordinates quality (25%)
        coordinates_score = 0.0
        if coordinates and coordinates.get("lat", 0) != 0 and coordinates.get("lng", 0) != 0:
            coordinates_score = 1.0
        
        # Description quality (20%)
        description_score = 0.0
        if description and len(description) > 20:
            description_score += 0.5
        if len(description) > 100:
            description_score += 0.5
        
        # Overall score (weighted average)
        overall_score = (
            title_score * 0.30 +
            location_score * 0.25 +
            coordinates_score * 0.25 +
            description_score * 0.20
        )
        
        return QualityScore(
            title_score=title_score,
            location_score=location_score,
            coordinates_score=coordinates_score,
            description_score=description_score,
            overall_score=overall_score
        )

    def enhance_disaster_data(self, disaster_data: Dict) -> Dict:
        """Enhance disaster data quality"""
        # Clean location
        original_location = disaster_data.get("location", "")
        cleaned_location = self.clean_location(original_location)
        
        # Get coordinates
        coordinates = self.get_coordinates(cleaned_location)
        
        # Calculate quality score
        quality = self.calculate_quality_score(
            disaster_data.get("title", ""),
            cleaned_location,
            disaster_data.get("description", ""),
            coordinates
        )
        
        # Update disaster data
        enhanced_data = disaster_data.copy()
        enhanced_data["location"] = cleaned_location
        enhanced_data["coordinates"] = coordinates
        enhanced_data["quality_score"] = quality.overall_score
        
        logger.info(f"Enhanced data quality: {quality.overall_score:.2f} - {disaster_data.get('title', '')[:50]}")
        
        return enhanced_data

    def filter_high_quality_disasters(self, disasters: List[Dict], min_quality: float = 0.6) -> List[Dict]:
        """Filter disasters by quality score"""
        high_quality = []
        
        for disaster in disasters:
            enhanced = self.enhance_disaster_data(disaster)
            if enhanced.get("quality_score", 0) >= min_quality:
                high_quality.append(enhanced)
            else:
                logger.debug(f"Filtered low quality: {enhanced.get('quality_score', 0):.2f} - {disaster.get('title', '')[:50]}")
        
        logger.info(f"Quality filter: {len(high_quality)}/{len(disasters)} disasters passed (min quality: {min_quality})")
        return high_quality
