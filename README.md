# UEM v2 - Unified Emotion Model

Cognitive architecture with emotional processing, social affect, and memory systems.

## Quick Start

### Requirements

- Python 3.10+
- Docker (for PostgreSQL persistence)

### PostgreSQL Setup

Start the PostgreSQL container:

```bash
# Stop and remove old container (if exists)
docker stop uem_v2_postgres 2>/dev/null
docker rm uem_v2_postgres 2>/dev/null

# Create new container
docker run -d \
  --name uem_v2_postgres \
  -e POSTGRES_USER=uem \
  -e POSTGRES_PASSWORD=uem_secret \
  -e POSTGRES_DB=uem_v2 \
  -p 5432:5432 \
  -v uem_v2_pgdata:/var/lib/postgresql/data \
  postgres:15

# Test connection
docker exec -it uem_v2_postgres psql -U uem -d uem_v2 -c "SELECT 1;"
```

Initialize the schema:

```bash
# Apply schema
docker exec -i uem_v2_postgres psql -U uem -d uem_v2 < sql/memory_schema.sql

# Verify tables
docker exec -it uem_v2_postgres psql -U uem -d uem_v2 -c "\dt"
```

### Environment Variables

```bash
# Database connection (optional, has defaults)
export UEM_DATABASE_URL="postgresql://uem:uem_secret@localhost:5432/uem_v2"

# Enable SQL logging (optional)
export UEM_SQL_ECHO="true"
```

### Running Tests

```bash
# Trust module tests
python tests/unit/test_trust.py

# All tests (requires pytest)
python -m pytest tests/ -v
```

## Architecture

```
UEM v2
├── foundation/          # Core types and state management
│   ├── state/          # StateVector system
│   └── types/          # Common types
├── core/               # Main modules
│   ├── affect/         # Emotional processing
│   │   ├── emotion/    # PAD model, basic emotions
│   │   └── social/     # Empathy, Sympathy, Trust
│   └── memory/         # Memory systems
│       ├── types.py    # Memory types
│       ├── store.py    # In-memory store
│       └── persistence/ # PostgreSQL layer
├── engine/             # Cognitive cycle
│   ├── cycle.py        # 10-phase cognitive loop
│   ├── phases/         # Phase definitions
│   ├── handlers/       # Phase handlers
│   └── events/         # Event bus
├── sql/                # Database schemas
└── docs/               # Documentation
```

## Modules

### Memory Module

Neuroscience-inspired memory system:

- **Sensory Buffer**: Ultra-short-term traces
- **Working Memory**: 7±2 capacity limit
- **Episodic Memory**: Event records (5W1H)
- **Semantic Memory**: Facts and concepts
- **Emotional Memory**: Affect-tagged memories
- **Relationship Memory**: Agent interaction history

### Social Affect

- **Empathy**: Understanding others' states
- **Sympathy**: Emotional response to others
- **Trust**: Multi-dimensional trust model

### Cognitive Cycle

10-phase processing loop:

1. SENSE - Raw sensory input
2. ATTEND - Attention direction
3. PERCEIVE - Meaning extraction
4. RETRIEVE - Memory retrieval
5. REASON - Reasoning
6. EVALUATE - Evaluation
7. FEEL - Emotional computation
8. DECIDE - Decision making
9. PLAN - Action planning
10. ACT - Action execution

## Docker Commands Reference

```bash
# Start container
docker start uem_v2_postgres

# Stop container
docker stop uem_v2_postgres

# View logs
docker logs uem_v2_postgres

# Connect to psql
docker exec -it uem_v2_postgres psql -U uem -d uem_v2

# Backup database
docker exec uem_v2_postgres pg_dump -U uem uem_v2 > backup.sql

# Restore database
docker exec -i uem_v2_postgres psql -U uem -d uem_v2 < backup.sql

# Apply memory decay (manual)
docker exec -it uem_v2_postgres psql -U uem -d uem_v2 -c "SELECT apply_memory_decay(0.01);"

# Get memory stats
docker exec -it uem_v2_postgres psql -U uem -d uem_v2 -c "SELECT * FROM get_memory_stats();"
```
