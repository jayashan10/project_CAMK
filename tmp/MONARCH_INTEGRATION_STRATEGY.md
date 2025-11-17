# Monarch Initiative Database Integration Strategy

## ✅ MIGRATION COMPLETE (2025-11-15)

**Status:** The migration from `seed_data.py` to Monarch Initiative database + `clinical_data.py` is **COMPLETE** and **VERIFIED**.

**What Changed:**
- ✅ Disease/gene/phenotype data now sourced from Monarch Initiative (1.3M+ nodes, 255K+ associations)
- ✅ Treatment recommendations, variant annotations, and pathways preserved in `clinical_data.py`
- ✅ `seed_data.py` archived to `backend/temp_archived/seed_data.py.archived`
- ✅ All imports and references updated
- ✅ Tests passing with KnowledgeGraphService

**Data Flow:**
```
ScenarioProcessor
    ↓
KnowledgeGraphService
    ├─→ Monarch Database (diseases, genes, phenotypes)
    └─→ clinical_data.py (treatments, variants, pathways)
```

---

## Executive Summary

This document outlines the **completed integration** of the Monarch Initiative Neo4j knowledge graph (1.3M+ nodes, 14.7M+ relationships) into the Project CAMK clinical decision support system. The system now uses real-world biomedical data from Monarch supplemented with curated clinical guidelines.

