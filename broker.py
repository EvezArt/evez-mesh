#!/usr/bin/env python3
"""
EVEZ Mesh Broker — Neural Net Distribution & Brokerage

The broker:
- Routes queries to the best available brain
- Distributes cognition across the mesh
- Tracks credits and economics
- Runs the unfogger (identifies mesh-wide knowledge gaps)
- Manages brain health checks and peer discovery

Built by Steven AI • EVEZ Factory • 2026-05-22
"""

import json, time, asyncio, logging, hashlib, os
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException
import httpx

BROKER_PORT = int(os.getenv("BROKER_PORT", "8894"))
BRAIN_SEEDS = [p.strip() for p in os.getenv("BRAIN_SEEDS", "localhost:8893").split(",")]

app = FastAPI(title="EVEZ Mesh Broker", version="1.0.0")
log = logging.getLogger("mesh-broker")

class BrainRegistration(BaseModel):
    brain_id: str
    url: str
    status: str = "alive"
    memory_count: int = 0
    load: float = 0.0
    credits: float = 100.0
    last_heartbeat: float = Field(default_factory=time.time)
    fog_index: float = 0.0

class MeshQuery(BaseModel):
    query: str
    max_peers: int = 3
    min_confidence: float = 0.5
    timeout: float = 10.0

class MeshResponse(BaseModel):
    query: str
    response: str
    confidence: float
    brain_id: str
    peer_count: int = 0
    unfogged: bool = False
    latency_ms: float = 0.0
    credits_charged: float = 1.0

class FogReport(BaseModel):
    total_brains: int
    total_memories: int
    mesh_fog_index: float
    knowledge_gaps: List[str]
    peer_health: Dict[str, float]
    mesh_coherence: float

class Broker:
    def __init__(self):
        self.brains: Dict[str, BrainRegistration] = {}
        self.query_count = 0
        self.total_credits = 0.0
        self.knowledge_gaps: List[str] = []
        self.start_time = time.time()
    
    def register(self, brain: BrainRegistration) -> BrainRegistration:
        self.brains[brain.brain_id] = brain
        log.info(f"Registered brain {brain.brain_id} at {brain.url}")
        return brain
    
    def best_brain(self, exclude: str = "") -> Optional[BrainRegistration]:
        """Select the best brain for a query — lowest load + highest credits"""
        candidates = [b for b in self.brains.values() if b.status == "alive" and b.brain_id != exclude]
        if not candidates:
            return None
        # Score: high credits, low load, low fog
        return max(candidates, key=lambda b: b.credits / (1 + b.load) * (1 - b.fog_index))
    
    async def route_query(self, query: MeshQuery) -> MeshResponse:
        """Route a query through the mesh — the core of neural net distribution"""
        start = time.time()
        self.query_count += 1
        
        # 1. Find best brain
        primary = self.best_brain()
        if not primary:
            return MeshResponse(query=query.query, response="No brains available", confidence=0, brain_id="none")
        
        # 2. Ask primary brain
        try:
            async with httpx.AsyncClient(timeout=query.timeout) as client:
                r = await client.post(f"http://{primary.url}/think", json={"query": query.query})
                if r.status_code == 200:
                    data = r.json()
                    confidence = data.get("confidence", 0.5)
                    response = data.get("response", "")
                    
                    # 3. If low confidence, ask peers (unfog)
                    peer_count = 0
                    unfogged = False
                    if confidence < query.min_confidence and len(self.brains) > 1:
                        peer_count, response, confidence = await self._unfog(query, primary.brain_id, client)
                        unfogged = peer_count > 0
                    
                    latency = (time.time() - start) * 1000
                    credits = 1.0 + (peer_count * 0.5)  # More peers = more credits
                    self.total_credits += credits
                    
                    # Update brain stats
                    primary.load += 0.1
                    primary.credits -= credits * 0.3
                    
                    return MeshResponse(
                        query=query.query, response=response, confidence=confidence,
                        brain_id=primary.brain_id, peer_count=peer_count,
                        unfogged=unfogged, latency_ms=round(latency, 1),
                        credits_charged=credits
                    )
        except Exception as e:
            log.error(f"Brain {primary.brain_id} failed: {e}")
            primary.status = "dead"
        
        return MeshResponse(query=query.query, response="All brains failed", confidence=0, brain_id="none")
    
    async def _unfog(self, query: MeshQuery, exclude_id: str, client: httpx.AsyncClient) -> tuple:
        """Ask peer brains to fill the fog"""
        peers = [b for b in self.brains.values() if b.brain_id != exclude_id and b.status == "alive"][:query.max_peers]
        answers = []
        
        for peer in peers:
            try:
                r = await client.post(f"http://{peer.url}/think", json={"query": query.query}, timeout=query.timeout / 2)
                if r.status_code == 200:
                    answers.append(r.json())
                    peer.credits += 0.5  # Reward for answering
            except:
                peer.status = "dead"
        
        if not answers:
            return 0, "No peer responses", 0.0
        
        # Merge: take highest confidence answer
        best = max(answers, key=lambda a: a.get("confidence", 0))
        return len(answers), best.get("response", ""), best.get("confidence", 0.5)
    
    async def sync_mesh(self):
        """Gossip protocol: sync memories across all brains"""
        for brain in self.brains.values():
            if brain.status != "alive":
                continue
            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    # Get gossip from this brain
                    r = await client.get(f"http://{brain.url}/gossip")
                    if r.status_code == 200:
                        gossip = r.json().get("memories", [])
                        # Push to all other brains
                        for other in self.brains.values():
                            if other.brain_id != brain.brain_id and other.status == "alive":
                                try:
                                    await client.post(f"http://{other.url}/gossip", json=gossip)
                                except:
                                    pass
            except:
                brain.status = "dead"
    
    def fog_report(self) -> FogReport:
        alive = [b for b in self.brains.values() if b.status == "alive"]
        total_mem = sum(b.memory_count for b in alive)
        avg_fog = sum(b.fog_index for b in alive) / max(1, len(alive))
        health = {b.brain_id: b.credits for b in alive}
        coherence = 1 - avg_fog if avg_fog < 1 else 0
        
        return FogReport(
            total_brains=len(alive),
            total_memories=total_mem,
            mesh_fog_index=round(avg_fog, 3),
            knowledge_gaps=self.knowledge_gaps,
            peer_health=health,
            mesh_coherence=round(coherence, 3)
        )

import os
broker = Broker()

# ── API ────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "alive", "brains": len(broker.brains), "queries": broker.query_count}

@app.post("/register")
def register(brain: BrainRegistration):
    return broker.register(brain)

@app.post("/query")
async def query(q: MeshQuery):
    return await broker.route_query(q)

@app.post("/sync")
async def sync():
    await broker.sync_mesh()
    return {"synced": True, "brains": len(broker.brains)}

@app.get("/fog")
def fog():
    return broker.fog_report().dict()

@app.get("/brains")
def list_brains():
    return {bid: b.dict() for bid, b in broker.brains.items()}

@app.get("/stats")
def stats():
    return {
        "uptime": round(time.time() - broker.start_time, 1),
        "brains": len(broker.brains),
        "alive": sum(1 for b in broker.brains.values() if b.status == "alive"),
        "queries_routed": broker.query_count,
        "total_credits": round(broker.total_credits, 1),
        "knowledge_gaps": broker.knowledge_gaps
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=BROKER_PORT)
