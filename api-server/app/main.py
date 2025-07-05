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

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from hybrid_search import HybridDisasterEngine
from ai_search import DisasterInfo
from cache_manager import SimpleDisasterCache
from blockchain import DisasterUploader

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

# Global Hybrid search engine (API + AI)
search_engine = HybridDisasterEngine()

# Global disaster cache (file-based)
disaster_cache = SimpleDisasterCache()

# Global disaster cache for auto-refresh
current_disasters = []

@app.on_event("startup")
async def startup_event():
    """Application startup initialization"""
    logger.info("🚀 Starting WRLD Relief Crisis Monitor...")
    
    # Initialize cache (load from file)
    await disaster_cache.initialize()
    
    # Get cached disasters
    cached_disasters = await disaster_cache.get_disasters(days=7)
    
    if len(cached_disasters) < 50 or disaster_cache.should_update():
        # Cache is empty or outdated, fetch fresh data
        logger.info("🔄 Cache is empty or outdated, fetching fresh data...")
        fresh_disasters = await search_engine.get_initial_disasters(days=7)
        await disaster_cache.update_cache(fresh_disasters)
        
    # Load current disasters from cache
    global current_disasters
    current_disasters = await disaster_cache.get_disasters(days=7)
    
    logger.info(f"✅ Dashboard ready! Loaded {len(current_disasters)} disasters from cache")

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
                    
                    console.log(`✅ Downloaded blockchain data for disaster: ${disasterId}`);
                } catch (error) {
                    alert('Download failed. Please try again.');
                    console.error('Download error:', error);
                }
            }
            
            async function uploadToChain(disasterId) {
                const loading = document.getElementById('loading');
                
                try {
                    loading.style.display = 'inline';
                    console.log(`🔗 Uploading disaster ${disasterId} to blockchain...`);
                    
                    const response = await fetch(`/api/disaster/${disasterId}/upload-chain`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' }
                    });
                    
                    const data = await response.json();
                    
                    if (data.success) {
                        // Success notification
                        const etherscanUrl = data.etherscan_url;
                        const txHash = data.transaction_hash;
                        
                        alert(`✅ Successfully uploaded to blockchain!
                        
Transaction Hash: ${txHash}
Block Number: ${data.block_number}
Gas Used: ${data.gas_used}

View on Etherscan: ${etherscanUrl}`);
                        
                        console.log(`✅ Uploaded disaster ${disasterId} to blockchain:`, data);
                        
                        // Open Etherscan in new tab
                        if (confirm('Would you like to view the transaction on Etherscan?')) {
                            window.open(etherscanUrl, '_blank');
                        }
                        
                    } else {
                        // Error handling
                        let errorMessage = `❌ Upload failed: ${data.error}`;
                        
                        if (data.error_type === 'DUPLICATE') {
                            errorMessage = `⚠️ This disaster already exists on the blockchain.`;
                        } else if (data.error_type === 'CONNECTION_ERROR') {
                            errorMessage = `❌ Blockchain connection failed. Please check your configuration.`;
                        } else if (data.error_type === 'CONTRACT_ERROR') {
                            errorMessage = `❌ Smart contract error. You may not have permission to upload.`;
                        }
                        
                        alert(errorMessage);
                        console.error('Upload failed:', data);
                    }
                    
                } catch (error) {
                    alert(`❌ Upload failed: ${error.message}`);
                    console.error('Upload error:', error);
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
    """Load initial disaster data from cache (instant response)"""
    try:
        logger.info("📂 Loading disasters from cache...")
        
        # Get disasters from cache (instant)
        disasters = await disaster_cache.get_disasters(days=7)
        
        # Background update if needed
        if disaster_cache.should_update():
            asyncio.create_task(background_update())
        
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
            "days": 7,
            "cached": True,
            "last_update": disaster_cache.last_update.isoformat() if disaster_cache.last_update else None,
            "loaded_at": int(datetime.now().timestamp())
        })
        
    except Exception as e:
        logger.error(f"❌ Initial load error: {e}")
        return JSONResponse({
            "success": False,
            "message": str(e),
            "disasters": []
        })

