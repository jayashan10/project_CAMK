# Archived Files

This folder contains files that have been replaced or deprecated during the migration to use the Monarch Initiative knowledge graph.

## seed_data.py.archived

**Date Archived:** 2025-11-15

**Reason for Archiving:**
This file contained hardcoded disease/gene/phenotype data that has been replaced with real data from the Monarch Initiative Neo4j database (1.3M+ nodes, 14.7M+ relationships).

**What Was Preserved:**
The following data from seed_data.py was extracted and moved to `backend/knowledge_graph/clinical_data.py`:
- `TREATMENT_RECOMMENDATIONS` - Evidence-based treatment and surveillance recommendations
- `VARIANT_ANNOTATIONS` - DMD exon deletion annotations with reading frame rules and therapy eligibility
- `DIAGNOSTIC_PATHWAYS` - Clinical workflow steps
- `GENERAL_RECOMMENDATIONS` - Fallback recommendations for uncertain diagnoses

**What Was Replaced by Monarch:**
- `DISEASES` array - Replaced by Monarch disease profiles (MONDO IDs)
- Disease phenotype arrays - Replaced by Monarch's 255,967 disease-phenotype associations
- Gene associations - Replaced by Monarch's gene-disease associations

**Migration Details:**
See `MONARCH_INTEGRATION_STRATEGY.md` for full integration documentation.

**Can This Be Deleted?**
This file is kept for historical reference and rollback purposes. It can be safely deleted after confirming the migration works correctly in production.
