# Muscular Dystrophy Clinical Decision Support System

## Overview
A knowledge graph-driven RAG system for clinical decision support in rare muscular dystrophies, focusing on scenario-based differential diagnosis and management recommendations.

## Architecture

### Core Components

1. **Clinical Scenario Processor**
   - Accepts comprehensive patient presentations
   - Extracts phenotypes and clinical features
   - Maps to HPO (Human Phenotype Ontology) terms

2. **Knowledge Graph Engine**
   - Neo4j-based graph database
   - Stores gene-disease-phenotype relationships
   - Enables complex clinical reasoning queries

3. **RAG System**
   - Processes clinical guidelines and literature
   - Provides evidence-based recommendations
   - Maintains citation traceability

4. **Differential Diagnosis Module**
   - Phenotype-based disease ranking
   - Contextual variant interpretation
   - Probability scoring with explanations

## Supported Scenarios

### Primary Use Cases

1. **New Patient Presentation**
   - Input: Clinical features, lab values, family history
   - Output: Differential diagnosis, recommended tests, initial management

2. **Variant Interpretation**
   - Input: Genetic variant + clinical context
   - Output: Pathogenicity assessment, phenotype prediction, treatment eligibility

3. **Management Planning**
   - Input: Confirmed diagnosis + patient status
   - Output: Age-appropriate surveillance, treatment options, prognostic counseling

## Disease Coverage (Phase 1)

- **Duchenne Muscular Dystrophy (DMD)**
- **Becker Muscular Dystrophy (BMD)**
- **Limb-Girdle MD Type R1 (LGMDR1/LGMD2A)**
- **LAMA2-Related Congenital MD (MDC1A)**

## Technical Stack

- **Backend**: FastAPI (Python)
- **Graph DB**: Neo4j
- **Vector DB**: ChromaDB/Pinecone
- **LLM**: OpenAI GPT-4 / Claude
- **RAG**: LangChain
- **Frontend**: React + Next.js

## Project Structure

```
├── backend/
│   ├── api/               # FastAPI endpoints
│   ├── core/              # Core business logic
│   │   ├── scenario_processor.py
│   │   ├── differential_diagnosis.py
│   │   └── variant_interpreter.py
│   ├── knowledge_graph/   # Neo4j integration
│   ├── rag/              # RAG pipeline
│   └── data/             # Data ingestion scripts
│
├── frontend/
│   ├── components/       # React components
│   ├── pages/           # Next.js pages
│   └── utils/           # Helper functions
│
├── data/
│   ├── guidelines/      # Clinical guidelines
│   ├── gene_data/       # Genetic databases
│   └── scenarios/       # Test scenarios
│
└── notebooks/
    └── prototype.ipynb  # Development notebook
```

## Getting Started

### Prerequisites
- Python 3.9+
- Node.js 16+
- Neo4j 4.4+
- Docker (optional)

### Installation
```bash
# Backend setup
cd backend
pip install -r requirements.txt

# Frontend setup
cd frontend
npm install

# Start Neo4j
docker run -p 7474:7474 -p 7687:7687 neo4j:latest
```

## Example Clinical Scenario

```json
{
  "patient": {
    "age": "7 years",
    "sex": "male"
  },
  "symptoms": [
    "Progressive proximal muscle weakness",
    "Gowers sign positive",
    "Calf pseudohypertrophy"
  ],
  "labs": {
    "CK": "15000 U/L"
  },
  "question": "What is the diagnosis and management?"
}
```

## Development Status

- [x] Project planning and architecture
- [ ] Knowledge graph schema design
- [ ] Clinical scenario processor
- [ ] RAG pipeline implementation
- [ ] API development
- [ ] Frontend interface
- [ ] Testing with real scenarios

## References

- Birnkrant DJ, et al. Diagnosis and management of Duchenne muscular dystrophy. Lancet Neurol. 2018
- TREAT-NMD Standards of Care Guidelines
- ACMG/AMP Variant Interpretation Guidelines