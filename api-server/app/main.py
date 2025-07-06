"""
🌍 WRLD Relief Crisis Monitor - Integrated Dashboard with AI Agent
Real-time Global Disaster Monitoring with Natural Language Search
"""

from fastapi import FastAPI, HTTPException, Path
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import asyncio
import logging
from datetime import datetime
import json
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from hybrid_search import HybridDisasterEngine
from ai_search import DisasterInfo
from cache_manager import SimpleDisasterCache

# Optional blockchain import
try:
    from blockchain import DisasterUploader
    BLOCKCHAIN_AVAILABLE = True
except ImportError as e:
    logger.warning(f"⚠️ Blockchain module not available: {e}")
    DisasterUploader = None
    BLOCKCHAIN_AVAILABLE = False

# FastAPI app
app = FastAPI(
    title="🌍 WRLD Relief Crisis Monitor",
    description="Real-time Global Disaster Monitoring Dashboard with AI Agent",
    version="2.0.0"
)

class SearchRequest(BaseModel):
    query: Optional[str] = "global disasters today"
    max_results: Optional[int] = 20

class DisasterQueryRequest(BaseModel):
    query: str = "global disasters today"
    max_results: int = 10
    requester: str = "web_user"

class DisasterResult(BaseModel):
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

class DisasterResults(BaseModel):
    disasters: List[DisasterResult]
    total_count: int
    query: str
    searched_at: int
    agent_name: str = "WRLD Relief Disaster Agent"

# Global instances
search_engine = HybridDisasterEngine()
disaster_cache = SimpleDisasterCache()
current_disasters = []

@app.on_event("startup")
async def startup_event():
    """Application startup initialization"""
    logger.info("🚀 Starting WRLD Relief Crisis Monitor...")
    
    await disaster_cache.initialize()
    cached_disasters = await disaster_cache.get_disasters(days=7)
    
    if len(cached_disasters) < 50 or disaster_cache.should_update():
        logger.info("🔄 Fetching fresh data...")
        fresh_disasters = await search_engine.get_initial_disasters(days=7)
        await disaster_cache.update_cache(fresh_disasters)
        
    global current_disasters
    current_disasters = await disaster_cache.get_disasters(days=7)
    
    logger.info(f"✅ Dashboard ready! Loaded {len(current_disasters)} disasters")