**Date:** 2025-11-15
**Database:** monarch (Neo4j at neo4j://127.0.0.1:7687)
**Exploration Scripts:** `explore_monarch_database.py`, `explore_md_specific.py`
**Migration Date:** 2025-11-15

---

## 1. Database Overview

### 1.1 Schema Architecture

The Monarch database uses the **Biolink Model** ontology schema:

**Node Labels** (46 total, key ones):
- `biolink:Disease` - 14,000+ disease nodes
- `biolink:Gene` - 617,827 gene nodes (multi-species)
- `biolink:PhenotypicFeature` - 168,000+ phenotype nodes
- `biolink:SequenceVariant` - Variant nodes (present but unpopulated in current dump)

**Relationship Types** (36 total, key ones):
- `biolink:has_phenotype` - Disease → Phenotype (255,967 associations)
- `biolink:causes` - Gene → Disease (8,919 associations)
- `biolink:gene_associated_with_condition` - Gene ↔ Disease (8,101 associations)
- `biolink:has_mode_of_inheritance` - Disease → Inheritance pattern (8,821 associations)

**Important:** The custom schema defined in `backend/knowledge_graph/schema.py` (Disease, Gene, Phenotype) has **0 nodes** in this database. All data uses `biolink:` prefixed labels.

### 1.2 Data Statistics

```
Total Nodes:        1,307,970
Total Relationships: 14,700,000+
Disease-Phenotype:   255,967 associations
Gene-Disease:        17,020 associations (combined causes + gene_associated_with_condition)
```

---

## 2. Muscular Dystrophy Coverage

### 2.1 Diseases Found

The Monarch database contains comprehensive coverage of muscular dystrophies:

| Disease | MONDO ID | Genes | Phenotypes | Inheritance |
|---------|----------|-------|------------|-------------|
| **Duchenne Muscular Dystrophy** | MONDO:0010679 | DMD, LTBP4 | 20+ HPO terms | X-linked recessive (HP:0001419) |
| **Becker Muscular Dystrophy** | MONDO:0010311 | DMD | 20+ HPO terms | X-linked recessive (HP:0001419) |
| **LAMA2-related CMD (MDC1A)** | MONDO:0011925 | LAMA2 | Not explored | Autosomal recessive |
| **Limb-Girdle MD (various)** | Multiple IDs | Various | Multiple | Mixed |

### 2.2 DMD/BMD Detailed Analysis

**Duchenne MD (MONDO:0010679):**
- **Description:** "Rapidly progressive muscle weakness and wasting due to degeneration of skeletal, smooth and cardiac muscle"
- **Key Phenotypes:**
  - HP:0008981: Calf muscle hypertrophy
  - HP:0003391: Gowers sign
  - HP:0003236: Elevated circulating creatine kinase concentration
  - HP:0001644: Dilated cardiomyopathy
  - HP:0100543: Cognitive impairment
  - HP:0002194: Delayed gross motor development

**Becker MD (MONDO:0010311):**
- **Description:** "Progressive muscle wasting and weakness" (milder than DMD)
- **Key Phenotypes:**
  - HP:0003707: Calf muscle pseudohypertrophy
  - HP:0003236: Elevated circulating creatine kinase concentration
  - HP:0001638: Cardiomyopathy
  - HP:0003546: Exercise intolerance
  - HP:0012378: Fatigue

**Phenotype Overlap:** DMD and BMD share **16 common phenotypes**, including:
- Abnormal EKG, Arrhythmia, Cardiomyopathy
- Calf muscle pseudohypertrophy
- Difficulty climbing stairs
- Elevated CK, Hyporeflexia, Muscle weakness

**Unique to DMD (distinguishing features):**
- Cognitive impairment
- Delayed speech and language development
- Achilles tendon contracture
- Congestive heart failure
- Dilated cardiomyopathy

### 2.3 Gene Data

**DMD Gene (HGNC:2928):**
- Full name: "dystrophin"
- Associated with 8 diseases (including DMD, BMD, dilated cardiomyopathy, intellectual disability)
- Relationships: `biolink:causes` and `biolink:gene_associated_with_condition`

**LAMA2 Gene (HGNC:6482):**
- Full name: "laminin subunit alpha 2"
- Associated with merosin-deficient CMD and LGMD type 23

**Note:** Variant data (`biolink:SequenceVariant`) nodes exist in schema but are **not populated** in current database dump. Exon-level deletion/duplication data is NOT available.

---

## 3. Schema Comparison: Custom vs. Biolink

| Feature | Custom Schema (schema.py) | Monarch Biolink Schema |
|---------|---------------------------|------------------------|
| **Node Labels** | Disease, Gene, Phenotype, Variant, Treatment | biolink:Disease, biolink:Gene, biolink:PhenotypicFeature |
| **Relationships** | HAS_PHENOTYPE, CAUSED_BY_MUTATION_IN | biolink:has_phenotype, biolink:causes |
| **Data Population** | 0 nodes (empty) | 1.3M+ nodes (fully populated) |
| **Phenotype IDs** | HPO IDs (e.g., HP:0003391) | Same HPO IDs with biolink wrapper |
| **Variant Support** | Planned (exon-specific) | Schema exists, unpopulated |
| **Treatment Data** | Custom recommendations | Not present in Monarch |

**Key Insight:** The project's custom schema is **structurally similar** to Biolink but uses **simplified labels**. Monarch data can be accessed with minor query adjustments.

---

## 4. Integration Strategy

### 4.1 Recommended Approach: Hybrid Architecture

**Option 1: Two-Database Strategy (RECOMMENDED)**
- **Monarch Database:** Disease profiles, gene-disease associations, phenotype ontology
- **Custom Database:** Treatment recommendations, exon-specific variants, clinical pathways
- **Integration Layer:** `KnowledgeGraphService` queries both databases

**Option 2: Schema Adapter Pattern**
- Create `MonarchService` class (already exists in codebase)
- Map Biolink queries to custom schema expectations
- Transparent to `ScenarioProcessor`

**Option 3: Data Import + Merge**
- Import Monarch disease-phenotype data into custom schema
- Requires ETL pipeline and ongoing sync
- **Not recommended** due to maintenance overhead

### 4.2 Proposed Architecture

```
┌─────────────────────────┐
│  ScenarioProcessor      │
│  (scenario_processor.py)│
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────────────────────────────┐
│  KnowledgeGraphService (service.py)             │
│  - Orchestrates queries across data sources     │
└───────────┬─────────────────────┬───────────────┘
            │                     │
            ▼                     ▼
┌───────────────────────┐ ┌──────────────────────┐
│  MonarchService       │ │  CustomService       │
│  (monarch_service.py) │ │  (In-memory/Neo4j)   │
│                       │ │                      │
│  - Disease profiles   │ │  - Treatment recs    │
│  - Phenotype data     │ │  - Variant annot.    │
│  - Gene associations  │ │  - Exon-specific     │
└───────────────────────┘ └──────────────────────┘
```

### 4.3 Implementation Roadmap

**Phase 1: Monarch Read-Only Integration (Week 1-2)**
1. ✅ Explore database schema and content (COMPLETED)
2. Update `MonarchService` to query disease-phenotype associations
3. Implement phenotype-based disease ranking using Monarch data
4. Test with existing demo scenarios

**Phase 2: Enhanced Differential Diagnosis (Week 3-4)**
1. Replace in-memory disease profiles with Monarch queries
2. Implement phenotype overlap scoring algorithm
3. Add mode of inheritance filtering
4. Validate against clinical test cases

**Phase 3: Hybrid Data Model (Week 5-6)**
1. Keep custom schema for variant annotations (exon deletions)
2. Keep custom schema for treatment recommendations
3. Use Monarch for disease-phenotype-gene data
4. Implement caching layer for performance

**Phase 4: Advanced Features (Future)**
1. Add gene-to-phenotype queries for variant interpretation
2. Implement disease similarity based on phenotype networks
3. Add anatomical location and biological process data
4. Integrate additional Monarch relationship types

---

## 5. Code Examples

### 5.1 Query: Find Diseases by Phenotype Overlap

```python
def search_diseases_by_phenotypes(self, hpo_ids: List[str], limit: int = 10) -> List[Dict]:
    """
    Find diseases matching a set of HPO phenotype IDs.
    Uses Monarch biolink schema.
    """
    query = """
    MATCH (d:`biolink:Disease`)-[:`biolink:has_phenotype`]->(p:`biolink:PhenotypicFeature`)
    WHERE p.id IN $hpo_ids
    WITH d, count(DISTINCT p) as match_count, collect(DISTINCT p.id) as matched_phenotypes
    RETURN d.id as disease_id,
           d.name as disease_name,
           d.description as description,
           match_count,
           matched_phenotypes
    ORDER BY match_count DESC
    LIMIT $limit
    """

    with self.driver.session(database=self.database) as session:
        result = session.run(query, {"hpo_ids": hpo_ids, "limit": limit})
        return [dict(record) for record in result]
```

**Example Usage:**
```python
# Patient with: proximal weakness, elevated CK, calf hypertrophy, Gowers sign
hpo_ids = ["HP:0003236", "HP:0008981", "HP:0003391", "HP:0003551"]
diseases = monarch_service.search_diseases_by_phenotypes(hpo_ids)

# Expected results:
# 1. MONDO:0010679 (Duchenne MD) - match_count: 4
# 2. MONDO:0010311 (Becker MD) - match_count: 3
# 3. Other muscular dystrophies - match_count: 2-3
```

### 5.2 Query: Get Disease Profile with Phenotypes

```python
def get_disease_profile(self, disease_id: str) -> Dict:
    """
    Get comprehensive disease information from Monarch.
    """
    query = """
    MATCH (d:`biolink:Disease`)
    WHERE d.id = $disease_id

    OPTIONAL MATCH (d)-[:`biolink:has_phenotype`]->(p:`biolink:PhenotypicFeature`)
    OPTIONAL MATCH (d)-[:`biolink:has_mode_of_inheritance`]->(i:`biolink:PhenotypicFeature`)
    OPTIONAL MATCH (g:`biolink:Gene`)-[r]-(d)
    WHERE type(r) IN ['biolink:causes', 'biolink:gene_associated_with_condition']

    RETURN d.id as id,
           d.name as name,
           d.description as description,
           collect(DISTINCT {id: p.id, name: p.name}) as phenotypes,
           collect(DISTINCT {id: i.id, name: i.name}) as inheritance,
           collect(DISTINCT {gene_id: g.id, symbol: g.symbol, relationship: type(r)}) as genes
    """

    with self.driver.session(database=self.database) as session:
        result = session.run(query, {"disease_id": disease_id})
        record = result.single()
        return dict(record) if record else None
```

### 5.3 Query: Get Phenotype Specificity Scores

```python
def get_phenotype_specificity(self, hpo_ids: List[str]) -> Dict[str, float]:
    """
    Calculate inverse document frequency (IDF) scores for phenotypes.
    Rare phenotypes (fewer disease associations) get higher scores.
    """
    query = """
    UNWIND $hpo_ids as hpo_id
    MATCH (p:`biolink:PhenotypicFeature` {id: hpo_id})
    OPTIONAL MATCH (p)<-[:`biolink:has_phenotype`]-(d:`biolink:Disease`)
    WITH p.id as phenotype_id, count(DISTINCT d) as disease_count

    // Calculate specificity: 1.0 / log(disease_count + 1)
    RETURN phenotype_id,
           disease_count,
           1.0 / (log(toFloat(disease_count + 1)) + 1.0) as specificity_score
    """

    with self.driver.session(database=self.database) as session:
        result = session.run(query, {"hpo_ids": hpo_ids})
        return {r['phenotype_id']: r['specificity_score'] for r in result}
```

---

## 6. Integration Points in Existing Code

### 6.1 `ScenarioProcessor._generate_differential_diagnosis()`

**Current Implementation:**
```python
def _generate_differential_diagnosis(self, scenario: ClinicalScenario) -> List[DifferentialDiagnosis]:
    # Uses in-memory disease profiles from seed_data.py
    disease_profiles = self.kg_service.get_disease_profiles()
    # Manual scoring based on feature matching
```

**Enhanced with Monarch:**
```python
def _generate_differential_diagnosis(self, scenario: ClinicalScenario) -> List[DifferentialDiagnosis]:
    # Extract HPO IDs from patient symptoms
    hpo_ids = self._extract_hpo_terms(scenario)

    # Query Monarch for diseases matching these phenotypes
    diseases = self.kg_service.search_diseases_by_phenotypes(hpo_ids, limit=20)

    # Score diseases using:
    # - Phenotype overlap (from Monarch)
    # - Phenotype specificity (rare symptoms weighted higher)
    # - Age appropriateness (custom logic)
    # - Inheritance pattern (from Monarch)
    # - Lab values (custom logic)

    scored_diseases = []
    for disease in diseases:
        score = self._calculate_disease_score(disease, scenario, hpo_ids)
        scored_diseases.append((disease, score))

    # Convert to DifferentialDiagnosis objects
    return self._create_differential_list(scored_diseases)
```

### 6.2 `KnowledgeGraphService` Updates

**Add Monarch-Specific Methods:**
```python
class KnowledgeGraphService:
    def __init__(self):
        self.monarch_service = MonarchService()  # Connect to Monarch DB
        self.custom_service = CustomService()    # In-memory or custom Neo4j

    def search_diseases_by_phenotypes(self, hpo_ids: List[str]) -> List[Dict]:
        """Use Monarch for phenotype-based disease search."""
        return self.monarch_service.search_diseases_by_phenotypes(hpo_ids)

    def get_disease_profile(self, disease_id: str) -> Dict:
        """Get disease info from Monarch."""
        monarch_data = self.monarch_service.get_disease_profile(disease_id)

        # Optionally merge with custom data (treatments, etc.)
        custom_data = self.custom_service.get_treatment_recommendations(disease_id)

        return {**monarch_data, 'treatments': custom_data}

    def get_variant_annotations(self, gene: str, variant: str) -> Dict:
        """Use custom service for exon-specific variant data."""
        return self.custom_service.get_variant_annotations(gene, variant)
```

---

## 7. Advantages of Monarch Integration

### 7.1 Data Quality
- ✅ **Evidence-based:** Curated from primary sources (OMIM, Orphanet, HPO)
- ✅ **Comprehensive:** 255,967 disease-phenotype associations vs. ~50 in seed_data.py
- ✅ **Standardized:** Biolink Model ensures interoperability
- ✅ **Maintained:** Monarch team updates regularly

### 7.2 Clinical Decision Support
- ✅ **Broader differential:** Access to 14,000+ diseases beyond muscular dystrophies
- ✅ **Phenotype specificity:** Can weight rare symptoms higher than common ones
- ✅ **Inheritance filtering:** X-linked, autosomal recessive, etc.
- ✅ **Gene-disease validation:** Confirm variant pathogenicity via gene associations

### 7.3 Scalability
- ✅ **No manual curation:** Eliminate need to maintain seed_data.py disease profiles
- ✅ **Easy expansion:** Add new diseases by querying Monarch, not coding
- ✅ **Version control:** Database dumps are versioned and downloadable

---

## 8. Limitations and Mitigations

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| **No variant data** | Can't map exon deletions to treatments | Keep custom variant annotations in seed_data.py |
| **No treatment recommendations** | Monarch focuses on disease/phenotype, not clinical management | Maintain custom treatment recommendation database |
| **Schema differences** | Biolink vs. custom labels | Use MonarchService adapter layer |
| **Performance** | Monarch DB is large (1.3M nodes) | Implement caching, index HPO IDs, limit query scope |
| **Sparse data for rare diseases** | Some diseases have few phenotypes | Combine Monarch data with literature-based custom annotations |

---

## 9. Testing Strategy

### 9.1 Validation Test Cases

**Test 1: DMD Diagnosis from Phenotypes**
```python
# Input: Young male, proximal weakness, elevated CK, calf hypertrophy, Gowers sign
hpo_ids = ["HP:0003236", "HP:0008981", "HP:0003391"]
diseases = monarch_service.search_diseases_by_phenotypes(hpo_ids)

# Expected: MONDO:0010679 (DMD) in top 3 results
assert any(d['disease_id'] == 'MONDO:0010679' for d in diseases[:3])
```

**Test 2: DMD vs. BMD Discrimination**
```python
# DMD-specific phenotypes
dmd_hpo = ["HP:0100543", "HP:0002194", "HP:0001644"]  # Cognitive impairment, delayed development, dilated CM
dmd_diseases = monarch_service.search_diseases_by_phenotypes(dmd_hpo)

# BMD-specific phenotypes
bmd_hpo = ["HP:0003546", "HP:0012378"]  # Exercise intolerance, fatigue
bmd_diseases = monarch_service.search_diseases_by_phenotypes(bmd_hpo)

# Expected: DMD ranks higher for DMD phenotypes, BMD for BMD phenotypes
```

**Test 3: LAMA2-CMD Infant Presentation**
```python
# Infant with hypotonia, muscle weakness
hpo_ids = ["HP:0001252", "HP:0001324"]  # Hypotonia, muscle weakness
diseases = monarch_service.search_diseases_by_phenotypes(hpo_ids)

# Expected: MONDO:0011925 (LAMA2-CMD) in results
assert any('LAMA2' in d['disease_name'] for d in diseases)
```

### 9.2 Integration Tests

1. **Query Performance:** Measure response time for phenotype searches (<500ms target)
2. **Data Accuracy:** Validate Monarch phenotype counts against HPO database
3. **Scoring Validation:** Compare Monarch-based differential vs. expert clinical diagnosis
4. **Fallback Behavior:** Ensure system works if Monarch connection fails

---

## 10. Next Steps

### Immediate Actions (This Week)
1. ✅ Complete database exploration (DONE)
2. ✅ Document integration strategy (DONE)
3. ⏳ Create `MonarchService` class with core query methods
4. ⏳ Test phenotype-based disease search with demo scenarios

### Short-Term (Next 2 Weeks)
1. Integrate Monarch queries into `ScenarioProcessor`
2. Implement phenotype specificity scoring
3. Add caching layer for performance
4. Validate with clinical test cases

### Long-Term (Next Month)
1. Deploy hybrid architecture (Monarch + custom DB)
2. Benchmark against current in-memory system
3. Expand to additional disease categories
4. Publish integration results

---

## 11. Resources

### Database Access
- **Connection:** neo4j://127.0.0.1:7687
- **Database:** monarch
- **Credentials:** See `.env` file
- **Exploration Scripts:** `explore_monarch_database.py`, `explore_md_specific.py`

### Documentation
- **Monarch Initiative:** https://monarchinitiative.org/
- **Biolink Model:** https://biolink.github.io/biolink-model/
- **HPO Browser:** https://hpo.jax.org/
- **Monarch KG Docs:** https://monarch-initiative.github.io/monarch-ingest/

### Code Files
- `backend/knowledge_graph/monarch_service.py` - Monarch query layer (to be created)
- `backend/knowledge_graph/service.py` - Main KG service orchestrator
- `backend/core/scenario_processor.py` - Differential diagnosis logic
- `backend/knowledge_graph/seed_data.py` - Custom annotations (variants, treatments)

---

## 12. Conclusion

The Monarch Initiative database provides a **production-grade knowledge graph** with comprehensive disease-phenotype-gene associations that far exceed the current in-memory seed data. By integrating Monarch via a hybrid architecture:

1. **Leverage** 255,967 curated disease-phenotype associations for differential diagnosis
2. **Maintain** custom variant annotations and treatment recommendations
3. **Scale** to broader disease coverage without manual curation
4. **Validate** gene-disease associations for variant interpretation

**Recommendation:** Proceed with **Phase 1 implementation** (MonarchService read-only integration) while preserving custom variant and treatment data in the existing seed_data.py structure.

---

**Document Version:** 1.0
**Last Updated:** 2025-11-15
**Author:** Claude Code
**Status:** ✅ Ready for Implementation