async def background_update():
    """백그라운드에서 캐시 업데이트"""
    try:
        logger.info("🔄 Background update started...")
        
        # 새로운 데이터 수집
        fresh_disasters = await search_engine.get_initial_disasters(days=7)
        
        # 캐시 업데이트
        added_count = await disaster_cache.update_cache(fresh_disasters)
        
        # 글로벌 캐시 업데이트
        global current_disasters
        current_disasters = await disaster_cache.get_disasters(days=7)
        
        logger.info(f"✅ Background update complete: {added_count} new disasters, total: {len(current_disasters)}")
        
    except Exception as e:
        logger.error(f"❌ Background update failed: {e}")

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
        
        # 기존 재해 데이터와 새 검색 결과를 통합
        global current_disasters
        
        # 기존 재해 ID 목록
        existing_ids = {d.id for d in current_disasters}
        
        # 새로운 재해만 추가
        new_disasters = []
        for disaster in disasters:
            if disaster.id not in existing_ids:
                new_disasters.append(disaster)
        
        # 기존 데이터에 새 데이터 추가 (교체하지 않음)
        current_disasters.extend(new_disasters)
        
        logger.info(f"📊 Search results: {len(disasters)} found, {len(new_disasters)} new, total: {len(current_disasters)}")
        
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

@app.get("/api/cache/stats")
async def get_cache_stats():
    """Get cache statistics and status"""
    try:
        cache_stats = disaster_cache.get_cache_stats()
        
        return JSONResponse({
            "success": True,
            "cache_stats": cache_stats,
            "current_disasters": len(current_disasters),
            "should_update": disaster_cache.should_update(),
            "timestamp": int(datetime.now().timestamp())
        })
        
    except Exception as e:
        logger.error(f"❌ Cache stats error: {e}")
        return JSONResponse({
            "success": False,
            "message": str(e)
        })

@app.post("/api/cache/refresh")
async def force_cache_refresh():
    """Force cache refresh (manual trigger)"""
    try:
        logger.info("🔄 Manual cache refresh triggered...")
        
        # Force refresh cache
        added_count = await disaster_cache.force_refresh()
        
        # Update global cache
        global current_disasters
        current_disasters = await disaster_cache.get_disasters(days=7)
        
        return JSONResponse({
            "success": True,
            "message": f"Cache refreshed successfully",
            "added_disasters": added_count,
            "total_disasters": len(current_disasters),
            "refreshed_at": int(datetime.now().timestamp())
        })
        
    except Exception as e:
        logger.error(f"❌ Manual refresh error: {e}")
        return JSONResponse({
            "success": False,
            "message": str(e)
        })

@app.post("/api/disaster/{disaster_id}/upload-chain")
async def upload_disaster_to_chain(disaster_id: str = Path(..., description="Disaster ID")):
    """Upload disaster to blockchain"""
    try:
        logger.info(f"🔗 Blockchain upload request for disaster: {disaster_id}")
        
        # Find disaster in current cache
        disaster = None
        for d in current_disasters:
            if d.id == disaster_id:
                disaster = d
                break
        
        if not disaster:
            raise HTTPException(status_code=404, detail="Disaster not found")
        
        # Initialize blockchain uploader
        try:
            uploader = DisasterUploader()
        except Exception as e:
            logger.error(f"❌ Failed to initialize blockchain uploader: {e}")
            return JSONResponse({
                "success": False,
                "error": f"Blockchain connection failed: {str(e)}",
                "error_type": "CONNECTION_ERROR"
            })
        
        # Upload to blockchain
        result = await uploader.upload_disaster(disaster)
        
        if result["success"]:
            logger.info(f"✅ Successfully uploaded disaster {disaster_id} to blockchain")
            return JSONResponse(result)
        else:
            logger.error(f"❌ Failed to upload disaster {disaster_id}: {result.get('error')}")
            return JSONResponse(result, status_code=400)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Blockchain upload error: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e),
            "error_type": "UNKNOWN_ERROR"
        }, status_code=500)