@app.get("/")
async def integrated_dashboard():
    """Integrated dashboard with AI Agent functionality"""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>🌍 WRLD Relief Crisis Monitor</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                margin: 0; 
                padding: 20px; 
                background-color: #f5f5f5;
            }
            .container { max-width: 1400px; margin: 0 auto; }
            .header { 
                text-align: center; 
                margin-bottom: 30px; 
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .status-bar {
                background: #e8f5e8;
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 20px;
                border-left: 4px solid #28a745;
            }
            .search-tabs {
                background: white;
                border-radius: 10px;
                margin-bottom: 20px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                overflow: hidden;
            }
            .tab-buttons {
                display: flex;
                background: #f8f9fa;
                border-bottom: 1px solid #ddd;
            }
            .tab-button {
                flex: 1;
                padding: 15px 20px;
                border: none;
                background: transparent;
                cursor: pointer;
                font-size: 16px;
                font-weight: 500;
                transition: all 0.3s;
                border-bottom: 3px solid transparent;
            }
            .tab-button.active {
                background: white;
                border-bottom-color: #007bff;
                color: #007bff;
            }
            .tab-button:hover:not(.active) {
                background: #e9ecef;
            }
            .tab-content {
                padding: 20px;
                display: none;
            }
            .tab-content.active {
                display: block;
            }
            .search-input, .ai-search-input {
                width: 100%;
                padding: 15px;
                border: 2px solid #ddd;
                border-radius: 8px;
                font-size: 16px;
                margin-bottom: 15px;
                box-sizing: border-box;
            }
            .search-input:focus, .ai-search-input:focus {
                border-color: #007bff;
                outline: none;
            }
            .example-queries {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 10px;
                margin: 15px 0;
            }
            .example-btn {
                padding: 10px;
                background: #e9ecef;
                border: 1px solid #ddd;
                border-radius: 6px;
                cursor: pointer;
                text-align: center;
                transition: all 0.3s;
                font-size: 14px;
            }
            .example-btn:hover {
                background: #007bff;
                color: white;
            }
            .ai-results {
                margin-top: 20px;
                padding: 15px;
                background: #f8f9fa;
                border-radius: 8px;
                border-left: 4px solid #007bff;
                display: none;
            }
            .disaster-item {
                background: white;
                padding: 15px;
                margin: 10px 0;
                border-radius: 6px;
                border-left: 4px solid #28a745;
            }
            .results-section {
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            table { 
                width: 100%; 
                border-collapse: collapse; 
                margin-top: 15px;
            }
            th, td { 
                border: 1px solid #ddd; 
                padding: 12px 8px; 
                text-align: left; 
                font-size: 14px;
            }
            th { 
                background-color: #f8f9fa; 
                font-weight: 600;
                position: sticky;
                top: 0;
            }
            tr:nth-child(even) { background-color: #f9f9f9; }
            tr:hover { background-color: #f0f8ff; }
            
            .btn {
                padding: 10px 20px;
                margin: 5px;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-size: 14px;
                font-weight: 500;
                transition: all 0.3s;
            }
            .btn-primary { background: #007bff; color: white; }
            .btn-primary:hover { background: #0056b3; }
            .btn-success { background: #28a745; color: white; }
            .btn-success:hover { background: #1e7e34; }
            .btn-small { padding: 6px 12px; font-size: 12px; }
            
            .severity-critical { color: #dc3545; font-weight: bold; }
            .severity-high { color: #fd7e14; font-weight: bold; }
            .severity-medium { color: #ffc107; font-weight: bold; }
            .severity-low { color: #28a745; }
            
            .loading { 
                display: none; 
                color: #666; 
                font-style: italic;
                margin-left: 10px;
            }
            .auto-refresh {
                color: #28a745;
                font-weight: 500;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🌍 WRLD Relief Crisis Monitor</h1>
                <p>Real-time Global Disaster Monitoring Dashboard with AI Agent</p>
            </div>
            
            <div class="status-bar">
                <strong>Status:</strong> <span class="auto-refresh">Monitoring Active</span> | 
                <strong>Last Update:</strong> <span id="lastUpdate">Loading...</span> | 
                <strong>Auto-refresh:</strong> Every 10 minutes |
                <strong>Data Range:</strong> Last 7 days
            </div>
            
            <div class="search-tabs">
                <div class="tab-buttons">
                    <button class="tab-button active" onclick="switchTab('standard')">🔍 Standard Search</button>
                    <button class="tab-button" onclick="switchTab('ai')">🤖 AI Agent Search</button>
                </div>
                
                <div id="standard-tab" class="tab-content active">
                    <h4>Standard Disaster Search</h4>
                    <p>Search disasters using keywords and filters</p>
                    <input type="text" id="searchQuery" class="search-input" 
                           placeholder="Search disasters (e.g., earthquake japan, flood texas)..." 
                           value="global disasters today">
                    <div>
                        <button class="btn btn-primary" onclick="searchDisasters()">🔍 Search Disasters</button>
                        <button class="btn btn-success" onclick="refreshData()">🔄 Refresh Now</button>
                        <span class="loading" id="loading">Loading...</span>
                    </div>
                </div>
                
                <div id="ai-tab" class="tab-content">
                    <h4>AI Agent Natural Language Search</h4>
                    <p>Ask questions in natural language about global disasters</p>
                    <input type="text" id="aiQuery" class="ai-search-input" 
                           placeholder="Ask about disasters (e.g., 'What earthquakes happened in Japan?', 'Show me recent floods')" 
                           value="What earthquakes happened in Japan recently?">
                    
                    <div>
                        <button class="btn btn-primary" onclick="searchWithAI()">🤖 Ask AI Agent</button>
                        <button class="btn btn-success" onclick="getAgentStatus()">📊 Agent Status</button>
                        <span class="loading" id="aiLoading">Processing...</span>
                    </div>
                    
                    <h5>Example Queries:</h5>
                    <div class="example-queries">
                        <div class="example-btn" onclick="setAIQuery('What earthquakes happened in Japan recently?')">🗾 Japan Earthquakes</div>
                        <div class="example-btn" onclick="setAIQuery('Show me recent floods in Texas')">🌊 Texas Floods</div>
                        <div class="example-btn" onclick="setAIQuery('What wildfires are happening globally?')">🔥 Global Wildfires</div>
                        <div class="example-btn" onclick="setAIQuery('Show me conflicts and attacks')">⚔️ Conflicts</div>
                        <div class="example-btn" onclick="setAIQuery('What hurricanes or typhoons occurred?')">🌀 Hurricanes</div>
                        <div class="example-btn" onclick="setAIQuery('Show me magnitude 5+ earthquakes')">📊 Strong Earthquakes</div>
                    </div>
                    
                    <div id="aiResults" class="ai-results">
                        <h4>🤖 AI Agent Response:</h4>
                        <div id="aiResultsContent"></div>
                    </div>
                </div>
            </div>
            
            <div class="results-section">
                <h3>Global Disaster Status</h3>
                <div style="overflow-x: auto;">
                    <table id="disastersTable">
                        <thead>
                            <tr>
                                <th>Title</th>
                                <th>Location</th>
                                <th>Severity</th>
                                <th>Category</th>
                                <th>Time</th>
                                <th>Confidence</th>
                                <th>Affected People</th>
                                <th>Action</th>
                            </tr>
                        </thead>
                        <tbody id="disastersBody">
                            <tr><td colspan="8" style="text-align: center; padding: 20px;">Loading disaster data...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <script>
            let currentDisasters = [];
            let autoRefreshInterval;
            
            // Initialize on page load
            window.onload = async function() {
                await loadInitialData();
                startAutoRefresh();
                updateLastUpdateTime();
            };
            
            // Tab switching
            function switchTab(tabName) {
                // Update tab buttons
                document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
                document.querySelector(`[onclick="switchTab('${tabName}')"]`).classList.add('active');
                
                // Update tab content
                document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
                document.getElementById(`${tabName}-tab`).classList.add('active');
            }
            
            // AI Agent functions
            function setAIQuery(query) {
                document.getElementById('aiQuery').value = query;
            }
            
            async function searchWithAI() {
                const query = document.getElementById('aiQuery').value;
                const loading = document.getElementById('aiLoading');
                const results = document.getElementById('aiResults');
                const resultsContent = document.getElementById('aiResultsContent');
                
                if (!query.trim()) {
                    alert('Please enter a question.');
                    return;
                }
                
                loading.style.display = 'inline';
                results.style.display = 'none';
                
                try {
                    const response = await fetch('/api/uagent/query', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ 
                            query: query, 
                            max_results: 5,
                            requester: "web_user"
                        })
                    });
                    
                    const data = await response.json();
                    
                    if (data.disasters && data.disasters.length > 0) {
                        resultsContent.innerHTML = `
                            <p><strong>Query:</strong> "${data.query}"</p>
                            <p><strong>Results:</strong> ${data.total_count} disasters found</p>
                            <p><strong>Agent:</strong> ${data.agent_name}</p>
                            <hr>
                            ${data.disasters.map((disaster, i) => `
                                <div class="disaster-item">
                                    <h5>🚨 Disaster ${i + 1}: ${disaster.title}</h5>
                                    <p><strong>📍 Location:</strong> ${disaster.location}</p>
                                    <p><strong>⚠️ Severity:</strong> ${disaster.severity}</p>
                                    <p><strong>📂 Category:</strong> ${disaster.category}</p>
                                    <p><strong>📰 Source:</strong> ${disaster.source}</p>
                                    <p><strong>🎯 Confidence:</strong> ${(disaster.confidence * 100).toFixed(1)}%</p>
                                    ${disaster.affected_people > 0 ? `<p><strong>👥 Affected:</strong> ${disaster.affected_people} people</p>` : ''}
                                    <p><strong>📝 Description:</strong> ${disaster.description}</p>
                                </div>
                            `).join('')}
                        `;
                        results.style.display = 'block';
                    } else {
                        resultsContent.innerHTML = `
                            <p><strong>Query:</strong> "${data.query}"</p>
                            <p>❌ No disasters found matching your criteria.</p>
                            <p>Try a different search term.</p>
                        `;
                        results.style.display = 'block';
                    }
                    
                } catch (error) {
                    resultsContent.innerHTML = `
                        <p>❌ Search error: ${error.message}</p>
                        <p>Please try again.</p>
                    `;
                    results.style.display = 'block';
                    console.error('AI search error:', error);
                } finally {
                    loading.style.display = 'none';
                }
            }
            
            async function getAgentStatus() {
                const loading = document.getElementById('aiLoading');
                const results = document.getElementById('aiResults');
                const resultsContent = document.getElementById('aiResultsContent');
                
                loading.style.display = 'inline';
                
                try {
                    const response = await fetch('/api/uagent/status');
                    const data = await response.json();
                    
                    resultsContent.innerHTML = `
                        <h4>📊 WRLD Relief Agent Status</h4>
                        <p><strong>🟢 Status:</strong> ${data.status}</p>
                        <p><strong>🤖 Agent Name:</strong> ${data.agent_name}</p>
                        <p><strong>📊 Total Disasters:</strong> ${data.total_disasters}</p>
                        <p><strong>⏰ Last Update:</strong> ${data.last_update || 'N/A'}</p>
                        <p><strong>💾 Cache Status:</strong> ${data.cache_healthy ? 'Healthy' : 'Error'}</p>
                        <p><strong>🔗 Protocols:</strong> ${data.protocols.join(', ')}</p>
                        <p><strong>🚀 Version:</strong> ${data.version}</p>
                    `;
                    results.style.display = 'block';
                    
                } catch (error) {
                    resultsContent.innerHTML = `
                        <p>❌ Status check error: ${error.message}</p>
                    `;
                    results.style.display = 'block';
                    console.error('Status error:', error);
                } finally {
                    loading.style.display = 'none';
                }
            }
            
            // Standard search functions
            async function loadInitialData() {
                const loading = document.getElementById('loading');
                const tbody = document.getElementById('disastersBody');
                
                loading.style.display = 'inline';
                tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; padding: 20px;">Loading disaster data...</td></tr>';
                
                try {
                    const response = await fetch('/api/initial-load');
                    const data = await response.json();
                    
                    if (data.success) {
                        currentDisasters = data.disasters || [];
                        displayResults(currentDisasters);
                        console.log(`✅ Loaded ${currentDisasters.length} disasters`);
                    } else {
                        throw new Error(data.message || 'Failed to load data');
                    }
                } catch (error) {
                    tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; padding: 20px; color: #dc3545;">Error loading data. Please refresh.</td></tr>';
                    console.error('Load error:', error);
                } finally {
                    loading.style.display = 'none';
                }
            }
            
            async function searchDisasters() {
                const query = document.getElementById('searchQuery').value;
                const loading = document.getElementById('loading');
                const tbody = document.getElementById('disastersBody');
                
                loading.style.display = 'inline';
                tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; padding: 20px;">Searching disasters...</td></tr>';
                
                try {
                    const response = await fetch('/api/search', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ query: query, max_results: 20 })
                    });
                    
                    const data = await response.json();
                    if (data.success) {
                        currentDisasters = data.disasters || [];
                        displayResults(currentDisasters);
                        updateLastUpdateTime();
                    } else {
                        throw new Error(data.message || 'Search failed');
                    }
                } catch (error) {
                    tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; padding: 20px; color: #dc3545;">Search failed. Please try again.</td></tr>';
                    console.error('Search error:', error);
                } finally {
                    loading.style.display = 'none';
                }
            }
            
            async function refreshData() {
                console.log('🔄 Refreshing data...');
                await searchDisasters();
            }
            
            function startAutoRefresh() {
                autoRefreshInterval = setInterval(async () => {
                    await refreshData();
                }, 600000); // 10 minutes
                console.log('✅ Auto-refresh started');
            }
            
            function displayResults(disasters) {
                const tbody = document.getElementById('disastersBody');
                
                if (disasters.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; padding: 20px;">No disasters found.</td></tr>';
                    return;
                }
                
                tbody.innerHTML = disasters.map(disaster => `
                    <tr>
                        <td style="max-width: 300px;">${disaster.title}</td>
                        <td>${disaster.location}</td>
                        <td><span class="severity-${disaster.severity.toLowerCase()}">${disaster.severity}</span></td>
                        <td>${disaster.category}</td>
                        <td>${formatTime(disaster.timestamp)}</td>
                        <td>${(disaster.confidence * 100).toFixed(1)}%</td>
                        <td>${formatNumber(disaster.affected_people)}</td>
                        <td>
                            <button class="btn btn-success btn-small" onclick="downloadSingle('${disaster.id}')">
                                📥 Download
                            </button>
                            <button class="btn btn-primary btn-small" onclick="uploadToChain('${disaster.id}')">
                                🔗 Upload
                            </button>
                        </td>
                    </tr>
                `).join('');
            }
            
            async function downloadSingle(disasterId) {
                try {
                    const response = await fetch(`/api/disaster/${disasterId}/blockchain`);
                    const data = await response.json();
                    
                    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `disaster_${disasterId}_blockchain.json`;
                    a.click();
                    URL.revokeObjectURL(url);
                    
                    console.log(`✅ Downloaded: ${disasterId}`);
                } catch (error) {
                    alert('Download failed.');
                    console.error('Download error:', error);
                }
            }
            
            async function uploadToChain(disasterId) {
                const loading = document.getElementById('loading');
                
                try {
                    loading.style.display = 'inline';
                    
                    const response = await fetch(`/api/disaster/${disasterId}/upload-chain`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' }
                    });
                    
                    const data = await response.json();
                    
                    if (data.success) {
                        alert(`✅ Successfully uploaded to blockchain!\\n\\nTransaction: ${data.transaction_hash}`);
                        if (confirm('View on Etherscan?')) {
                            window.open(data.etherscan_url, '_blank');
                        }
                    } else {
                        alert(`❌ Upload failed: ${data.error}`);
                    }
                    
                } catch (error) {
                    alert(`❌ Upload failed: ${error.message}`);
                } finally {
                    loading.style.display = 'none';
                }
            }
            
            function formatTime(timestamp) {
                const date = new Date(timestamp * 1000);
                const now = new Date();
                const diffHours = Math.floor((now - date) / (1000 * 60 * 60));
                
                if (diffHours < 1) return 'Just now';
                if (diffHours < 24) return `${diffHours}h ago`;
                
                const diffDays = Math.floor(diffHours / 24);
                if (diffDays < 7) return `${diffDays}d ago`;
                
                return date.toLocaleDateString();
            }
            
            function formatNumber(num) {
                if (!num || num === 0) return 'TBD';
                if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
                if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
                return num.toString();
            }
            
            function updateLastUpdateTime() {
                document.getElementById('lastUpdate').textContent = new Date().toLocaleTimeString();
            }
            
            // Enter key support
            document.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    if (document.getElementById('ai-tab').classList.contains('active')) {
                        searchWithAI();
                    } else {
                        searchDisasters();
                    }
                }
            });
            
            // Cleanup
            window.onbeforeunload = function() {
                if (autoRefreshInterval) {
                    clearInterval(autoRefreshInterval);
                }
            };
        </script>
    </body>
    </html>
    """)

# API endpoints (same as before)
@app.get("/api/initial-load")
async def load_initial_disasters():
    try:
        disasters = await disaster_cache.get_disasters(days=7)
        global current_disasters
        current_disasters = disasters
        
        disasters_dict = []
        for disaster in disasters:
            disasters_dict.append({
                "id": disaster.id,
                "title": disaster.title,
                "description": disaster.description,
                "location": disaster.location,
                "severity": disaster.severity,
                "category": disaster.category,
                "timestamp": disaster.timestamp,
                "source": disaster.source,
                "confidence": disaster.confidence,
                "affected_people": disaster.affected_people,
                "damage_estimate": disaster.damage_estimate,
                "coordinates": disaster.coordinates
            })
        
        return JSONResponse({
            "success": True,
            "disasters": disasters_dict,
            "total": len(disasters_dict),
            "loaded_at": int(datetime.now().timestamp())
        })
        
    except Exception as e:
        logger.error(f"❌ Initial load error: {e}")
        return JSONResponse({
            "success": False,
            "message": str(e),
            "disasters": []
        })

@app.post("/api/search")
async def search_disasters(request: SearchRequest):
    try:
        disasters = await search_engine.search_disasters(
            query=request.query,
            max_results=request.max_results
        )
        
        disasters_dict = []
        for disaster in disasters:
            disasters_dict.append({
                "id": disaster.id,
                "title": disaster.title,
                "description": disaster.description,
                "location": disaster.location,
                "severity": disaster.severity,
                "category": disaster.category,
                "timestamp": disaster.timestamp,
                "source": disaster.source,
                "confidence": disaster.confidence,
                "affected_people": disaster.affected_people,
                "damage_estimate": disaster.damage_estimate,
                "coordinates": disaster.coordinates
            })
        
        return JSONResponse({
            "success": True,
            "disasters": disasters_dict,
            "total": len(disasters_dict),
            "query": request.query,
            "searched_at": int(datetime.now().timestamp())
        })
        
    except Exception as e:
        logger.error(f"❌ Search error: {e}")
        return JSONResponse({
            "success": False,
            "message": str(e),
            "disasters": []
        })

@app.post("/api/uagent/query")
async def uagent_disaster_query(request: DisasterQueryRequest):
    try:
        logger.info(f"🤖 uAgent query: {request.query}")
        
        # current_disasters를 딕셔너리 형태로 변환
        disasters_dict = []
        for disaster in current_disasters:
            disasters_dict.append({
                "id": disaster.id,
                "title": disaster.title,
                "description": disaster.description,
                "location": disaster.location,
                "severity": disaster.severity,
                "category": disaster.category,
                "timestamp": disaster.timestamp,
                "source": disaster.source,
                "confidence": disaster.confidence,
                "affected_people": disaster.affected_people,
                "coordinates": disaster.coordinates
            })
        
        # 딕셔너리 데이터로 검색
        matched_disasters = search_disasters_by_query(
            disasters_dict, 
            request.query, 
            request.max_results
        )
        
        disaster_results = []
        for disaster in matched_disasters:
            disaster_result = DisasterResult(
                id=disaster.get('id', ''),
                title=disaster.get('title', ''),
                description=disaster.get('description', ''),
                location=disaster.get('location', ''),
                severity=disaster.get('severity', 'LOW'),
                category=disaster.get('category', 'OTHER'),
                timestamp=disaster.get('timestamp', 0),
                source=disaster.get('source', ''),
                confidence=disaster.get('confidence', 0.0),
                affected_people=disaster.get('affected_people', 0) or 0,
                coordinates=disaster.get('coordinates', {"lat": 0.0, "lng": 0.0}) or {"lat": 0.0, "lng": 0.0}
            )
            disaster_results.append(disaster_result)
        
        results = DisasterResults(
            disasters=disaster_results,
            total_count=len(disaster_results),
            query=request.query,
            searched_at=int(datetime.now().timestamp()),
            agent_name="WRLD Relief Disaster Agent"
        )
        
        logger.info(f"✅ uAgent found {len(disaster_results)} disasters for: '{request.query}'")
        
        return JSONResponse(results.dict())
        
    except Exception as e:
        logger.error(f"❌ uAgent query error: {e}")
        return JSONResponse({
            "disasters": [],
            "total_count": 0,
            "query": request.query,
            "searched_at": int(datetime.now().timestamp()),
            "agent_name": "WRLD Relief Disaster Agent (Error)",
            "error": str(e)
        })

def search_disasters_by_query(disasters_data: List[Any], query: str, max_results: int = 10) -> List[Any]:
    """Search disasters by query for uAgent - 딕셔너리 데이터 처리"""
    query_lower = query.lower()
    matched_disasters = []
    
    for disaster in disasters_data:
        # 딕셔너리 형태로 접근 (disaster.title이 아니라 disaster['title'])
        title = disaster.get('title', '').lower() if disaster.get('title') else ''
        description = disaster.get('description', '').lower() if disaster.get('description') else ''
        location = disaster.get('location', '').lower() if disaster.get('location') else ''
        category = disaster.get('category', '').lower() if disaster.get('category') else ''
        
        score = 0
        query_words = query_lower.split()
        
        # 기본 키워드 매칭
        for word in query_words:
            if word in title:
                score += 3
            if word in description:
                score += 2
            if word in location:
                score += 2
            if word in category:
                score += 1
        
        # 한국어 키워드 매핑
        korean_mappings = {
            '지진': ['earthquake', 'seismic'],
            '홍수': ['flood', 'flooding'],
            '산불': ['fire', 'wildfire'],
            '태풍': ['hurricane', 'typhoon', 'cyclone'],
            '화산': ['volcano', 'volcanic'],
            '분쟁': ['war', 'conflict', 'attack'],
            '일본': ['japan', 'japanese'],
            '중국': ['china', 'chinese'],
            '미국': ['usa', 'america', 'united states'],
            '최근': ['recent', 'latest'],
            '현재': ['current', 'now'],
            '일어나는': ['happening', 'occurring']
        }
        
        # 한국어 → 영어 매핑 처리
        for korean, english_words in korean_mappings.items():
            if korean in query_lower:
                for eng_word in english_words:
                    if eng_word in title or eng_word in description or eng_word in location or eng_word in category:
                        score += 5
        
        # 특별 키워드 처리 (영어)
        if any(word in ['earthquake', 'seismic'] for word in query_words):
            if disaster.get('category') == 'EARTHQUAKE':
                score += 5
        
        if any(word in ['flood', 'flooding'] for word in query_words):
            if disaster.get('category') == 'FLOOD':
                score += 5
                
        if any(word in ['fire', 'wildfire'] for word in query_words):
            if disaster.get('category') == 'WILDFIRE':
                score += 5
                
        if any(word in ['hurricane', 'typhoon', 'cyclone'] for word in query_words):
            if disaster.get('category') == 'HURRICANE':
                score += 5
                
        if any(word in ['volcano', 'volcanic'] for word in query_words):
            if disaster.get('category') == 'VOLCANO':
                score += 5
                
        if any(word in ['war', 'conflict', 'attack'] for word in query_words):
            if disaster.get('category') == 'OTHER' and any(word in description for word in ['attack', 'killed', 'war', 'conflict']):
                score += 5
        
        # 지역별 검색 (영어)
        if any(word in ['japan', 'japanese'] for word in query_words):
            if 'japan' in location:
                score += 4
                
        if any(word in ['china', 'chinese'] for word in query_words):
            if 'china' in location:
                score += 4
                
        if any(word in ['usa', 'america', 'united states'] for word in query_words):
            if any(word in location for word in ['united states', 'usa', 'america']):
                score += 4
        
        # 최근/현재 키워드 처리
        if any(word in ['recent', 'latest', 'current', 'now', 'today'] for word in query_words):
            score += 2  # 모든 데이터가 최근 7일이므로 보너스 점수
        
        if score > 0:
            # 딕셔너리에 점수 추가
            disaster_copy = disaster.copy()
            disaster_copy['search_score'] = score
            matched_disasters.append(disaster_copy)
    
    # 점수순으로 정렬
    matched_disasters.sort(key=lambda x: x.get('search_score', 0), reverse=True)
    return matched_disasters[:max_results]

@app.get("/api/uagent/status")
async def uagent_status():
    """uAgent status check"""
    try:
        return JSONResponse({
            "status": "online",
            "agent_name": "WRLD Relief Disaster Agent",
            "total_disasters": len(current_disasters),
            "uptime": "Running via FastAPI",
            "version": "2.0.0",
            "protocols": ["DisasterQuery", "DisasterResults", "AgentStatus"],
            "endpoints": ["/api/uagent/query", "/api/uagent/status"],
            "checked_at": int(datetime.now().timestamp())
        })
        
    except Exception as e:
        logger.error(f"❌ uAgent status error: {e}")
        return JSONResponse({
            "status": "error",
            "error": str(e),
            "checked_at": int(datetime.now().timestamp())
        })

@app.get("/api/disaster/{disaster_id}/blockchain")
async def get_disaster_blockchain(disaster_id: str = Path(..., description="Disaster ID")):
    """Get blockchain data for a specific disaster"""
    try:
        disaster = None
        for d in current_disasters:
            if d.id == disaster_id:
                disaster = d
                break
        
        if not disaster:
            raise HTTPException(status_code=404, detail="Disaster not found")
        
        blockchain_data = search_engine.generate_blockchain_data(disaster)
        return JSONResponse(blockchain_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Blockchain export error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/disaster/{disaster_id}/upload-chain")
async def upload_disaster_to_chain(disaster_id: str = Path(..., description="Disaster ID")):
    """Upload disaster to blockchain"""
    if not BLOCKCHAIN_AVAILABLE:
        return JSONResponse({
            "success": False,
            "error": "Blockchain functionality not available",
            "error_type": "MODULE_NOT_AVAILABLE"
        })
    
    try:
        disaster = None
        for d in current_disasters:
            if d.id == disaster_id:
                disaster = d
                break
        
        if not disaster:
            raise HTTPException(status_code=404, detail="Disaster not found")
        
        uploader = DisasterUploader()
        result = await uploader.upload_disaster(disaster)
        
        if result["success"]:
            return JSONResponse(result)
        else:
            return JSONResponse(result, status_code=400)
        
    except Exception as e:
        logger.error(f"❌ Blockchain upload error: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e),
            "error_type": "UNKNOWN_ERROR"
        }, status_code=500)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "wrld-relief-crisis-monitor",
        "version": "2.0.0",
        "monitoring": "active",
        "disasters_loaded": len(current_disasters),
        "uagent_integrated": True,
        "timestamp": int(datetime.now().timestamp())
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
