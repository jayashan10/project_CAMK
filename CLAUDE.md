# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a knowledge graph-driven clinical decision support system for rare muscular dystrophies, focusing on scenario-based differential diagnosis and management recommendations. The system processes comprehensive patient presentations (clinical features, lab results, genetic findings) and provides evidence-based diagnostic and treatment recommendations.

**Phase 1 Disease Coverage:** Duchenne Muscular Dystrophy (DMD), Becker Muscular Dystrophy (BMD), Limb-Girdle MD Type R1 (LGMDR1), LAMA2-Related Congenital MD (MDC1A).

## Tech Stack

- **Backend:** Python (FastAPI planned)
- **Graph Database:** Neo4j (with in-memory fallback for development)
- **Vector Database:** ChromaDB/Pinecone (planned)
- **LLM:** OpenAI GPT-4 / Claude (planned)
- **RAG:** LangChain (planned)
- **Frontend:** React + Next.js (planned)

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

**Fallback Behavior:**
- **With Neo4j:** Connects to Monarch database and uses real-world biomedical data
- **Without Neo4j:** Automatically falls back to in-memory knowledge store seeded from [backend/knowledge_graph/seed_data.py](backend/knowledge_graph/seed_data.py)

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
Dual-mode service that abstracts storage:
- **Neo4j mode:** Connects to Neo4j database (Monarch Initiative or custom schema)
- **In-memory mode:** Python dictionaries seeded from `seed_data.py` (automatic fallback)

**Connection Logic:**
- Reads environment variables (`NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`, `NEO4J_DATABASE`)
- Attempts Neo4j connection on initialization
- Falls back to in-memory store if connection fails or variables not set
- Logs connection status for debugging

**Current Schema Support:**
The service queries expect the **custom schema** defined in `schema.py`:
- Node labels: `Disease`, `Gene`, `Phenotype`, `Variant`, `Treatment`, etc.
- Relationships: `HAS_PHENOTYPE`, `CAUSED_BY_MUTATION_IN`, `ELIGIBLE_FOR`, etc.

**Monarch Initiative Schema:**
The Monarch database uses **Biolink Model** schema:
- Node labels: `biolink:Disease`, `biolink:Gene`, `biolink:PhenotypicFeature`, etc.
- Relationships: `biolink:has_phenotype`, `biolink:causes`, `biolink:gene_associated_with_condition`, etc.

**Key Methods:**
- `get_disease_profiles()`: Returns disease metadata, phenotypes, and diagnostic tests (custom schema)
- `get_variant_annotations()`: Returns variant-to-phenotype and variant-to-treatment mappings
- `get_treatment_recommendations()`: Disease-specific management guidelines

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

#### 5. Seed Data ([backend/knowledge_graph/seed_data.py](backend/knowledge_graph/seed_data.py))
Curated domain knowledge including:
- Disease profiles with clinical features and onset patterns
- Variant annotations with reading frame predictions
- Treatment recommendations with evidence levels
- Diagnostic pathways

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
- ⚠️ Schema adapter needed (Monarch uses `biolink:` schema, project uses custom schema)
- ❌ FastAPI endpoints (planned, see README)
- ❌ RAG pipeline for literature (planned)
- ❌ Frontend interface (planned)

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

To add a new muscular dystrophy:
1. Add disease profile to `DISEASES` list in [backend/knowledge_graph/seed_data.py](backend/knowledge_graph/seed_data.py)
2. Include phenotypes with HPO IDs and specificity scores
3. Add diagnostic tests with frequency recommendations
4. Add treatment recommendations to `TREATMENT_RECOMMENDATIONS` list
5. Re-seed the knowledge graph (automatic on next run)
6. Update scoring logic in `ScenarioProcessor` if needed for disease-specific rules

## File Organization

```
backend/
├── core/
│   ├── clinical_scenario.py      # Pydantic models (input/output schema)
│   └── scenario_processor.py     # Main processing pipeline
└── knowledge_graph/
    ├── schema.py                  # Graph schema definition (custom schema)
    ├── service.py                 # Knowledge retrieval service (Neo4j + in-memory)
    ├── seed_data.py               # Curated clinical domain knowledge
    └── memory.py                  # In-memory store implementation (if separate)

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
