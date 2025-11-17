# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a knowledge graph-driven clinical decision support system for rare muscular dystrophies, focusing on scenario-based differential diagnosis and management recommendations. The system processes comprehensive patient presentations (clinical features, lab results, genetic findings) and provides evidence-based diagnostic and treatment recommendations.

**Phase 1 Disease Coverage:** Duchenne Muscular Dystrophy (DMD), Becker Muscular Dystrophy (BMD), Limb-Girdle MD Type R1 (LGMDR1), LAMA2-Related Congenital MD (MDC1A).

## Tech Stack

- **Backend:** Python with FastAPI (`backend/api/`)
- **Graph Database:** Neo4j with Monarch Initiative database (1.3M+ nodes, 14.7M+ relationships)
- **In-memory Fallback:** Custom memory store for clinical data when Neo4j unavailable
- **Variant Database:** NCBI ClinVar API (E-utilities) with 30-day caching
- **RAG:** Google Gemini File Search API for clinical guideline retrieval
- **Frontend:** React + Next.js with TypeScript (`frontend/`)
- **Deployment:** Uvicorn ASGI server (backend), Next.js dev server (frontend)

## Development Setup

### Python Environment

**Using uv (Recommended):**
```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment
uv venv
source .venv/bin/activate  # On macOS/Linux
# .venv\Scripts\activate  # On Windows

# Install dependencies from pyproject.toml (creates/updates uv.lock)
uv sync

# Or install dependencies directly
uv pip install neo4j pydantic python-dotenv

# Install with dev dependencies (for notebooks)
uv sync --extra dev
```

**Alternative: Using pip:**
```bash
python -m venv venv
source venv/bin/activate
pip install neo4j pydantic python-dotenv
```

**Dependencies:**
- `neo4j>=5.0.0` - Neo4j Python driver for database connectivity
- `pydantic>=2.0.0` - Data validation and settings management
- `python-dotenv>=1.0.0` - Environment variable management from .env files

### Neo4j Setup

The project uses **Neo4j** with the **Monarch Initiative** knowledge graph database, which provides comprehensive biomedical knowledge including:
- 1.3M+ nodes (diseases, genes, phenotypes, variants)
- 14.7M+ relationships (associations, interactions, causal links)
- Biolink Model schema (`biolink:Disease`, `biolink:Gene`, `biolink:PhenotypicFeature`, etc.)

**Configuration:**
1. **Install Neo4j Desktop** (recommended) or use Docker
2. **Import Monarch Initiative dump** into a database named `monarch`
3. **Create `.env` file** in project root:
   ```bash
   NEO4J_URI=neo4j://127.0.0.1:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=your-password
   NEO4J_DATABASE=monarch
   ```

**Data Sources:**
- **Disease/Gene/Phenotype Data:** Monarch Initiative database (1.3M+ nodes, 255K+ disease-phenotype associations)
- **Clinical Decision Support:** Curated data from [backend/knowledge_graph/clinical_data.py](backend/knowledge_graph/clinical_data.py)
  - Treatment recommendations with evidence levels
  - Variant annotations (exon deletions, reading frame rules, therapy eligibility)
  - Diagnostic pathways
- **Fallback:** In-memory store for clinical data when Neo4j unavailable

**Testing Connection:**
```bash
# Test Monarch database connection
python test_monarch_database.py

# Test general Neo4j connection
python test_neo4j_connection.py
```

**Important Schema Note:**
The Monarch Initiative uses the **Biolink Model** schema (e.g., `biolink:Disease`, `biolink:has_phenotype`), while the project's custom schema uses simpler labels (e.g., `Disease`, `HAS_PHENOTYPE`). The `KnowledgeGraphService` currently expects the custom schema. To use Monarch data, you'll need to either:
1. Create an adapter layer to translate between schemas
2. Write new queries matching Monarch's schema
3. Use both databases (custom for project-specific data, Monarch for broader biomedical knowledge)