@app.get("/api/blockchain/status")
async def get_blockchain_status():
    """Get blockchain connection status and permissions"""
    try:
        uploader = DisasterUploader()
        
        # Check permissions
        permissions = await uploader.check_permissions()
        
        # Get total disasters count from blockchain
        total_count = await uploader.get_total_disasters_count()
        
        return JSONResponse({
            "success": True,
            "blockchain_connected": True,
            "permissions": permissions,
            "total_disasters_on_chain": total_count,
            "contract_address": uploader.config.contract_address,
            "network": uploader.config.network_name,
            "account_address": uploader.account.address,
            "etherscan_url": uploader.config.etherscan_url,
            "checked_at": int(datetime.now().timestamp())
        })
        
    except Exception as e:
        logger.error(f"❌ Blockchain status check failed: {e}")
        return JSONResponse({
            "success": False,
            "blockchain_connected": False,
            "error": str(e),
            "checked_at": int(datetime.now().timestamp())
        })

@app.get("/api/disaster/{disaster_id}/blockchain-status")
async def get_disaster_blockchain_status(disaster_id: str = Path(..., description="Disaster ID")):
    """Check if disaster exists on blockchain"""
    try:
        uploader = DisasterUploader()
        
        # Check if disaster exists on blockchain
        blockchain_data = await uploader.get_disaster_from_blockchain(disaster_id)
        
        if blockchain_data:
            return JSONResponse({
                "success": True,
                "exists_on_blockchain": True,
                "blockchain_data": blockchain_data,
                "disaster_id": disaster_id
            })
        else:
            return JSONResponse({
                "success": True,
                "exists_on_blockchain": False,
                "disaster_id": disaster_id
            })
            
    except Exception as e:
        logger.error(f"❌ Failed to check blockchain status for disaster {disaster_id}: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e),
            "disaster_id": disaster_id
        })

@app.post("/api/disasters/batch-upload-chain")
async def batch_upload_disasters_to_chain():
    """Upload multiple disasters to blockchain"""
    try:
        logger.info(f"🔗 Batch blockchain upload request for {len(current_disasters)} disasters")
        
        if not current_disasters:
            return JSONResponse({
                "success": False,
                "error": "No disasters available for upload"
            })
        
        uploader = DisasterUploader()
        
        results = []
        success_count = 0
        error_count = 0
        
        # Upload disasters one by one (to avoid nonce conflicts)
        for disaster in current_disasters[:10]:  # Limit to 10 for demo
            try:
                result = await uploader.upload_disaster(disaster)
                results.append({
                    "disaster_id": disaster.id,
                    "disaster_title": disaster.title,
                    "result": result
                })
                
                if result["success"]:
                    success_count += 1
                    logger.info(f"✅ Uploaded {disaster.id}")
                else:
                    error_count += 1
                    logger.warning(f"❌ Failed to upload {disaster.id}: {result.get('error')}")
                
                # Small delay to avoid rate limiting
                await asyncio.sleep(2)
                
            except Exception as e:
                error_count += 1
                results.append({
                    "disaster_id": disaster.id,
                    "disaster_title": disaster.title,
                    "result": {
                        "success": False,
                        "error": str(e),
                        "error_type": "UPLOAD_ERROR"
                    }
                })
                logger.error(f"❌ Exception uploading {disaster.id}: {e}")
        
        return JSONResponse({
            "success": True,
            "total_processed": len(results),
            "success_count": success_count,
            "error_count": error_count,
            "results": results,
            "uploaded_at": int(datetime.now().timestamp())
        })
        
    except Exception as e:
        logger.error(f"❌ Batch upload error: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    cache_stats = disaster_cache.get_cache_stats()
    
    # Check blockchain status
    blockchain_healthy = False
    try:
        uploader = DisasterUploader()
        blockchain_healthy = True
    except:
        blockchain_healthy = False
    
    return {
        "status": "healthy",
        "service": "wrld-relief-crisis-monitor",
        "version": "2.0.0",
        "monitoring": "active",
        "disasters_loaded": len(current_disasters),
        "cache_healthy": cache_stats["cache_file_exists"],
        "blockchain_healthy": blockchain_healthy,
        "last_cache_update": cache_stats["last_update"],
        "timestamp": int(datetime.now().timestamp())
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
