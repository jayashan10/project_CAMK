"""In-memory knowledge representation for muscular dystrophy decision support.

This module offers a consistent data access layer that the scenario processor
can consume without requiring a running Neo4j database. It mirrors the schema
captured in :mod:`backend.knowledge_graph.schema` and is intended for unit tests
and notebook demos.
"""
from __future__ import annotations

from typing import Dict, List

from . import seed_data


class InMemoryKnowledgeGraph:
    def __init__(self) -> None:
        self.diseases: Dict[str, Dict] = {}
        self.recommendations: Dict[str, List[Dict]] = {}
        self.diagnostic_pathways: Dict[str, List[str]] = {}
        self.variant_annotations: Dict[str, List[Dict]] = {}
        self.general_recommendations: List[Dict] = []

    def seed(self) -> None:
        self.diseases = {
            disease["code"]: {
                "code": disease["code"],
                "name": disease["name"],
                "inheritance": disease["inheritance"],
                "typical_onset": [disease["typical_onset"]["min"], disease["typical_onset"]["max"]],
                "key_features": disease["key_features"],
                "diagnostic_tests": [test["name"] for test in disease["diagnostic_tests"]],
                "phenotypes": disease["phenotypes"],
                "pathways": disease.get("pathways", []),
            }
            for disease in seed_data.DISEASES
        }

        self.recommendations = {}
        for rec in seed_data.TREATMENT_RECOMMENDATIONS:
            self.recommendations.setdefault(rec["disease_code"], []).append(rec)

        self.diagnostic_pathways = {
            pathway["code"]: pathway["steps"] for pathway in seed_data.DIAGNOSTIC_PATHWAYS
        }

        self.general_recommendations = seed_data.GENERAL_RECOMMENDATIONS

        self.variant_annotations = {}
        for annotation in seed_data.VARIANT_ANNOTATIONS:
            key = (annotation["gene"], annotation["variant_type"])
            self.variant_annotations.setdefault(key, []).append(annotation)

    def get_disease_profile(self, code: str) -> Dict:
        return self.diseases.get(code, {})

    def get_all_disease_profiles(self) -> Dict[str, Dict]:
        return self.diseases

    def get_recommendations(self, disease_code: str) -> List[Dict]:
        return self.recommendations.get(disease_code, [])

    def get_general_recommendations(self) -> List[Dict]:
        return self.general_recommendations

    def get_pathway(self, pathway_code: str) -> List[str]:
        return self.diagnostic_pathways.get(pathway_code, [])

    def get_variant_annotations(self, gene: str, variant_type: str) -> List[Dict]:
        return self.variant_annotations.get((gene, variant_type), [])