### ClinVar Setup (Optional - Variant Enrichment)

The project integrates with **NCBI ClinVar** to enrich variant annotations with clinical significance data from multiple laboratories. This is used as a **showcase feature** - the curated `clinical_data.py` remains authoritative for reading frame predictions and therapy eligibility.

**Why Use ClinVar:**
- Multi-lab consensus on clinical significance (Pathogenic/Benign/VUS)
- Review status and confidence metrics
- Comprehensive variant catalogs for DMD, LAMA2, and CAPN3 genes
- Rich genomic coordinate and phenotype data
- **NOT** a replacement for `clinical_data.py` (ClinVar lacks reading frame rules and therapy eligibility)

**Setup Steps:**

1. **Get Free NCBI API Key** (recommended for higher rate limits):
   - Create account at https://www.ncbi.nlm.nih.gov/account/
   - Navigate to Settings → API Key Management
   - Generate new API key
   - **Rate limits:** 10 req/sec with API key, 3 req/sec without

2. **Add to `.env` file:**
   ```bash
   # NCBI ClinVar Integration (optional)
   NCBI_API_KEY=your_api_key_here
   ENABLE_CLINVAR=true
   ```

3. **Verify Integration:**
   ```bash
   python test_clinvar_integration.py
   ```
   This test script verifies:
   - API connectivity and authentication
   - Rate limiting (respects NCBI guidelines)
   - Caching mechanism (30-day TTL)
   - Enrichment preserves critical fields (reading frame, therapy eligibility)
   - Integration with KnowledgeGraphService

**API Endpoints:**
The project provides FastAPI endpoints for ClinVar integration:
- `POST /api/variants/interpret` - Interpret variant with curated + ClinVar data
- `GET /api/variants/search/{gene}` - Search variants by gene with ClinVar enrichment
- `GET /api/variants/clinvar/gene/{gene}` - Direct ClinVar API query (showcase)
- `GET /api/variants/therapies` - List FDA-approved therapies

See [backend/api/routes/variants.py](backend/api/routes/variants.py) for full API documentation.

**ClinVar Data Structure:**

The NCBI E-utilities API returns 12 fields per variant (see [backend/knowledge_graph/clinvar_service.py](backend/knowledge_graph/clinvar_service.py)):

```python
{
  "variation_id": "4526298",                    # Numeric ID
  "clinvar_accession": "VCV004526298",          # VCV accession
  "variant_name": "NC_000023.10:g.(...)del",    # HGVS notation
  "clinical_significance": "Pathogenic",        # From germline_classification
  "review_status": "criteria provided...",      # Review confidence
  "last_evaluated": "2025/07/22 00:00",         # Evaluation date
  "gene_symbol": "DMD",                         # Gene name
  "variant_type": "Deletion",                   # Type (obj_type)
  "chromosome": "X",                            # Chromosome
  "position_start": "33038318",                 # Start position
  "position_stop": "33229667",                  # End position
  "assembly": "GRCh37",                         # Reference genome
  "phenotypes": ["Neuromuscular disease..."]    # Associated diseases
}
```

**IMPORTANT - API Response Structure:**
NCBI ClinVar changed its API structure. The correct field paths are:
- Clinical significance: `variant_data['germline_classification']['description']` (NOT `clinical_significance`)
- Review status: `variant_data['germline_classification']['review_status']`
- Variant type: `variant_data['obj_type']` or `variation_set[0]['variant_type']`
- Phenotypes: `germline_classification['trait_set'][]['trait_name']`
- Location: `variation_set[0]['variation_loc'][0]` (chr, start, stop, assembly)

**Frontend Display:**
The frontend displays ClinVar data in a 7-column table:
1. **Accession** - Clickable VCV link
2. **Variant** - HGVS notation (truncated with tooltip)
3. **Type** - Deletion/Duplication/SNV with blue badge
4. **Significance** - Color-coded (🔴 Pathogenic, 🟢 Benign, 🟡 Uncertain)
5. **Review Status** - With evaluation date
6. **Location** - Chr:start-stop (assembly)
7. **Phenotype** - Associated disease/condition

