"""Knowledge graph service for muscular dystrophy clinical decision support.

The graph service abstracts the underlying storage so the ScenarioProcessor can
retrieve disease knowledge from Neo4j when available and fall back to an
in-memory store (seeded from curated data) otherwise.
"""
from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional

import hashlib

from dotenv import load_dotenv
from neo4j import GraphDatabase, basic_auth

from . import clinical_data
from .schema import CONSTRAINT_STATEMENTS, INDEX_STATEMENTS
from .monarch_service import MonarchService
from .monarch_mapper import DISEASE_CODE_MAP
from .clinvar_service import ClinVarService

# Import RAG service (with graceful handling if not available)
try:
    from backend.rag.gemini_file_search import GeminiFileSearchService
    GEMINI_RAG_AVAILABLE = True
except ImportError:
    GEMINI_RAG_AVAILABLE = False
    logger.warning("Gemini RAG module not available - RAG features will be disabled")

# Load environment variables from .env file
load_dotenv()

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
        self._monarch_service = None
        self._clinvar_service = None
        self._gemini_rag = None
        self._database_type = "unknown"

        if self._config:
            try:
                self._driver = GraphDatabase.driver(
                    self._config.uri,
                    auth=basic_auth(self._config.user, self._config.password),
                )
                logger.info("Connected to Neo4j at %s", self._config.uri)
                self._initialize_monarch_support()
            except Exception as exc:  # pylint: disable=broad-except
                logger.warning("Failed to initialize Neo4j driver: %s", exc)
                self._driver = None

        # Create in-memory store as fallback if Neo4j not available
        if self._driver is None and self._monarch_service is None:
            logger.info("Falling back to in-memory knowledge store")
            self._in_memory_store = InMemoryKnowledgeStore()
            self._in_memory_store.seed()

        # Initialize ClinVar service if enabled
        if os.getenv("ENABLE_CLINVAR", "").lower() in ["true", "1", "yes"]:
            try:
                self._clinvar_service = ClinVarService()
                logger.info("ClinVar service initialized for variant enrichment")
            except Exception as exc:
                logger.warning(f"Failed to initialize ClinVar service: {exc}")
                self._clinvar_service = None

        # Initialize Gemini RAG service if enabled
        if GEMINI_RAG_AVAILABLE and os.getenv("ENABLE_GEMINI_RAG", "true").lower() in ["true", "1", "yes"]:
            try:
                self._gemini_rag = GeminiFileSearchService()
                if self._gemini_rag.client:
                    # Initialize the File Search store
                    if self._gemini_rag.initialize_store("md_clinical_guidelines"):
                        logger.info("Gemini RAG service initialized for guideline retrieval")
                    else:
                        logger.warning("Gemini RAG store initialization failed")
                        self._gemini_rag = None
                else:
                    logger.warning("Gemini RAG client not initialized (check GOOGLE_API_KEY)")
                    self._gemini_rag = None
            except Exception as exc:
                logger.warning(f"Failed to initialize Gemini RAG service: {exc}")
                self._gemini_rag = None

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
        # Don't seed if using Monarch - Monarch data should already be in the database
        if self._monarch_service:
            logger.info("Monarch service detected - skipping seed (Monarch data should already be loaded)")
            return

        if not self._driver:
            logger.warning("No Neo4j connection - cannot seed database")
            return

        logger.info("Seeding Neo4j knowledge graph with custom schema")
        with self._driver.session(database=self._config.database) as session:
            session.execute_write(self._seed_graph)

    def close(self) -> None:
        if self._driver:
            self._driver.close()

    def get_data_source_info(self) -> Dict[str, str]:
        """Return information about which data source is currently being used."""
        info = {
            "neo4j_connected": "Yes" if self._driver else "No",
            "monarch_service": "Yes" if self._monarch_service else "No",
            "clinvar_service": "Yes" if self._clinvar_service else "No",
            "gemini_rag": "Yes" if self._gemini_rag else "No",
            "in_memory_store": "Yes" if self._in_memory_store else "No",
            "database_type": self._database_type,
        }
        
        database_name = (self._config.database or "neo4j") if self._config else "Not configured"
        
        if self._monarch_service:
            info["active_source"] = f"Monarch Initiative Database (database: {database_name})"
        elif self._in_memory_store:
            info["active_source"] = "Clinical Data (in-memory) + Monarch cache"
        elif self._driver:
            if database_name.lower() == "monarch":
                info["active_source"] = f"Neo4j Database '{database_name}' (checking for Monarch data...)"
            else:
                info["active_source"] = f"Neo4j Custom Schema (database: {database_name}, legacy mode)"
        else:
            info["active_source"] = "Unknown/No connection"
        
        if self._config:
            info["neo4j_uri"] = self._config.uri
            info["neo4j_database"] = self._config.database or "default"
        else:
            info["neo4j_uri"] = "Not configured"
            info["neo4j_database"] = "Not configured"
        
        # Get database labels if connected
        info["database_labels"] = []
        if self._driver:
            try:
                with self._driver.session(database=self._config.database if self._config else None) as session:
                    result = session.run("CALL db.labels()")
                    info["database_labels"] = [record["label"] for record in result]
            except Exception:
                info["database_labels"] = []
        
        return info

    # Query methods ----------------------------------------------------
    def get_disease_profiles(self) -> Dict[str, Dict]:
        if self._monarch_service:
            return self._assemble_monarch_disease_profiles()

        if self._in_memory_store:
            return self._in_memory_store.get_disease_profiles()

        if not self._driver:
            logger.warning("No Neo4j connection and no Monarch service - returning empty disease profiles")
            return {}

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

    def get_treatment_recommendations(self, disease_code: str, use_rag: bool = True) -> List[Dict]:
        """
        Get treatment recommendations for a disease from curated clinical data + RAG.

        This method combines two sources:
        1. Static recommendations from clinical_data.py (always available)
        2. RAG-retrieved evidence from clinical guidelines (if Gemini RAG enabled)

        Args:
            disease_code: Disease code (e.g., "DMD", "BMD", "LGMDR1")
            use_rag: Whether to query Gemini RAG for additional evidence (default: True)

        Returns:
            List of recommendation dictionaries with fields:
            - disease_code, category, recommendation, evidence_level, urgency, references
            - source_type: "static" or "RAG" to indicate data source
            - citation: File URI for RAG-sourced recommendations
            - confidence: Confidence score for RAG-sourced recommendations
        """
        # 1. Get static recommendations (always available, authoritative)
        static_recs = [
            {**rec, "source_type": "static"}
            for rec in clinical_data.TREATMENT_RECOMMENDATIONS
            if rec["disease_code"] == disease_code
        ]

        # 2. Query Gemini RAG if enabled and requested
        rag_recs = []
        if use_rag and self._gemini_rag:
            try:
                logger.info(f"Querying Gemini RAG for {disease_code} treatment recommendations")

                # Build comprehensive query for this disease
                query = f"What are the evidence-based treatment and clinical management recommendations for {disease_code}?"

                # Search with disease filtering
                evidence_list = self._gemini_rag.search_guidelines(
                    query=query,
                    disease_code=disease_code,
                    max_results=10
                )

                # Convert evidence to recommendation format
                for evidence in evidence_list:
                    rag_rec = {
                        "disease_code": disease_code,
                        "category": "Clinical Management",  # Default category
                        "recommendation": evidence.recommendation,
                        "evidence_level": evidence.evidence_level or "Unspecified",
                        "urgency": "routine",  # Default urgency
                        "references": [evidence.source] if evidence.source else [],
                        "source_type": "RAG",
                        "citation": evidence.citation,
                        "confidence": evidence.confidence,
                        "chunk_id": evidence.chunk_id,
                        "retrieved_text": evidence.retrieved_text,  # Actual text from guideline
                    }
                    rag_recs.append(rag_rec)

                logger.info(f"Retrieved {len(rag_recs)} RAG recommendations for {disease_code}")

            except Exception as exc:
                logger.warning(f"Failed to retrieve RAG recommendations for {disease_code}: {exc}")

        # 3. Merge results (static first, then RAG)
        # Keep static recommendations as authoritative, add RAG as supplementary
        all_recs = static_recs + rag_recs

        logger.info(f"Returning {len(static_recs)} static + {len(rag_recs)} RAG = {len(all_recs)} total recommendations for {disease_code}")
        return all_recs

    def _get_treatment_recommendations_from_neo4j(self, disease_code: str) -> List[Dict]:
        """Legacy method for querying custom Neo4j database (deprecated)."""
        if not self._driver:
            logger.warning("No Neo4j connection - returning empty treatment recommendations")
            return []

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
        """
        Get general fallback recommendations from curated clinical data.

        Note: These are sourced from clinical_data.py regardless of database mode.
        """
        return clinical_data.GENERAL_RECOMMENDATIONS

    def _get_general_recommendations_from_neo4j(self) -> List[Dict]:
        """Legacy method for querying custom Neo4j database (deprecated)."""
        if not self._driver:
            logger.warning("No Neo4j connection - returning empty general recommendations")
            return []

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
        """
        Get diagnostic pathway steps from curated clinical data.

        Note: Diagnostic pathways are sourced from clinical_data.py
        regardless of database mode.
        """
        for pathway in clinical_data.DIAGNOSTIC_PATHWAYS:
            if pathway["code"] == pathway_code:
                return pathway.get("steps", [])
        return []

    def _get_pathway_steps_from_neo4j(self, pathway_code: str) -> List[str]:
        """Legacy method for querying custom Neo4j database (deprecated)."""
        if not self._driver:
            logger.warning("No Neo4j connection - returning empty pathway steps")
            return []

        query = """
        MATCH (p:DiagnosticPathway {code: $code})
        RETURN p.steps AS steps
        """
        with self._driver.session(database=self._config.database) as session:
            record = session.run(query, code=pathway_code).single()
            return record["steps"] if record else []

    def get_variant_annotations(self, gene: str, variant_type: str) -> List[Dict]:
        """
        Get variant annotations with optional ClinVar enrichment.

        Returns variants from Monarch/clinical_data/Neo4j, enriched with ClinVar
        clinical significance if ENABLE_CLINVAR=true.

        IMPORTANT: clinical_data.py remains authoritative for reading frame predictions
        and therapy eligibility. ClinVar only adds supplementary clinical significance.
        """
        if self._monarch_service:
            # Get Monarch variant data and convert to expected format
            monarch_variants = self._monarch_service.get_variant_gene_associations(gene_codes_or_ids=[gene])

            # Also try to get variants associated with DMD/BMD diseases
            if gene.upper() == "DMD":
                dmd_disease_ids = ["MONDO:0010679", "MONDO:0010311"]  # DMD and BMD
                disease_variants = self._monarch_service.get_variants_by_disease(dmd_disease_ids)
                monarch_variants.extend(disease_variants)

            # Convert Monarch format to expected annotation format
            # Note: Monarch doesn't have exon/reading_frame/treatment data, so return what we can
            converted = []
            seen_variant_ids = set()

            for variant in monarch_variants:
                variant_id = variant.get("variant_id", "")
                if variant_id in seen_variant_ids:
                    continue
                seen_variant_ids.add(variant_id)

                # Extract exon info from variant name/id if possible
                exons = []
                variant_name = variant.get("variant_name", "")

                # Try multiple patterns to extract exon numbers:
                # - "exon 45-47" or "exon 45,46,47" or "exons 45-47"
                # - "del45-47" or "del(45-47)"
                # - "exon45" or "exon_45"
                patterns = [
                    r'exon[_\s]*(\d+)[-–](\d+)',  # Range: exon 45-47
                    r'exon[_\s]*(\d+)',  # Single: exon 45
                    r'del[\(]?(\d+)[-–](\d+)',  # del(45-47) or del45-47
                    r'del[\(]?(\d+)',  # del45
                    r'exons?\s*(\d+)[,\s]+(\d+)[,\s]+(\d+)',  # exons 45, 46, 47
                ]

                for pattern in patterns:
                    matches = re.findall(pattern, variant_name.lower())
                    if matches:
                        if isinstance(matches[0], tuple):
                            # Range or multiple exons
                            for match in matches:
                                if len(match) == 2:
                                    # Range
                                    start, end = int(match[0]), int(match[1])
                                    exons.extend(range(start, end + 1))
                                else:
                                    # Multiple numbers
                                    exons.extend([int(m) for m in match if m.isdigit()])
                        else:
                            # Single number
                            exons.extend([int(m) for m in matches if m.isdigit()])
                        break

                # Remove duplicates and sort
                exons = sorted(list(set(exons)))

                converted.append({
                    "uid": variant_id,
                    "exons": exons,
                    "reading_frame": None,  # Not available in Monarch
                    "predicted_phenotype": variant.get("diseases", [{}])[0].get("disease_name") if variant.get("diseases") else None,
                    "severity": None,  # Not available in Monarch
                    "eligible_treatments": [],  # Not available in Monarch
                    "gene": variant.get("gene_name", gene),
                    "variant_type": variant_type,
                    "variant_id": variant_id,
                    "variant_name": variant_name,
                    "diseases": variant.get("diseases", []),
                })

            # Merge with clinical_data variant annotations for reading frame and treatment info
            for clinical_variant in clinical_data.VARIANT_ANNOTATIONS:
                if clinical_variant["gene"].upper() == gene.upper() and clinical_variant["variant_type"] == variant_type:
                    converted.append(clinical_variant)

            # Enrich with ClinVar if enabled
            return self._enrich_variants_with_clinvar(converted, gene)

        # Fallback: Use clinical_data if no Monarch or custom Neo4j available
        if not self._driver:
            annotations = [
                ann for ann in clinical_data.VARIANT_ANNOTATIONS
                if ann["gene"].upper() == gene.upper() and ann["variant_type"] == variant_type
            ]
            # Enrich with ClinVar if enabled
            return self._enrich_variants_with_clinvar(annotations, gene)

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
            # Enrich with ClinVar if enabled
            return self._enrich_variants_with_clinvar(annotations, gene)

    def _enrich_variants_with_clinvar(self, variants: List[Dict], gene: str) -> List[Dict]:
        """
        Enrich variant annotations with ClinVar clinical significance data.

        This method is SUPPLEMENTARY - it only adds clinical significance labels
        WITHOUT overwriting critical fields like reading_frame or eligible_treatments
        from clinical_data.py.

        Args:
            variants: List of variant annotations from Monarch/clinical_data/Neo4j
            gene: Gene symbol

        Returns:
            Enriched variant list (supplementary ClinVar data added)
        """
        if not self._clinvar_service or not variants:
            return variants

        enriched = []
        for variant in variants:
            # Only enrich point mutations - large deletions less useful in ClinVar
            variant_type = variant.get("variant_type", "")

            # Skip HGVS-based lookup for large deletions (clinical_data.py is authoritative)
            # BUT add gene-level ClinVar variant table
            if variant_type == "deletion" and variant.get("exons"):
                # Large exon deletion - add gene-level ClinVar variant list
                try:
                    gene_variants = self._clinvar_service.search_variants_by_gene(
                        gene_symbol=gene,
                        max_results=10  # Get more variants for table display
                    )
                    if gene_variants:
                        enriched_variant = variant.copy()
                        # Store full variant list for table display
                        enriched_variant["clinvar_variants"] = gene_variants
                        enriched_variant["clinvar_gene_summary"] = f"{len(gene_variants)} DMD variants from ClinVar"
                        enriched.append(enriched_variant)
                        logger.debug(f"Added {len(gene_variants)} ClinVar variants for {gene} deletion")
                    else:
                        enriched.append(variant)
                except Exception as exc:
                    logger.warning(f"Gene-level ClinVar query failed for {gene}: {exc}")
                    enriched.append(variant)
                continue

            # Try to enrich with ClinVar data
            # Look for HGVS expression in various fields
            hgvs = (
                variant.get("hgvs")
                or variant.get("variant_name")
                or variant.get("uid")
            )

            if hgvs:
                try:
                    clinvar_data = self._clinvar_service.get_variant_by_hgvs(hgvs, gene)
                    if clinvar_data:
                        # Add ClinVar data WITHOUT overwriting critical fields
                        enriched_variant = variant.copy()
                        enriched_variant["clinvar_id"] = clinvar_data.get("variation_id")
                        enriched_variant["clinvar_significance"] = clinvar_data.get("clinical_significance")
                        enriched_variant["clinvar_review_status"] = clinvar_data.get("review_status")

                        # Only add phenotypes if not already present
                        if "phenotypes" not in enriched_variant or not enriched_variant["phenotypes"]:
                            enriched_variant["phenotypes"] = clinvar_data.get("phenotypes", [])

                        enriched.append(enriched_variant)
                        logger.debug(f"Enriched variant {gene}:{hgvs} with ClinVar data")
                    else:
                        # No ClinVar data found - keep original
                        enriched.append(variant)
                except Exception as exc:
                    logger.warning(f"ClinVar enrichment failed for {gene}:{hgvs}: {exc}")
                    enriched.append(variant)
            else:
                # No HGVS expression - keep original
                enriched.append(variant)

        return enriched

    def search_diseases_by_phenotypes(self, hpo_ids: Iterable[str]) -> List[Dict]:
        """Return diseases ranked by phenotype overlap."""
        if self._monarch_service:
            logger.info(f"🔎 KnowledgeGraphService: Searching for diseases matching HPO IDs: {list(hpo_ids)}")
            mapped_results = []
            monarch_results = self._monarch_service.search_diseases_by_phenotypes(hpo_ids)
            logger.info(f"📦 KnowledgeGraphService: Received {len(monarch_results)} diseases from MonarchService")

            for entry in monarch_results:
                # Map Monarch disease_id to project code
                code = self._lookup_project_code(entry["disease_id"])
                # If we can't map it, use the disease_id as code (for unknown diseases)
                if not code or code == entry["disease_id"]:
                    # Try to extract code from disease name or use a fallback
                    code = entry.get("disease_id", "UNKNOWN")

                mapped_results.append(
                    {
                        "code": code,
                        "disease_id": entry["disease_id"],
                        "disease_name": entry["disease_name"],
                        "matched_hpo_ids": entry["matched_hpo_ids"],
                        "match_count": entry["match_count"],
                    }
                )

            logger.info(f"🎯 KnowledgeGraphService: Mapped {len(mapped_results)} diseases with codes")
            logger.info(f"📋 Mapped diseases (top 15):")
            for i, disease in enumerate(mapped_results[:15], 1):
                logger.info(f"   {i}. [{disease['code']}] {disease['disease_name']} - {disease['match_count']} HPO matches")

            return mapped_results
        
        if not self._driver:
            return []
        
        # Fallback to custom schema query if not using Monarch
        return []

    # Internal helpers -------------------------------------------------
    def _seed_graph(self, tx) -> None:
        self._create_nodes(tx)
        self._create_relationships(tx)

    def _clear_database(self, tx) -> None:
        tx.run("MATCH (n) DETACH DELETE n")

    def _create_nodes(self, tx) -> None:
        """
        DEPRECATED: This method is no longer used as disease data comes from Monarch.

        Previously seeded custom Neo4j database from seed_data.py.
        Now uses Monarch Initiative database for disease/gene/phenotype data.

        All legacy seeding code has been removed. See backend/temp_archived/seed_data.py.archived
        for reference.
        """
        logger.warning("_create_nodes is deprecated - use Monarch database instead")
        return

    def _create_relationships(self, tx) -> None:
        """
        DEPRECATED: This method is no longer used as relationships come from Monarch.

        Previously created relationships in custom Neo4j database from seed_data.py.
        Now uses Monarch Initiative database which already has relationships defined.
        """
        logger.warning("_create_relationships is deprecated - use Monarch database instead")
        return

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

    # ------------------------------------------------------------------
    # Internal helpers (Monarch integration)

    def _initialize_monarch_support(self) -> None:
        if not self._driver:
            return

        try:
            # Check if database name is "monarch" - this is a strong indicator
            database_name = self._config.database or "neo4j"
            is_named_monarch = database_name.lower() == "monarch"
            
            monarch_service = MonarchService(self._driver, self._config.database)
            info = monarch_service.get_database_info()
            self._database_type = info.database_type
            
            # Check for biolink labels more aggressively
            biolink_labels = [l for l in info.available_labels if l.startswith("biolink:")]
            
            # If database is named "monarch" or has biolink labels, use Monarch service
            # BUT verify it actually has data
            has_monarch_indicators = is_named_monarch or info.database_type == "monarch" or biolink_labels

            if has_monarch_indicators:
                # Verify the database actually has disease data
                with self._driver.session(database=self._config.database) as session:
                    # Check for biolink:Disease nodes (Monarch) or Disease nodes (custom schema)
                    count_result = session.run("""
                        MATCH (d) WHERE d:`biolink:Disease` OR d:Disease
                        RETURN count(d) as disease_count
                    """)
                    disease_count = count_result.single()["disease_count"]

                    if disease_count > 0:
                        self._monarch_service = monarch_service
                        self._database_type = "monarch"
                        logger.info("Monarch database detected with %d diseases", disease_count)
                        if biolink_labels:
                            logger.info("Biolink labels found: %s", ", ".join(biolink_labels[:10]))
                    else:
                        logger.warning("Database named '%s' but no disease data found - using in-memory fallback",
                                     database_name)
                        self._driver = None  # Force fallback to in-memory
            else:
                logger.info("Database uses custom schema (not Monarch). Database: %s, Labels: %s",
                          database_name, ", ".join(info.available_labels[:10]))
        except Exception as exc:  # pylint: disable=broad-except
            logger.warning("Unable to inspect Neo4j database schema: %s", exc)
            self._database_type = "unknown"

    def _assemble_monarch_disease_profiles(self) -> Dict[str, Dict]:
        """Return disease profiles assembled from Monarch data."""
        if not self._monarch_service:
            return {}

        logger.info(f"🔧 Assembling disease profiles from Monarch for {len(DISEASE_CODE_MAP)} diseases")

        profiles: Dict[str, Dict] = {}
        for code, identifiers in DISEASE_CODE_MAP.items():
            records = self._monarch_service.get_disease_profiles(identifiers)
            if not records:
                logger.warning(f"⚠️  No Monarch data found for disease code: {code} (IDs: {identifiers})")
                continue

            phenotypes = self._merge_monarch_phenotypes(records)
            metadata = {
                "code": code,
                "name": records[0]["name"] or code,
                "phenotypes": phenotypes,
                "diagnostic_tests": [],
            }
            metadata.update(self._default_disease_metadata(code))
            profiles[code] = metadata
            logger.info(f"✅ [{code}] {metadata['name']}: {len(phenotypes)} phenotypes from Monarch")

        logger.info(f"📚 Total disease profiles loaded: {len(profiles)}")
        return profiles

    @staticmethod
    def _merge_monarch_phenotypes(records: List[Dict]) -> List[Dict]:
        """Merge phenotype arrays from multiple Monarch records."""
        merged: Dict[str, Dict] = {}
        for record in records:
            for phenotype in record.get("phenotypes", []):
                hpo_id = phenotype.get("hpo_id")
                if not hpo_id or hpo_id in merged:
                    continue
                merged[hpo_id] = phenotype
        return list(merged.values())

    @staticmethod
    def _default_disease_metadata(code: str) -> Dict:
        defaults = {
            "DMD": {
                "inheritance": "X-linked",
                "typical_onset": [3, 8],
            },
            "BMD": {
                "inheritance": "X-linked",
                "typical_onset": [10, 30],
            },
        }
        return defaults.get(code.upper(), {})

    @staticmethod
    def _lookup_project_code(disease_id: str) -> str:
        for code, identifiers in DISEASE_CODE_MAP.items():
            if disease_id in identifiers:
                return code
        return disease_id

    def export_disease_subgraph(self, disease_code: str, max_phenotypes: int = 20) -> Dict:
        """
        Export a disease-centric knowledge graph subgraph for visualization.

        This creates a graph structure suitable for react-force-graph-2d showing:
        - Disease node (center)
        - Gene associations
        - Phenotype associations
        - Variant annotations (if applicable)
        - Treatment recommendations

        Args:
            disease_code: Disease code (e.g., "DMD", "BMD")
            max_phenotypes: Maximum number of phenotype nodes to include (default: 20)

        Returns:
            Dictionary with 'nodes' and 'links' arrays in react-force-graph-2d format:
            {
                "nodes": [
                    {"id": str, "label": str, "type": str, "group": str, ...}
                ],
                "links": [
                    {"source": str, "target": str, "relationship": str, ...}
                ]
            }
        """
        nodes = []
        links = []

        # Get disease profile
        disease_profiles = self.get_disease_profiles()
        if disease_code not in disease_profiles:
            logger.warning(f"Disease code {disease_code} not found in knowledge graph")
            return {"nodes": [], "links": []}

        disease = disease_profiles[disease_code]

        # 1. Add disease node (center)
        disease_node = {
            "id": f"disease:{disease_code}",
            "label": disease.get("name", disease_code),
            "type": "Disease",
            "group": "disease",
            "code": disease_code,
            "inheritance": disease.get("inheritance"),
            "onset": disease.get("typical_onset"),
        }
        nodes.append(disease_node)

        # 2. Add gene associations
        # Map disease code to Monarch IDs to find genes
        if disease_code in DISEASE_CODE_MAP and self._monarch_service:
            disease_ids = DISEASE_CODE_MAP[disease_code]
            for disease_id in disease_ids[:1]:  # Use first ID to find genes
                # Query Monarch for gene associations
                try:
                    with self._driver.session(database=self._config.database) as session:
                        # Find genes associated with this disease
                        gene_query = """
                        MATCH (d:`biolink:Disease` {id: $disease_id})<-[:`biolink:causes`]-(g:`biolink:Gene`)
                        RETURN g.id AS gene_id, g.name AS gene_name
                        LIMIT 5
                        """
                        result = session.run(gene_query, disease_id=disease_id)
                        for record in result:
                            gene_id = record["gene_id"]
                            gene_name = record["gene_name"] or gene_id

                            gene_node = {
                                "id": f"gene:{gene_id}",
                                "label": gene_name,
                                "type": "Gene",
                                "group": "gene",
                                "gene_id": gene_id,
                            }
                            nodes.append(gene_node)

                            # Add link from gene to disease
                            links.append({
                                "source": f"gene:{gene_id}",
                                "target": f"disease:{disease_code}",
                                "relationship": "causes",
                                "label": "causes",
                            })
                except Exception as exc:
                    logger.warning(f"Failed to query gene associations for {disease_code}: {exc}")

        # 3. Add phenotype associations
        phenotypes = disease.get("phenotypes", [])
        for idx, phenotype in enumerate(phenotypes[:max_phenotypes]):
            hpo_id = phenotype.get("hpo_id")
            if not hpo_id:
                continue

            phenotype_node = {
                "id": f"phenotype:{hpo_id}",
                "label": phenotype.get("term", hpo_id),
                "type": "Phenotype",
                "group": "phenotype",
                "hpo_id": hpo_id,
                "specificity": phenotype.get("specificity"),
            }
            nodes.append(phenotype_node)

            # Add link from disease to phenotype
            links.append({
                "source": f"disease:{disease_code}",
                "target": f"phenotype:{hpo_id}",
                "relationship": "has_phenotype",
                "label": "has phenotype",
            })

        # 4. Add variant annotations (if available)
        # Try common genes for this disease
        gene_mapping = {
            "DMD": "DMD",
            "BMD": "DMD",
            "LGMDR1": "CAPN3",
            "MDC1A": "LAMA2",
        }

        if disease_code in gene_mapping:
            gene = gene_mapping[disease_code]
            variants = self.get_variant_annotations(gene, "deletion")

            for idx, variant in enumerate(variants[:5]):  # Limit to 5 variants
                variant_id = variant.get("uid") or f"{gene}_variant_{idx}"

                variant_node = {
                    "id": f"variant:{variant_id}",
                    "label": f"Exons {'-'.join(map(str, variant.get('exons', [])))}",
                    "type": "Variant",
                    "group": "variant",
                    "exons": variant.get("exons"),
                    "reading_frame": variant.get("reading_frame"),
                    "severity": variant.get("severity"),
                }
                nodes.append(variant_node)

                # Link variant to gene if gene node exists
                gene_node_id = f"gene:HGNC:2928"  # DMD gene (hardcoded for now)
                links.append({
                    "source": f"variant:{variant_id}",
                    "target": gene_node_id,
                    "relationship": "variant_of",
                    "label": "variant of",
                })

        # 5. Add treatment recommendations
        treatments = self.get_treatment_recommendations(disease_code, use_rag=False)
        for idx, treatment in enumerate(treatments[:5]):  # Limit to 5 treatments
            treatment_id = f"{disease_code}_treatment_{idx}"

            treatment_node = {
                "id": f"treatment:{treatment_id}",
                "label": treatment.get("category", "Treatment"),
                "type": "Treatment",
                "group": "treatment",
                "recommendation": treatment.get("recommendation"),
                "evidence_level": treatment.get("evidence_level"),
                "urgency": treatment.get("urgency"),
            }
            nodes.append(treatment_node)

            # Link disease to treatment
            links.append({
                "source": f"disease:{disease_code}",
                "target": f"treatment:{treatment_id}",
                "relationship": "has_recommendation",
                "label": "recommended",
            })

        logger.info(f"Exported subgraph for {disease_code}: {len(nodes)} nodes, {len(links)} links")

        return {
            "nodes": nodes,
            "links": links,
            "metadata": {
                "disease_code": disease_code,
                "disease_name": disease.get("name", disease_code),
                "node_count": len(nodes),
                "link_count": len(links),
            }
        }


class InMemoryKnowledgeStore:
    """Simplified in-memory store for development and tests."""

    def __init__(self):
        self._diseases: Dict[str, Dict] = {}
        self._recommendations: Dict[str, List[Dict]] = {}
        self._general_recs: List[Dict] = []
        self._pathways: Dict[str, List[str]] = {}
        self._variants: Dict[str, List[Dict]] = {}

    def seed(self) -> None:
        """
        Seed the in-memory store with clinical data.

        Note: Disease data is no longer seeded here - use Monarch database instead.
        This only seeds treatment recommendations, pathways, and variant annotations
        from clinical_data.py.
        """
        # Disease data now comes from Monarch - this dict is kept empty
        self._diseases = {}

        self._recommendations = {}
        for rec in clinical_data.TREATMENT_RECOMMENDATIONS:
            self._recommendations.setdefault(rec["disease_code"], []).append(rec)

        self._general_recs = clinical_data.GENERAL_RECOMMENDATIONS

        self._pathways = {
            pathway["code"]: pathway["steps"]
            for pathway in clinical_data.DIAGNOSTIC_PATHWAYS
        }

        self._variants = {}
        for variant in clinical_data.VARIANT_ANNOTATIONS:
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
