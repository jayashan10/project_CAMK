# Clinical Decision Support System - Web UI

This document provides instructions for running the complete web-based UI for the Clinical Decision Support System, including both the FastAPI backend and Next.js frontend.

## Architecture Overview

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────────┐
│   Next.js UI    │ ──HTTP──│   FastAPI API    │ ──────── │  Neo4j / Monarch    │
│  (Port 3000)    │         │   (Port 8000)    │         │   Knowledge Graph   │
└─────────────────┘         └──────────────────┘         └─────────────────────┘
                                      │
                                      └──────────── In-Memory Fallback
```

## Prerequisites

1. **Python 3.9+** with `uv` package manager (recommended) or `pip`
2. **Node.js 18+** with `npm`
3. **Neo4j** (optional - system falls back to in-memory mode if unavailable)

## Setup Instructions

### 1. Backend Setup

#### Install Python Dependencies

Using `uv` (recommended):
```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On macOS/Linux
# .venv\Scripts\activate  # On Windows

# Install all dependencies including FastAPI
uv sync
```

Using `pip`:
```bash
python -m venv venv
source venv/bin/activate

pip install -e .
```

#### Configure Neo4j (Optional)

If you want to use the Monarch Initiative knowledge graph:

1. Create a `.env` file in the project root:
```bash
NEO4J_URI=neo4j://127.0.0.1:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password
NEO4J_DATABASE=monarch
```

2. Start Neo4j with the Monarch database

**Note:** The system will automatically fall back to in-memory mode if Neo4j is not available.

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Return to project root
cd ..
```

## Running the Application

You need to run **both** the backend and frontend servers.

### Terminal 1: Start the Backend API

```bash
# Activate virtual environment if not already active
source .venv/bin/activate  # or venv/bin/activate if using pip

# Start the FastAPI server
uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**API Endpoints:**
- Health check: http://localhost:8000/health
- API docs: http://localhost:8000/docs
- Process scenario: POST http://localhost:8000/api/scenarios/process

### Terminal 2: Start the Frontend

```bash
cd frontend

# Start the Next.js dev server
npm run dev
```

You should see:
```
  ▲ Next.js 15.0.0
  - Local:        http://localhost:3000
  - Ready in 1.2s
```

### 3. Open the Application

Navigate to **http://localhost:3000** in your web browser.

## Using the Application

### 1. Select an Example Scenario

The home page displays 4 example clinical scenarios:
- **Classic DMD Presentation** - 6-year-old boy with progressive weakness
- **Becker Muscular Dystrophy** - 15-year-old with preserved ambulation
- **Clinical Presentation Without Genetics** - Diagnostic workup without genetic data
- **Infant with Congenital MD** - 6-month-old with hypotonia and MRI findings

Click any example to load it.

### 2. Analyze the Scenario

Click the **"Analyze Scenario"** button to process the clinical case through the system.

### 3. View Results

The system displays:

#### Clinical Reasoning Workflow Graph
- **Interactive React Flow visualization** showing:
  - Symptoms → HPO Mapping → Knowledge Graph Query → Diseases → Variant Analysis → Treatments
  - Confidence scores on edges
  - Color-coded nodes by type
  - Zoomable and pannable
  - Mini-map for navigation

#### Differential Diagnosis
- Ranked disease possibilities with confidence scores
- Supporting and inconsistent clinical features
- Recommended diagnostic tests

#### Genetic Findings
- Variant interpretation (if genetic data provided)
- Reading frame analysis (in-frame vs out-of-frame)
- Treatment eligibility based on exon deletions

#### Clinical Recommendations
- Categorized by: Treatment, Surveillance, Diagnosis, Genetic Counseling
- Evidence levels (A/B/C)
- Urgency classification (immediate/urgent/routine)
- References to clinical guidelines

#### Clinical Question Answers
- Specific answers to each clinical question in the scenario

## Troubleshooting

### Backend Issues

**Error: "Connection refused" or API not responding**
- Ensure the backend server is running on port 8000
- Check that no other service is using port 8000
- Verify with: `curl http://localhost:8000/health`

**Error: Neo4j connection failed**
- This is expected if Neo4j is not running
- The system will automatically use in-memory mode
- Check backend logs for: "Falling back to in-memory knowledge store"

**Error: Module not found**
- Ensure you've activated the virtual environment
- Run `uv sync` or `pip install -e .` again

### Frontend Issues

**Error: "Cannot connect to API"**
- Ensure the backend is running on port 8000
- Check browser console for CORS errors
- Verify the API proxy is configured in `next.config.js`

**Error: Module not found in frontend**
- Run `npm install` in the frontend directory
- Delete `node_modules` and `.next` directories and reinstall

**Error: TypeScript errors**
- Run `npm run build` to check for type errors
- Ensure all dependencies are installed

### Common Issues

**Slow initial load**
- First request may be slow as the knowledge graph initializes
- Subsequent requests will be faster

**Empty differential diagnosis**
- Check that the knowledge graph has data
- Verify Neo4j connection or in-memory fallback
- Check backend logs for errors

## Development

### Hot Reload

Both servers support hot reload:
- **Backend**: FastAPI automatically reloads when Python files change
- **Frontend**: Next.js automatically reloads when React components change

### Adding New Scenarios

Edit `frontend/components/ExampleScenarios.tsx` to add more example scenarios.

### Modifying the Workflow Graph

- Custom node types: `frontend/components/WorkflowGraph/nodes/`
- Graph layout: `frontend/lib/workflowBuilder.ts`
- Main component: `frontend/components/WorkflowGraph/index.tsx`

## Production Deployment

### Backend

```bash
# Install production dependencies
uv sync

# Run with production server
uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Frontend

```bash
cd frontend

# Build for production
npm run build

# Start production server
npm start
```

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **Neo4j** - Graph database (Monarch Initiative knowledge graph)
- **Pydantic** - Data validation
- **Python 3.9+** - Core language

### Frontend
- **Next.js 15** - React framework with App Router
- **TypeScript** - Type-safe JavaScript
- **Tailwind CSS** - Utility-first CSS framework
- **React Flow** - Interactive graph visualization
- **Dagre** - Graph layout algorithm
- **Axios** - HTTP client

## API Documentation

Interactive API documentation is available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Data Sources

- **Monarch Initiative**: 1.3M+ biomedical entities, 14.7M+ relationships
- **Curated Clinical Data**: Treatment recommendations, variant annotations (backend/knowledge_graph/clinical_data.py)
- **Clinical Guidelines**: TREAT-NMD, ACMG standards

## Next Steps

- Implement multi-step wizard for custom scenario input
- Add RAG-powered literature search
- Implement case management (save/load scenarios)
- Add clinical trial matching
- Enable multi-scenario comparison

## Support

For issues or questions:
1. Check the [main README.md](README.md) for project documentation
2. Review [CLAUDE.md](CLAUDE.md) for architecture details
3. Check backend logs for detailed error messages
4. Open an issue in the project repository