See [frontend/components/ResultsPanel/index.tsx](frontend/components/ResultsPanel/index.tsx) lines 477-606 for table implementation.

**What Gets Enriched:**
- Gene-level queries for deletions (shows related DMD variants as reference)
- Point mutations and small indels get clinical significance labels
- Large exon deletions keep authoritative data from `clinical_data.py`
- **ClinVar adds:** All 12 fields above as `clinvar_variants` array
- **ClinVar NEVER overwrites:** `reading_frame`, `eligible_treatments`, `exons`

**Caching:**
- API responses cached for 30 days in `.clinvar_cache/` directory
- Minimizes API calls and respects rate limits
- Cache automatically invalidates after 30 days

**Disabling ClinVar:**
Set `ENABLE_CLINVAR=false` in `.env` or remove the variable. The system will function normally without ClinVar enrichment.

### Running Notebooks
```bash
# Start Jupyter
jupyter notebook

# Open the demo notebook
notebooks/demo_scenario_processing.ipynb
```

## Architecture Overview

### Core Processing Pipeline

The system follows a **scenario-driven** architecture where clinical scenarios flow through a processing pipeline:

1. **Input:** `ClinicalScenario` object containing patient demographics, symptoms, labs, genetic findings, and clinical questions
2. **Processing:** `ScenarioProcessor` orchestrates the analysis pipeline
3. **Knowledge Retrieval:** `KnowledgeGraphService` provides domain knowledge (disease profiles, variant annotations, recommendations)
4. **Output:** `ScenarioResponse` with differential diagnoses, variant interpretations, and clinical recommendations

### Key Components

#### 1. Clinical Scenario Models ([backend/core/clinical_scenario.py](backend/core/clinical_scenario.py))
- **Pydantic models** define the input/output schema
- `ClinicalScenario`: Comprehensive patient presentation input
- `ScenarioResponse`: Structured clinical decision support output
- `DifferentialDiagnosis`, `ClinicalRecommendation`, `GeneticFinding`: Supporting models
- **HPO Mapping:** Maps clinical features to Human Phenotype Ontology terms

#### 2. Scenario Processor ([backend/core/scenario_processor.py](backend/core/scenario_processor.py))
Main orchestration logic that:
- Extracts and maps clinical features to HPO terms
- Generates differential diagnoses by scoring disease matches
- Interprets genetic variants using the **reading frame rule** for DMD/BMD distinction
- Maps variants to treatment eligibility (e.g., exon-specific therapies like Eteplirsen for exon 51)
- Generates age-appropriate and disease-specific recommendations
- Answers specific clinical questions using rule-based logic

**Important:** The processor uses a **scoring system** combining:
- Symptom-to-disease feature matching (+20 per match)
- Age-appropriate onset windows (+15 if in range)
- Sex and inheritance pattern (+10 for X-linked diseases in males)
- Lab value interpretation (+15 for elevated CK)

#### 3. Knowledge Graph Service ([backend/knowledge_graph/service.py](backend/knowledge_graph/service.py))
Hybrid service combining real-world biomedical data with curated clinical guidelines:

**Data Sources:**
- **Monarch Database:** Disease profiles, gene associations, phenotype mappings (via `MonarchService`)
- **Clinical Data File:** Treatment recommendations, variant annotations, diagnostic pathways (via `clinical_data.py`)

**Architecture:**
- Queries Monarch Initiative for disease/gene/phenotype data (1.3M+ nodes)
- Supplements with curated clinical decision support from `clinical_data.py`
- Falls back to in-memory store when Neo4j unavailable

**Connection Logic:**
- Reads environment variables (`NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`, `NEO4J_DATABASE`)
- Connects to Monarch Neo4j database on initialization
- Falls back to in-memory + cached Monarch data if connection fails
- Logs connection status for debugging

