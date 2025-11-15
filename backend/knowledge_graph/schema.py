"""Knowledge graph schema definition for muscular dystrophy decision support.

This module captures the Neo4j schema design, including node labels, relationship
patterns, and helper builders for constraints and indexes. The schema is shared by
both the Neo4j-backed implementation and the in-memory fallback so the data model
remains consistent across storage engines.
"""
from __future__ import annotations

from typing import Dict, List

# High-level schema description -------------------------------------------------

SCHEMA_DESCRIPTION: Dict[str, Dict] = {
    "nodes": {
        "Disease": {
            "key": "code",
            "properties": {
                "code": "Short identifier (e.g., 'DMD')",
                "name": "Canonical disease name",
                "inheritance": "Inheritance pattern",
                "severity": "Typical clinical severity",
                "onset_min": "Lower bound of typical onset age (years)",
                "onset_max": "Upper bound of typical onset age (years)",
            },
        },
        "Gene": {
            "key": "symbol",
            "properties": {"symbol": "HGNC gene symbol (e.g., 'DMD')"},
        },
        "Phenotype": {
            "key": "hpo_id",
            "properties": {
                "hpo_id": "HPO identifier",
                "term": "HPO preferred term",
                "feature_key": "Local feature identifier used by the processor",
            },
        },
        "DiagnosticTest": {
            "key": "name",
            "properties": {
                "name": "Test name",
                "test_type": "Category (genetic, imaging, cardiac, pathology)",
                "frequency": "Suggested cadence (baseline, annual, etc.)",
            },
        },
        "DiagnosticPathway": {
            "key": "code",
            "properties": {
                "code": "Short identifier",
                "name": "Human readable name",
                "steps": "Ordered list of pathway steps",
            },
        },
        "Recommendation": {
            "key": "id",
            "properties": {
                "id": "Deterministic identifier",
                "category": "diagnosis/treatment/surveillance/etc.",
                "recommendation": "Recommendation text",
                "evidence_level": "Evidence grade (Level A/B/C)",
                "urgency": "Clinical urgency",
                "references": "Supporting literature references",
            },
        },
        "Treatment": {
            "key": "name",
            "properties": {"name": "Therapeutic agent or modality"},
        },
        "Variant": {
            "key": "uid",
            "properties": {
                "uid": "Synthetic identifier (gene|type|exons)",
                "gene": "Gene symbol",
                "variant_type": "Variant class (deletion, duplication, etc.)",
                "exons": "List of exon numbers",
                "reading_frame": "Predicted reading frame status",
                "predicted_phenotype": "Disease phenotype predicted by the variant",
                "severity": "Expected clinical severity",
            },
        },
        "GeneralRecommendation": {
            "key": "id",
            "properties": {
                "id": "Deterministic identifier",
                "category": "Recommendation category",
                "recommendation": "Recommendation text",
                "evidence_level": "Optional evidence grade",
                "urgency": "Clinical urgency",
                "references": "Reference list",
            },
        },
        "DataSource": {
            "key": "name",
            "properties": {
                "name": "Dataset or guideline name",
                "description": "Short summary",
                "url": "Primary URL",
                "license": "Usage license",
            },
        },
    },
    "relationships": {
        "(:Disease)-[:HAS_PHENOTYPE {specificity}]->(:Phenotype)": "Links disease to HPO phenotypes with specificity score",
        "(:Disease)-[:CAUSED_BY_MUTATION_IN]->(:Gene)": "Captures gene-disease associations",
        "(:Disease)-[:RECOMMENDED_TEST {frequency}]->(:DiagnosticTest)": "Lists diagnostic tests with recommended frequency",
        "(:Disease)-[:USES_PATHWAY]->(:DiagnosticPathway)": "Associates diseases with diagnostic pathways",
        "(:Disease)-[:HAS_RECOMMENDATION]->(:Recommendation)": "Disease-specific management recommendations",
        "(:Recommendation)-[:SUGGESTS]->(:Treatment)": "Treatments suggested by a recommendation",
        "(:Variant)-[:PREDICTS_PHENOTYPE]->(:Disease)": "Variant-to-disease phenotype linkage",
        "(:Variant)-[:ELIGIBLE_FOR]->(:Treatment)": "Variant-specific treatment eligibility",
        "(:GeneralRecommendation)-[:APPLIES_TO]->(:Disease)": "General recommendations per disease (optional)",
        "(:GeneralRecommendation)-[:APPLIES_WHEN]->(:DiagnosticPathway)": "Fallback recommendations when diagnosis uncertain",
        "(:DataSource)-[:CURATES]->(:Disease)": "Source coverage for diseases",
        "(:DataSource)-[:DOCUMENTS]->(:Treatment)": "References for treatments",
    },
}


# Constraint and index helpers ---------------------------------------------------

def build_constraint_statements() -> List[str]:
    """Generate CREATE CONSTRAINT Cypher statements for primary keys."""
    statements: List[str] = []
    for label, spec in SCHEMA_DESCRIPTION["nodes"].items():
        key = spec.get("key")
        if key:
            statements.append(
                f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{label}) REQUIRE n.{key} IS UNIQUE"
            )
    return statements


def build_index_statements() -> List[str]:
    """Indexes on frequently queried properties."""
    return [
        "CREATE RANGE INDEX IF NOT EXISTS disease_name_index FOR (d:Disease) ON (d.name)",
        "CREATE RANGE INDEX IF NOT EXISTS phenotype_feature_index FOR (p:Phenotype) ON (p.feature_key)",
        "CREATE TEXT INDEX IF NOT EXISTS recommendation_text_index FOR (r:Recommendation) ON EACH [r.recommendation]",
    ]


CONSTRAINT_STATEMENTS = build_constraint_statements()
INDEX_STATEMENTS = build_index_statements()
