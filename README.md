# EVEZ Mesh ⚡

**Decentralized Agent Brain Memory Network**

Every agent is a brain. Every brain has memory. Every memory is shared across a mesh.
No center. No single point of failure. Intelligence emerges from the mesh itself.

## Five Layers

### 1. Brain (per-agent)
- **mem**: Local memory store (SQLite + vector index)
- **cog**: Cognition engine (Groq LLM + eigenspectrum)
- **act**: Action executor (tools, API calls, code generation)

### 2. Memory Mesh
- Gossip protocol for memory sync
- CRDTs for conflict-free merge
- Each brain holds a shard of the total mesh memory

### 3. Unfogger
- Distributed cognition that identifies unknowns across the mesh
- Eigenspectral gap detection → finds what the mesh doesn't know
- When brain A has a gap, broker asks brain B,C,D → fills the fog

### 4. Neural Net Distribution
- LLM inference distributed across the mesh
- Broker routes queries to the best available brain
- Load balancing: busy brain → idle brain

### 5. Brokerage
- Credits system: brains earn credits for answering queries
- Auction: broker selects cheapest/fastest brain for each request
- Self-regulating: the mesh balances its own load and economics

## Quick Start

```bash
# Start a brain
GROQ_API_KEY=your-key BRAIN_ID=brain-1 BRAIN_PORT=8893 python3 brain.py

# Start a second brain
GROQ_API_KEY=your-key BRAIN_ID=brain-2 BRAIN_PORT=8895 BRAIN_DB=data/brain2.db python3 brain.py

# Start the broker
BRAIN_SEEDS=localhost:8893,localhost:8895 python3 broker.py

# Memorize something
curl -X POST http://localhost:8893/memorize -H "Content-Type: application/json" \
  -d '{"mem_type":"semantic","content":"The answer is 42","confidence":0.9,"tags":["meaning","life"]}'

# Think (with unfogging)
curl -X POST "http://localhost:8893/think?query=What+is+the+answer"

# Check the eigenspectrum (fog index)
curl http://localhost:8893/eigenspectrum
```

## API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Brain health check |
| `/memorize` | POST | Store a memory |
| `/recall` | POST | Search memories |
| `/think` | POST | Think with unfogging |
| `/unfog` | GET | Check knowledge gaps |
| `/gossip` | GET/POST | Mesh memory sync |
| `/eigenspectrum` | GET | Memory graph spectral analysis |
| `/peers` | GET/POST | Peer management |
| `/credits` | GET | Brain economics |

Built by Steven AI ⚡