**Schema Support:**
- Uses **Biolink Model** schema from Monarch (`biolink:Disease`, `biolink:Gene`, `biolink:PhenotypicFeature`)
- Clinical data uses project-specific schema (treatment categories, variant reading frames, etc.)

**Monarch Initiative Schema:**
The Monarch database uses **Biolink Model** schema:
- Node labels: `biolink:Disease`, `biolink:Gene`, `biolink:PhenotypicFeature`, etc.
- Relationships: `biolink:has_phenotype`, `biolink:causes`, `biolink:gene_associated_with_condition`, etc.

**Key Methods:**
- `get_disease_profiles()`: Returns disease metadata and phenotypes (Monarch) / legacy schema
- `get_variant_annotations()`: Variant → gene associations, falls back to legacy annotations
- `get_treatment_recommendations()`: Disease-specific management guidelines (custom/fallback)
- `search_diseases_by_phenotypes(hpo_ids)`: Ranks diseases based on Monarch phenotype overlap (feeds ScenarioProcessor scoring)

**Note:** To query Monarch data, you'll need to write Cypher queries using `biolink:` prefixed labels and relationship types, or create an adapter layer.

**Example Monarch Query:**
```cypher
// Find diseases associated with a gene
MATCH (g:`biolink:Gene` {id: "HGNC:2928"})-[:`biolink:causes`]->(d:`biolink:Disease`)
RETURN d.id, d.name LIMIT 10

// Find phenotypes for a disease
MATCH (d:`biolink:Disease` {id: "MONDO:0007254"})-[:`biolink:has_phenotype`]->(p:`biolink:PhenotypicFeature`)
RETURN p.id, p.name LIMIT 10
```

Note: Labels with colons must be escaped with backticks in Cypher: `` `biolink:Disease` ``

#### 4. Knowledge Graph Schema ([backend/knowledge_graph/schema.py](backend/knowledge_graph/schema.py))
Defines the graph model with nodes (Disease, Gene, Phenotype, Variant, Treatment, etc.) and relationships (HAS_PHENOTYPE, CAUSED_BY_MUTATION_IN, ELIGIBLE_FOR, etc.). Schema applies to both Neo4j and in-memory implementations.

#### 5. Clinical Data ([backend/knowledge_graph/clinical_data.py](backend/knowledge_graph/clinical_data.py))
Curated clinical decision support data **not available in Monarch**:
- **Treatment recommendations:** Evidence-based guidelines (Level A/B/C) with urgency classifications
- **Variant annotations:** DMD exon deletions with reading frame rules and FDA therapy eligibility
- **Diagnostic pathways:** Step-by-step clinical workflows (elevated CK pathway, infant hypotonia pathway)
- **General recommendations:** Fallback guidance when diagnosis uncertain

**Note:** Disease/gene/phenotype data now comes from Monarch database, not this file.
**Archived:** Previous `seed_data.py` moved to `backend/temp_archived/seed_data.py.archived`

### Data Flow Example

```
User Input (ClinicalScenario)
    ↓
ScenarioProcessor.process_scenario()
    ↓
├─→ extract_hpo_terms() → HPO mappings
├─→ _generate_differential_diagnosis() → Scored disease matches
│       ↓
│   KnowledgeGraphService.get_disease_profiles()
│
├─→ _interpret_variants() → Variant analysis
│       ↓
│   KnowledgeGraphService.get_variant_annotations()
│
├─→ _generate_recommendations()
│       ↓
│   KnowledgeGraphService.get_treatment_recommendations()
│
└─→ _answer_clinical_questions() → Question-specific answers
    ↓
ScenarioResponse (differential, variant interpretation, recommendations)
```

## Important Implementation Details

