"""Knowledge graph service for muscular dystrophy clinical decision support.

The graph service abstracts the underlying storage so the ScenarioProcessor can
retrieve disease knowledge from Neo4j when available and fall back to an
in-memory store (seeded from curated data) otherwise.
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from typing import Dict, List, Optional

import hashlib

from neo4j import GraphDatabase, basic_auth

from . import seed_data
from .schema import CONSTRAINT_STATEMENTS, INDEX_STATEMENTS

logger = logging.getLogger(__name__)


@dataclass
class KnowledgeGraphConfig:
    uri: str
    user: str
    password: str
    database: Optional[str] = None


class KnowledgeGraphService:
    """High-level interface for domain knowledge stored in Neo4j."""

    def __init__(self, config: Optional[KnowledgeGraphConfig] = None):
        self._config = config or self._load_config_from_env()
        self._driver = None
        self._in_memory_store = None

        if self._config:
            try:
                self._driver = GraphDatabase.driver(
                    self._config.uri,
                    auth=basic_auth(self._config.user, self._config.password),
                )
                logger.info("Connected to Neo4j at %s", self._config.uri)
            except Exception as exc:  # pylint: disable=broad-except
                logger.warning("Failed to initialize Neo4j driver: %s", exc)
                self._driver = None

        if self._driver is None:
            logger.info("Falling back to in-memory knowledge store")
            self._in_memory_store = InMemoryKnowledgeStore()
            self._in_memory_store.seed()

    # ------------------------------------------------------------------
    # Public API

    def ensure_schema(self) -> None:
        if not self._driver:
            return

        def run_statements(tx, statements):
            for stmt in statements:
                tx.run(stmt)

        with self._driver.session(database=self._config.database) as session:
            session.execute_write(run_statements, CONSTRAINT_STATEMENTS)
            session.execute_write(run_statements, INDEX_STATEMENTS)

    def seed(self) -> None:
        if self._in_memory_store:
            self._in_memory_store.seed()
            return

        if not self._driver:
            return

        logger.info("Seeding Neo4j knowledge graph")
        with self._driver.session(database=self._config.database) as session:
            session.execute_write(self._seed_graph)

    def close(self) -> None:
        if self._driver:
            self._driver.close()

    # Query methods ----------------------------------------------------
    def get_disease_profiles(self) -> Dict[str, Dict]:
        if self._in_memory_store:
            return self._in_memory_store.get_disease_profiles()

        query = """
        MATCH (d:Disease)
        OPTIONAL MATCH (d)-[hp:HAS_PHENOTYPE]->(p:Phenotype)
        OPTIONAL MATCH (d)-[rt:RECOMMENDED_TEST]->(test:DiagnosticTest)
        RETURN d.code AS code,
               d.name AS name,
               d.inheritance AS inheritance,
               d.key_features AS key_features,
               d.onset_min AS onset_min,
               d.onset_max AS onset_max,
               collect(DISTINCT {
                   feature_key: p.feature_key,
                   hpo_id: p.hpo_id,
                   term: p.term,
                   specificity: hp.specificity
               }) AS phenotypes,
               collect(DISTINCT {
                   name: test.name,
                   frequency: rt.frequency
               }) AS tests
        """
        with self._driver.session(database=self._config.database) as session:
            records = session.run(query)
            profiles = {}
            for record in records:
                phenotypes = [
                    p for p in record["phenotypes"] if p["feature_key"]
                ]
                tests = [t["name"] for t in record["tests"] if t["name"]]
                profiles[record["code"]] = {
                    "code": record["code"],
                    "name": record["name"],
                    "inheritance": record["inheritance"],
                    "key_features": record.get("key_features") or [],
                    "typical_onset": [record["onset_min"], record["onset_max"]],
                    "phenotypes": phenotypes,
                    "diagnostic_tests": tests,
                }
            return profiles

    def get_treatment_recommendations(self, disease_code: str) -> List[Dict]:
        if self._in_memory_store:
            return self._in_memory_store.get_treatment_recommendations(disease_code)

        query = """
        MATCH (d:Disease {code: $code})-[:HAS_RECOMMENDATION]->(rec:Recommendation)
        OPTIONAL MATCH (rec)-[:SUGGESTS]->(t:Treatment)
        RETURN rec.category AS category,
               rec.recommendation AS recommendation,
               rec.evidence_level AS evidence_level,
               rec.urgency AS urgency,
               rec.references AS references,
               collect(DISTINCT t.name) AS treatments
        """
        with self._driver.session(database=self._config.database) as session:
            result = session.run(query, code=disease_code)
            recommendations = []
            for record in result:
                entry = {
                    "category": record["category"],
                    "recommendation": record["recommendation"],
                    "evidence_level": record["evidence_level"],
                    "urgency": record["urgency"],
                    "references": record["references"] or [],
                    "treatments": [t for t in record["treatments"] if t],
                }
                recommendations.append(entry)
            return recommendations

    def get_general_recommendations(self) -> List[Dict]:
        if self._in_memory_store:
            return self._in_memory_store.get_general_recommendations()

        query = """
        MATCH (rec:GeneralRecommendation)
        RETURN rec.category AS category,
               rec.recommendation AS recommendation,
               rec.evidence_level AS evidence_level,
               rec.urgency AS urgency,
               rec.references AS references
        """
        with self._driver.session(database=self._config.database) as session:
            result = session.run(query)
            return [
                {
                    "category": record["category"],
                    "recommendation": record["recommendation"],
                    "evidence_level": record["evidence_level"],
                    "urgency": record["urgency"],
                    "references": record["references"] or [],
                }
                for record in result
            ]

    def get_pathway_steps(self, pathway_code: str) -> List[str]:
        if self._in_memory_store:
            return self._in_memory_store.get_pathway_steps(pathway_code)

        query = """
        MATCH (p:DiagnosticPathway {code: $code})
        RETURN p.steps AS steps
        """
        with self._driver.session(database=self._config.database) as session:
            record = session.run(query, code=pathway_code).single()
            return record["steps"] if record else []

    def get_variant_annotations(self, gene: str, variant_type: str) -> List[Dict]:
        if self._in_memory_store:
            return self._in_memory_store.get_variant_annotations(gene, variant_type)

        query = """
        MATCH (v:Variant {gene: $gene, variant_type: $variant_type})
        OPTIONAL MATCH (v)-[:ELIGIBLE_FOR]->(t:Treatment)
        RETURN v.uid AS uid,
               v.exons AS exons,
               v.reading_frame AS reading_frame,
               v.predicted_phenotype AS predicted_phenotype,
               v.severity AS severity,
               collect(DISTINCT t.name) AS treatments
        """
        with self._driver.session(database=self._config.database) as session:
            result = session.run(query, gene=gene, variant_type=variant_type)
            annotations = []
            for record in result:
                entry = {
                    "uid": record["uid"],
                    "exons": record["exons"],
                    "reading_frame": record["reading_frame"],
                    "predicted_phenotype": record["predicted_phenotype"],
                    "severity": record["severity"],
                    "eligible_treatments": [t for t in record["treatments"] if t],
                }
                annotations.append(entry)
            return annotations

    # Internal helpers -------------------------------------------------
    def _seed_graph(self, tx) -> None:
        self._create_nodes(tx)
        self._create_relationships(tx)

    def _clear_database(self, tx) -> None:
        tx.run("MATCH (n) DETACH DELETE n")

    def _create_nodes(self, tx) -> None:
        # Diseases
        for disease in seed_data.DISEASES:
            tx.run(
                """
                MERGE (d:Disease {code: $code})
                SET d.name = $name,
                    d.inheritance = $inheritance,
                    d.key_features = $key_features,
                    d.severity = $severity,
                    d.onset_min = $onset_min,
                    d.onset_max = $onset_max
                """,
                code=disease["code"],
                name=disease["name"],
                inheritance=disease["inheritance"],
                key_features=disease["key_features"],
                severity=disease["severity"],
                onset_min=disease["typical_onset"]["min"],
                onset_max=disease["typical_onset"]["max"],
            )
            for gene in disease["genes"]:
                tx.run(
                    """
                    MERGE (g:Gene {symbol: $symbol})
                    """,
                    symbol=gene,
                )
            for phenotype in disease["phenotypes"]:
                tx.run(
                    """
                    MERGE (p:Phenotype {hpo_id: $hpo_id})
                    SET p.term = $term,
                        p.feature_key = $feature_key
                    """,
                    hpo_id=phenotype["hpo_id"],
                    term=phenotype["term"],
                    feature_key=phenotype["feature_key"],
                )
            for test in disease["diagnostic_tests"]:
                tx.run(
                    """
                    MERGE (t:DiagnosticTest {name: $name})
                    SET t.test_type = $test_type,
                        t.frequency = $frequency
                    """,
                    name=test["name"],
                    test_type=test.get("type"),
                    frequency=test.get("frequency"),
                )
            for pathway_code in disease.get("pathways", []):
                pathway = next(
                    (p for p in seed_data.DIAGNOSTIC_PATHWAYS if p["code"] == pathway_code),
                    None,
                )
                if pathway:
                    tx.run(
                        """
                        MERGE (dp:DiagnosticPathway {code: $code})
                        SET dp.name = $name,
                            dp.steps = $steps
                        """,
                        code=pathway["code"],
                        name=pathway["name"],
                        steps=pathway["steps"],
                    )

        # Treatments and recommendations
        for rec in seed_data.TREATMENT_RECOMMENDATIONS:
            rec_id = self._recommendation_id(rec)
            tx.run(
                """
                MERGE (r:Recommendation {id: $id})
                SET r.category = $category,
                    r.recommendation = $recommendation,
                    r.evidence_level = $evidence_level,
                    r.urgency = $urgency,
                    r.references = $references
                """,
                id=rec_id,
                category=rec["category"],
                recommendation=rec["recommendation"],
                evidence_level=rec.get("evidence_level"),
                urgency=rec.get("urgency"),
                references=rec.get("references"),
            )
            for treatment_name in rec.get("treatments", []):
                tx.run(
                    "MERGE (t:Treatment {name: $name})",
                    name=treatment_name,
                )

        # General recommendations
        for rec in seed_data.GENERAL_RECOMMENDATIONS:
            rec_id = self._recommendation_id(rec, prefix="general")
            tx.run(
                """
                MERGE (gr:GeneralRecommendation {id: $id})
                SET gr.category = $category,
                    gr.recommendation = $recommendation,
                    gr.evidence_level = $evidence_level,
                    gr.urgency = $urgency,
                    gr.references = $references
                """,
                id=rec_id,
                category=rec["category"],
                recommendation=rec["recommendation"],
                evidence_level=rec.get("evidence_level"),
                urgency=rec.get("urgency"),
                references=rec.get("references"),
            )

        # Variants
        for variant in seed_data.VARIANT_ANNOTATIONS:
            uid = self._variant_uid(variant)
            tx.run(
                """
                MERGE (v:Variant {uid: $uid})
                SET v.gene = $gene,
                    v.variant_type = $variant_type,
                    v.exons = $exons,
                    v.reading_frame = $reading_frame,
                    v.predicted_phenotype = $predicted_phenotype,
                    v.severity = $severity
                """,
                uid=uid,
                gene=variant["gene"],
                variant_type=variant["variant_type"],
                exons=variant["exons"],
                reading_frame=variant["reading_frame"],
                predicted_phenotype=variant["predicted_phenotype"],
                severity=variant["severity"],
            )
            for treatment_name in variant.get("eligible_treatments", []):
                tx.run(
                    "MERGE (t:Treatment {name: $name})",
                    name=treatment_name,
                )

        # Data sources
        for src in seed_data.data_sources:
            tx.run(
                """
                MERGE (ds:DataSource {name: $name})
                SET ds.description = $description,
                    ds.url = $url,
                    ds.license = $license
                """,
                name=src["name"],
                description=src.get("description"),
                url=src.get("url"),
                license=src.get("license"),
            )

    def _create_relationships(self, tx) -> None:
        for disease in seed_data.DISEASES:
            # Gene associations
            for gene in disease["genes"]:
                tx.run(
                    """
                    MATCH (d:Disease {code: $code}), (g:Gene {symbol: $symbol})
                    MERGE (d)-[:CAUSED_BY_MUTATION_IN]->(g)
                    """,
                    code=disease["code"],
                    symbol=gene,
                )

            # Phenotype links
            for phenotype in disease["phenotypes"]:
                tx.run(
                    """
                    MATCH (d:Disease {code: $code}), (p:Phenotype {hpo_id: $hpo_id})
                    MERGE (d)-[r:HAS_PHENOTYPE]->(p)
                    SET r.specificity = $specificity
                    """,
                    code=disease["code"],
                    hpo_id=phenotype["hpo_id"],
                    specificity=phenotype.get("specificity"),
                )

            # Diagnostic tests
            for test in disease["diagnostic_tests"]:
                tx.run(
                    """
                    MATCH (d:Disease {code: $code}), (t:DiagnosticTest {name: $name})
                    MERGE (d)-[r:RECOMMENDED_TEST]->(t)
                    SET r.frequency = $frequency
                    """,
                    code=disease["code"],
                    name=test["name"],
                    frequency=test.get("frequency"),
                )

            # Pathways
            for pathway_code in disease.get("pathways", []):
                tx.run(
                    """
                    MATCH (d:Disease {code: $code}), (p:DiagnosticPathway {code: $pathway})
                    MERGE (d)-[:USES_PATHWAY]->(p)
                    """,
                    code=disease["code"],
                    pathway=pathway_code,
                )

            # Recommendations
            for rec in seed_data.TREATMENT_RECOMMENDATIONS:
                if rec["disease_code"] != disease["code"]:
                    continue
                rec_id = self._recommendation_id(rec)
                tx.run(
                    """
                    MATCH (d:Disease {code: $code}), (r:Recommendation {id: $id})
                    MERGE (d)-[:HAS_RECOMMENDATION]->(r)
                    """,
                    code=disease["code"],
                    id=rec_id,
                )
                for treatment_name in rec.get("treatments", []):
                    tx.run(
                        """
                        MATCH (r:Recommendation {id: $id}), (t:Treatment {name: $name})
                        MERGE (r)-[:SUGGESTS]->(t)
                        """,
                        id=rec_id,
                        name=treatment_name,
                    )

            # General recommendations apply to diseases lacking specifics
            for rec in seed_data.GENERAL_RECOMMENDATIONS:
                rec_id = self._recommendation_id(rec, prefix="general")
                tx.run(
                    """
                    MATCH (d:Disease {code: $code}), (gr:GeneralRecommendation {id: $id})
                    MERGE (gr)-[:APPLIES_TO]->(d)
                    """,
                    code=disease["code"],
                    id=rec_id,
                )

        # Variant relationships
        for variant in seed_data.VARIANT_ANNOTATIONS:
            uid = self._variant_uid(variant)
            disease_code = "DMD" if "Duchenne" in variant["predicted_phenotype"] else "BMD"
            tx.run(
                """
                MATCH (v:Variant {uid: $uid}), (d:Disease {code: $code})
                MERGE (v)-[:PREDICTS_PHENOTYPE]->(d)
                """,
                uid=uid,
                code=disease_code,
            )
            for treatment_name in variant.get("eligible_treatments", []):
                tx.run(
                    """
                    MATCH (v:Variant {uid: $uid}), (t:Treatment {name: $name})
                    MERGE (v)-[:ELIGIBLE_FOR]->(t)
                    """,
                    uid=uid,
                    name=treatment_name,
                )

        # Data sources referencing diseases and treatments (simplified)
        for src in seed_data.data_sources:
            for disease in seed_data.DISEASES:
                tx.run(
                    """
                    MATCH (ds:DataSource {name: $source}), (d:Disease {code: $code})
                    MERGE (ds)-[:CURATES]->(d)
                    """,
                    source=src["name"],
                    code=disease["code"],
                )
            for rec in seed_data.TREATMENT_RECOMMENDATIONS:
                rec_id = self._recommendation_id(rec)
                for treatment_name in rec.get("treatments", []):
                    tx.run(
                        """
                        MATCH (ds:DataSource {name: $source}), (t:Treatment {name: $name})
                        MERGE (ds)-[:DOCUMENTS]->(t)
                        """,
                        source=src["name"],
                        name=treatment_name,
                    )

    @staticmethod
    def _load_config_from_env() -> Optional[KnowledgeGraphConfig]:
        uri = os.getenv("NEO4J_URI")
        user = os.getenv("NEO4J_USER")
        password = os.getenv("NEO4J_PASSWORD")
        database = os.getenv("NEO4J_DATABASE")

        if uri and user and password:
            return KnowledgeGraphConfig(uri=uri, user=user, password=password, database=database)
        return None

    @staticmethod
    def _recommendation_id(rec: Dict, prefix: str = "disease") -> str:
        base = json.dumps(rec, sort_keys=True)
        digest = hashlib.md5(base.encode("utf-8"), usedforsecurity=False).hexdigest()
        return f"{prefix}:{digest}"

    @staticmethod
    def _variant_uid(variant: Dict) -> str:
        exons = "-".join(str(e) for e in variant.get("exons", [])) or "na"
        return f"{variant['gene']}|{variant['variant_type']}|{exons}"


class InMemoryKnowledgeStore:
    """Simplified in-memory store for development and tests."""

    def __init__(self):
        self._diseases: Dict[str, Dict] = {}
        self._recommendations: Dict[str, List[Dict]] = {}
        self._general_recs: List[Dict] = []
        self._pathways: Dict[str, List[str]] = {}
        self._variants: Dict[str, List[Dict]] = {}

    def seed(self) -> None:
        self._diseases = {
            disease["code"]: {
                "code": disease["code"],
                "name": disease["name"],
                "inheritance": disease["inheritance"],
                "typical_onset": [disease["typical_onset"]["min"], disease["typical_onset"]["max"]],
                "key_features": disease["key_features"],
                "diagnostic_tests": [test["name"] for test in disease["diagnostic_tests"]],
                "pathways": disease.get("pathways", []),
                "phenotypes": disease["phenotypes"],
            }
            for disease in seed_data.DISEASES
        }

        self._recommendations = {}
        for rec in seed_data.TREATMENT_RECOMMENDATIONS:
            self._recommendations.setdefault(rec["disease_code"], []).append(rec)

        self._general_recs = seed_data.GENERAL_RECOMMENDATIONS

        self._pathways = {
            pathway["code"]: pathway["steps"]
            for pathway in seed_data.DIAGNOSTIC_PATHWAYS
        }

        self._variants = {}
        for variant in seed_data.VARIANT_ANNOTATIONS:
            key = (variant["gene"], variant["variant_type"])
            self._variants.setdefault(key, []).append(variant)

    def get_disease_profiles(self) -> Dict[str, Dict]:
        return {
            code: {
                **data,
                "inheritance": data["inheritance"],
                "typical_onset": data["typical_onset"],
                "diagnostic_tests": data["diagnostic_tests"],
                "key_features": data["key_features"],
            }
            for code, data in self._diseases.items()
        }

    def get_treatment_recommendations(self, disease_code: str) -> List[Dict]:
        return self._recommendations.get(disease_code, [])

    def get_general_recommendations(self) -> List[Dict]:
        return self._general_recs

    def get_pathway_steps(self, pathway_code: str) -> List[str]:
        return self._pathways.get(pathway_code, [])

    def get_variant_annotations(self, gene: str, variant_type: str) -> List[Dict]:
        return self._variants.get((gene, variant_type), [])
