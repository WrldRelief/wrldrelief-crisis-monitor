"""
🌍 WRLD Relief Crisis Monitor - Real-time Global Disaster Monitoring Dashboard
AI-powered disaster monitoring with automatic updates and blockchain data export
"""

from fastapi import FastAPI, HTTPException, Path
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import asyncio
import logging
from datetime import datetime
import json

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai_search import DisasterSearchEngine, DisasterInfo

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app creation
app = FastAPI(
    title="🌍 WRLD Relief Crisis Monitor",
    description="Real-time Global Disaster Monitoring Dashboard",
    version="2.0.0"
)

class SearchRequest(BaseModel):
    query: Optional[str] = "global disasters today"
    max_results: Optional[int] = 20

# Global AI search engine
search_engine = DisasterSearchEngine()

# Global disaster cache for auto-refresh
current_disasters = []

@app.on_event("startup")
async def startup_event():
    """Application startup initialization"""
    logger.info("🚀 Starting WRLD Relief Crisis Monitor...")
    
    # Load initial disaster data from last 30 days
    global current_disasters
    current_disasters = await search_engine.get_initial_disasters(days=30)
    
    logger.info(f"✅ Dashboard ready! Loaded {len(current_disasters)} disasters from last 30 days")

@app.get("/")
async def dashboard():
    """Main dashboard page with auto-monitoring"""
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
            .controls {
                background: white;
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 20px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
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
            .search-input {
                width: 300px;
                padding: 10px;
                border: 2px solid #ddd;
                border-radius: 5px;
                font-size: 14px;
            }
            .search-input:focus {
                border-color: #007bff;
                outline: none;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🌍 WRLD Relief Crisis Monitor</h1>
                <p>Real-time Global Disaster Monitoring Dashboard</p>
            </div>
            
            <div class="status-bar">
                <strong>Status:</strong> <span class="auto-refresh">Monitoring Active</span> | 
                <strong>Last Update:</strong> <span id="lastUpdate">Loading...</span> | 
                <strong>Auto-refresh:</strong> Every 10 minutes |
                <strong>Data Range:</strong> Last 30 days
            </div>
            
            <div class="controls">
                <input type="text" id="searchQuery" class="search-input" placeholder="Search disasters (e.g., earthquake japan, flood texas)..." value="global disasters today">
                <button class="btn btn-primary" onclick="searchDisasters()">🔍 Search Disasters</button>
                <button class="btn btn-success" onclick="refreshData()">🔄 Refresh Now</button>
                <span class="loading" id="loading">Loading...</span>
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
                            <tr><td colspan="8" style="text-align: center; padding: 20px;">Loading initial disaster data from last 7 days...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <script>
            let currentDisasters = [];
            let autoRefreshInterval;
            
            // Load initial data on page load
            window.onload = async function() {
                await loadInitialData();
                startAutoRefresh();
                updateLastUpdateTime();
            };
            
            async function loadInitialData() {
                const loading = document.getElementById('loading');
                const tbody = document.getElementById('disastersBody');
                
                loading.style.display = 'inline';
                tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; padding: 20px;">Loading disaster data from last 7 days...</td></tr>';
                
                try {
                    const response = await fetch('/api/initial-load');
                    const data = await response.json();
                    
                    if (data.success) {
                        currentDisasters = data.disasters || [];
                        displayResults(currentDisasters);
                        console.log(`✅ Loaded ${currentDisasters.length} disasters from last 7 days`);
                    } else {
                        throw new Error(data.message || 'Failed to load initial data');
                    }
                } catch (error) {
                    tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; padding: 20px; color: #dc3545;">Error loading initial data. Please refresh the page.</td></tr>';
                    console.error('Initial load error:', error);
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
                console.log('🔄 Auto-refreshing disaster data...');
                await searchDisasters();
            }
            
            function startAutoRefresh() {
                // Auto-refresh every 10 minutes (600,000 ms)
                autoRefreshInterval = setInterval(async () => {
                    await refreshData();
                }, 600000);
                console.log('✅ Auto-refresh started (every 10 minutes)');
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
                    
                    console.log(`✅ Downloaded blockchain data for disaster: ${disasterId}`);
                } catch (error) {
                    alert('Download failed. Please try again.');
                    console.error('Download error:', error);
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
            
            // Cleanup on page unload
            window.onbeforeunload = function() {
                if (autoRefreshInterval) {
                    clearInterval(autoRefreshInterval);
                }
            };
        </script>
    </body>
    </html>
    """)

@app.get("/api/initial-load")
async def load_initial_disasters():
    """Load initial disaster data from last 30 days"""
    try:
        logger.info("🔍 Loading initial disasters from last 30 days...")
        
        global current_disasters
        current_disasters = await search_engine.get_initial_disasters(days=30)
        
        # Convert DisasterInfo objects to dictionaries
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
                "damage_estimate": disaster.damage_estimate,
                "coordinates": disaster.coordinates
            })
        
        return JSONResponse({
            "success": True,
            "disasters": disasters_dict,
            "total": len(disasters_dict),
            "days": 7,
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
    """AI-powered disaster search"""
    try:
        logger.info(f"🔍 Searching disasters: {request.query}")
        
        # Use AI search engine
        disasters = await search_engine.search_disasters(
            query=request.query,
            max_results=request.max_results
        )
        
        # Update global cache
        global current_disasters
        current_disasters = disasters
        
        # Convert DisasterInfo objects to dictionaries
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

@app.get("/api/disaster/{disaster_id}/blockchain")
async def get_disaster_blockchain(disaster_id: str = Path(..., description="Disaster ID")):
    """Get blockchain data for a specific disaster"""
    try:
        # Find disaster in current cache
        disaster = None
        for d in current_disasters:
            if d.id == disaster_id:
                disaster = d
                break
        
        if not disaster:
            raise HTTPException(status_code=404, detail="Disaster not found")
        
        # Generate blockchain data
        blockchain_data = search_engine.generate_blockchain_data(disaster)
        
        logger.info(f"📤 Generated blockchain data for disaster: {disaster_id}")
        return JSONResponse(blockchain_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Blockchain export error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/export-all")
async def export_all_blockchain_data():
    """Export blockchain data for all current disasters"""
    try:
        blockchain_data = {
            "version": "2.0",
            "timestamp": int(datetime.now().timestamp()),
            "total_disasters": len(current_disasters),
            "disasters": []
        }
        
        for disaster in current_disasters:
            disaster_blockchain = search_engine.generate_blockchain_data(disaster)
            blockchain_data["disasters"].append(disaster_blockchain)
        
        logger.info(f"📤 Exported blockchain data for {len(current_disasters)} disasters")
        return JSONResponse(blockchain_data)
        
    except Exception as e:
        logger.error(f"❌ Bulk export error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
async def get_disaster_stats():
    """Get disaster statistics"""
    try:
        if not current_disasters:
            return JSONResponse({
                "total": 0,
                "by_severity": {},
                "by_category": {},
                "last_updated": None
            })
        
        # Calculate statistics
        severity_counts = {}
        category_counts = {}
        
        for disaster in current_disasters:
            # Count by severity
            severity = disaster.severity
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            # Count by category
            category = disaster.category
            category_counts[category] = category_counts.get(category, 0) + 1
        
        return JSONResponse({
            "total": len(current_disasters),
            "by_severity": severity_counts,
            "by_category": category_counts,
            "last_updated": int(datetime.now().timestamp())
        })
        
    except Exception as e:
        logger.error(f"❌ Stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "wrld-relief-crisis-monitor",
        "version": "2.0.0",
        "monitoring": "active",
        "disasters_loaded": len(current_disasters),
        "timestamp": int(datetime.now().timestamp())
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