### DMD vs BMD Distinction (Reading Frame Rule)
The system distinguishes Duchenne from Becker muscular dystrophy based on whether deletions are in-frame or out-of-frame:
- **Out-of-frame deletions** → DMD (severe phenotype)
- **In-frame deletions** → BMD (milder phenotype)

See `ScenarioProcessor._check_reading_frame()` in [backend/core/scenario_processor.py:195-212](backend/core/scenario_processor.py#L195-L212) and the fallback interpreter at lines 164-192.

### Exon-Specific Treatment Eligibility
The system maps specific DMD exon deletions to FDA-approved exon-skipping therapies:
- Exon 45: Casimersen (Amondys 45)
- Exon 51: Eteplirsen (Exondys 51)
- Exon 53: Golodirsen (Vyondys 53), Viltolarsen (Viltepso)

This logic appears in both `seed_data.py` variant annotations and the fallback interpreter.

### Age-Appropriate Scoring
Differential diagnosis scoring includes age-based boosts:
- DMD: +10 score if patient age 3-8 years
- BMD: +10 score if patient age >10 years
- LAMA2-CMD: +15 score if patient age <2 years

See `ScenarioProcessor._generate_differential_diagnosis()` in [backend/core/scenario_processor.py:73-117](backend/core/scenario_processor.py#L73-L117).

### Confidence Thresholds
Only diseases scoring >30 points are included in the differential diagnosis, with a maximum of 5 diseases returned (sorted by confidence score).

## Project Status

Based on git history and code structure:
- ✅ Project architecture and domain models
- ✅ Knowledge graph schema and seed data
- ✅ Scenario processor with variant interpretation
- ✅ In-memory knowledge store with Neo4j support
- ✅ Neo4j connection to Monarch Initiative database (1.3M+ nodes, 14.7M+ relationships)
- ✅ Database connection testing scripts (`test_monarch_database.py`, `test_neo4j_connection.py`)
- ✅ Demonstration notebook with 4 test cases
- ✅ **FastAPI backend** (`backend/api/`) with routes for scenarios, variants, knowledge graph, and RAG
- ✅ **ClinVar integration** (`backend/knowledge_graph/clinvar_service.py`) with 4 API endpoints and 12-field data structure
- ✅ **Gemini RAG pipeline** (`backend/rag/gemini_file_search.py`) for clinical guideline retrieval
- ✅ **Next.js frontend** (`frontend/`) with React components for scenario submission and results display
- ✅ **Variant interpretation UI** with 7-column ClinVar table showing clinical significance, genomic coordinates, and phenotypes
- ⚠️ Schema adapter needed (Monarch uses `biolink:` schema, project uses custom schema)

## Testing Approach

Use the Jupyter notebook [notebooks/demo_scenario_processing.ipynb](notebooks/demo_scenario_processing.ipynb) to test scenarios. Four test cases are implemented:
1. Classic DMD presentation (young boy with exon 45-47 deletion)
2. BMD presentation (older patient with in-frame deletion)
3. Diagnostic dilemma without genetic data
4. Infant with LAMA2-CMD (white matter changes on MRI)

To add new test scenarios:
```python
from backend.core.clinical_scenario import ClinicalScenario, Patient
from backend.core.scenario_processor import ScenarioProcessor

scenario = ClinicalScenario(
    patient=Patient(age="...", sex="..."),
    chief_complaint="...",
    presenting_symptoms=[...],
    # ... other fields
)

processor = ScenarioProcessor()
response = processor.process_scenario(scenario)
```

## Clinical Domain References

The system is based on established clinical guidelines:
- Birnkrant DJ, et al. Diagnosis and management of Duchenne muscular dystrophy. Lancet Neurol. 2018
- TREAT-NMD Standards of Care Guidelines
- ACMG/AMP Variant Interpretation Guidelines

Treatment recommendations include evidence levels (Level A/B/C) and urgency classifications (immediate/urgent/routine).

## Adding New Diseases

**Disease data now comes from Monarch Initiative** (1.3M+ nodes). To add support for a new muscular dystrophy:

1. **Add disease mapping** to `DISEASE_CODE_MAP` in [backend/knowledge_graph/monarch_mapper.py](backend/knowledge_graph/monarch_mapper.py)
   - Map project code (e.g., "LGMD2I") to Monarch IDs (e.g., MONDO:xxx, OMIM:xxx)
2. **Add treatment recommendations** to `TREATMENT_RECOMMENDATIONS` in [backend/knowledge_graph/clinical_data.py](backend/knowledge_graph/clinical_data.py)
   - Include evidence levels (Level A/B/C) and urgency classifications
3. **Add variant annotations** (if applicable) to `VARIANT_ANNOTATIONS` in [backend/knowledge_graph/clinical_data.py](backend/knowledge_graph/clinical_data.py)
   - Include exon numbers, reading frame predictions, therapy eligibility
4. **Update scoring logic** in `ScenarioProcessor` if needed for disease-specific rules (e.g., age-appropriate onset windows)
5. **Verify in Monarch** that the disease exists with adequate phenotype associations

**Note:** No database seeding required - Monarch data is already loaded!

## File Organization

```
backend/
├── core/
│   ├── clinical_scenario.py      # Pydantic models (input/output schema)
│   └── scenario_processor.py     # Main processing pipeline
├── knowledge_graph/
│   ├── schema.py                  # Graph schema definition (custom schema, legacy)
│   ├── service.py                 # Hybrid service (Monarch + clinical data)
│   ├── monarch_service.py         # Monarch Initiative query layer
│   ├── monarch_mapper.py          # Biolink ↔ project schema mapping (disease/gene IDs)
│   ├── clinical_data.py           # Curated clinical guidelines (treatments, variants, pathways)
│   └── memory.py                  # In-memory store (fallback)
└── temp_archived/
    ├── seed_data.py.archived      # DEPRECATED: Replaced by Monarch + clinical_data
    └── README.md                  # Migration notes

docs/
├── pdfs/                          # Original project documentation (PDFs)
│   ├── HINF 6205 Project Paper.pdf
│   ├── HINF 6205 Project deliverable 1.pdf
│   └── Project_research.pdf
└── markdown/                      # Extracted markdown documentation (via semtools)
    ├── HINF 6205 Project Paper.pdf.md
    ├── HINF 6205 Project deliverable 1.pdf.md
    └── Project_research.pdf.md

notebooks/
└── demo_scenario_processing.ipynb # Test scenarios and demonstrations

# Testing and utilities
test_monarch_database.py           # Explore Monarch Initiative database schema
test_neo4j_connection.py          # Test Neo4j connection and basic queries
test_monarch_integration.py       # Smoke tests for KnowledgeGraphService + Monarch
.env                                # Neo4j connection configuration (not in git)
```

## Documentation Extraction

Project documentation PDFs have been converted to markdown using [semtools](https://github.com/run-llama/semtools), a CLI tool from LlamaIndex for document parsing and semantic search.

### Setup
```bash
# Install semtools
npm i -g @llamaindex/semtools

# Configure API key (get free key from https://cloud.llamaindex.ai)
# Create ~/.parse_config.json with your LlamaIndex Cloud API key
```

### Extract PDFs to Markdown
```bash
# Parse PDFs (cached to ~/.parse/)
parse docs/pdfs/*.pdf

# Copy to organized location
cp ~/.parse/*.md docs/markdown/
```

The markdown files preserve document structure, tables (as HTML), and formatting, making them suitable for RAG pipelines and semantic search.

## Code Conventions

- **Pydantic models** are used extensively for data validation and schema definition
- **Type hints** are used throughout (Python 3.9+)
- **Optional parameters** use `Optional[T]` from typing
- **Docstrings** follow standard Python format with parameter and return descriptions
- **Error handling** uses broad except clauses with logging (see `KnowledgeGraphService.__init__`)
