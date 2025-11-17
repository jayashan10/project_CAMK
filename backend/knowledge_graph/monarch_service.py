"""
Monarch knowledge graph service.

Provides a thin abstraction over the Monarch Initiative Neo4j schema so the
rest of the application can treat it like the customary knowledge graph
storage. The service focuses on DMD-related data (diseases, genes, phenotypes,
variants) and exposes higher-level query helpers that return dictionaries ready
for downstream consumption.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Set

from neo4j import Driver

from .monarch_mapper import (
    BIOLINK_CAUSES,
    BIOLINK_DISEASE,
    BIOLINK_GENE,
    BIOLINK_GENE_ASSOCIATED,
    BIOLINK_HAS_PHENOTYPE,
    BIOLINK_PHENOTYPE,
    BIOLINK_VARIANT,
    DMD_DISEASE_IDS,
    DMD_GENE_IDS,
    get_monarch_disease_ids,
    get_monarch_gene_ids,
)


@dataclass(frozen=True)
class MonarchDatabaseInfo:
    """Represents metadata about the connected Neo4j database."""

    database_type: str  # e.g., "monarch", "custom", "unknown"
    available_labels: List[str]


class MonarchService:
    """
    High level interface for querying the Monarch Initiative Neo4j database.

    The service does not assume exclusive ownership of the driver; the caller is
    responsible for lifecycle management.
    """

    def __init__(self, driver: Driver, database: Optional[str] = None):
        self._driver = driver
        self._database = database

    # ------------------------------------------------------------------
    # Detection / health

    def get_database_info(self) -> MonarchDatabaseInfo:
        """Return basic metadata about the connected Neo4j database."""
        query = "CALL db.labels()"
        labels = sorted({record["label"] for record in self._run_query(query)})
        db_type = "monarch" if any(label.startswith("biolink:") for label in labels) else "custom"
        if not labels:
            db_type = "unknown"
        return MonarchDatabaseInfo(database_type=db_type, available_labels=labels)

    def is_monarch_database(self) -> bool:
        """True when the connected database exposes biolink labels."""
        return self.get_database_info().database_type == "monarch"

    # ------------------------------------------------------------------
    # Internal helpers

    def _run_query(self, query: str, **parameters):
        with self._driver.session(database=self._database) as session:
            return list(session.run(query, **parameters))

    # ------------------------------------------------------------------
    # Placeholder API (implemented in subsequent phases)

    def get_disease_profiles(self, disease_codes_or_ids: Optional[Iterable[str]] = None) -> List[Dict]:
        """
        Fetch disease profiles (disease metadata + phenotypes) from Monarch.

        Args:
            disease_codes_or_ids: Sequence of project disease codes (e.g., "DMD")
                or Monarch identifiers (e.g., "OMIM:310200"). If omitted, defaults
                to the canonical DMD identifiers.
        """
        import logging
        logger = logging.getLogger(__name__)

        resolved_ids = self._resolve_disease_ids(disease_codes_or_ids)
        if not resolved_ids:
            return []

        logger.info(f"🔍 MonarchService.get_disease_profiles: Fetching profiles for IDs: {resolved_ids}")

        query = f"""
        MATCH (d:`{BIOLINK_DISEASE}`)
        WHERE d.id IN $disease_ids
        OPTIONAL MATCH (d)-[:`{BIOLINK_HAS_PHENOTYPE}`]->(p:`{BIOLINK_PHENOTYPE}`)
        RETURN d.id AS disease_id,
               d.name AS name,
               collect(DISTINCT {{
                   hpo_id: p.id,
                   term: p.name
               }}) AS phenotypes
        ORDER BY d.name
        """
        records = self._run_query(query, disease_ids=resolved_ids)
        profiles: List[Dict] = []
        for record in records:
            phenotypes = [
                {"hpo_id": p["hpo_id"], "term": p["term"]}
                for p in record["phenotypes"]
                if p["hpo_id"]
            ]
            profiles.append(
                {
                    "disease_id": record["disease_id"],
                    "name": record["name"],
                    "phenotypes": phenotypes,
                }
            )
            logger.info(f"   📋 {record['disease_id']}: {record['name']} - {len(phenotypes)} phenotypes")

        logger.info(f"✅ MonarchService: Retrieved {len(profiles)} disease profiles from Neo4j")
        return profiles

    def get_disease_phenotypes(self, disease_codes_or_ids: Optional[Iterable[str]] = None) -> List[Dict]:
        """Fetch only the phenotype associations for the provided diseases."""
        resolved_ids = self._resolve_disease_ids(disease_codes_or_ids)
        if not resolved_ids:
            return []

        query = f"""
        MATCH (d:`{BIOLINK_DISEASE}`)
        WHERE d.id IN $disease_ids
        MATCH (d)-[:`{BIOLINK_HAS_PHENOTYPE}`]->(p:`{BIOLINK_PHENOTYPE}`)
        RETURN d.id AS disease_id,
               p.id AS hpo_id,
               p.name AS term
        ORDER BY d.id, p.name
        """
        records = self._run_query(query, disease_ids=resolved_ids)
        return [
            {"disease_id": record["disease_id"], "hpo_id": record["hpo_id"], "term": record["term"]}
            for record in records
        ]

    def get_gene_disease_associations(self, gene_ids: Optional[Iterable[str]] = None) -> List[Dict]:
        """
        Fetch gene → disease associations for the specified gene IDs/symbols.

        Args:
            gene_ids: Iterable of gene symbols (e.g., \"DMD\") or Monarch gene
                identifiers (e.g., \"HGNC:2928\"). Defaults to the DMD gene.
        """
        resolved_ids = self._resolve_gene_ids(gene_ids)
        if not resolved_ids:
            return []

        query = f"""
        MATCH (g:`{BIOLINK_GENE}`)
        WHERE g.id IN $gene_ids
        MATCH (g)-[r]->(d:`{BIOLINK_DISEASE}`)
        WHERE type(r) IN ['{BIOLINK_CAUSES}', '{BIOLINK_GENE_ASSOCIATED}']
        RETURN g.id AS gene_id,
               g.name AS gene_name,
               d.id AS disease_id,
               d.name AS disease_name,
               type(r) AS relationship
        ORDER BY g.name, d.name
        """
        records = self._run_query(query, gene_ids=resolved_ids)
        return [
            {
                "gene_id": record["gene_id"],
                "gene_name": record["gene_name"],
                "disease_id": record["disease_id"],
                "disease_name": record["disease_name"],
                "relationship": record["relationship"],
            }
            for record in records
        ]

    def get_variant_gene_associations(
        self,
        variant_ids: Optional[Iterable[str]] = None,
        gene_codes_or_ids: Optional[Iterable[str]] = None,
    ) -> List[Dict]:
        """Fetch variant → gene associations, optionally filtered by variant IDs.
        
        Sequence variants connect to genes via:
        - biolink:is_sequence_variant_of -> GenomicEntity (genes are GenomicEntities)
        - biolink:has_sequence_variant <- GenomicEntity (reverse relationship)
        """
        gene_ids = self._resolve_gene_ids(gene_codes_or_ids)
        if not gene_ids:
            return []

        params: Dict[str, Iterable[str]] = {"gene_ids": gene_ids}
        variant_clause = ""
        if variant_ids:
            params["variant_ids"] = list(dict.fromkeys(variant_ids))
            variant_clause = "AND v.id IN $variant_ids"

        # Query 1: Variants -> GenomicEntity (where GenomicEntity is a Gene)
        # Sequence variants connect via is_sequence_variant_of to GenomicEntity
        # Genes are GenomicEntities, so we check if the target has Gene label
        query = f"""
        MATCH (v:`{BIOLINK_VARIANT}`)-[r:`biolink:is_sequence_variant_of`]->(ge:`biolink:GenomicEntity`)
        WHERE ge.id IN $gene_ids 
          AND '{BIOLINK_GENE}' IN labels(ge)
          {variant_clause}
        OPTIONAL MATCH (v)-[rel]->(d:`{BIOLINK_DISEASE}`)
        WHERE type(rel) IN ['{BIOLINK_CAUSES}', 'biolink:causes', 'biolink:genetically_associated_with']
        RETURN v.id AS variant_id,
               v.name AS variant_name,
               ge.id AS gene_id,
               ge.name AS gene_name,
               collect(DISTINCT {{
                   disease_id: d.id,
                   disease_name: d.name,
                   relationship: type(rel)
               }}) AS diseases
        ORDER BY variant_name
        """
        records = self._run_query(query, **params)
        results: List[Dict] = []
        for record in records:
            diseases = [
                disease
                for disease in record["diseases"]
                if disease["disease_id"]
            ]
            results.append(
                {
                    "variant_id": record["variant_id"],
                    "variant_name": record["variant_name"],
                    "gene_id": record["gene_id"],
                    "gene_name": record["gene_name"],
                    "diseases": diseases,
                }
            )
        
        # Query 2: Also check reverse relationship (Gene -> Variant)
        if not results:
            query2 = f"""
            MATCH (g:`{BIOLINK_GENE}`)-[r:`biolink:has_sequence_variant`]->(v:`{BIOLINK_VARIANT}`)
            WHERE g.id IN $gene_ids {variant_clause}
            OPTIONAL MATCH (v)-[rel]->(d:`{BIOLINK_DISEASE}`)
            WHERE type(rel) IN ['{BIOLINK_CAUSES}', 'biolink:causes', 'biolink:genetically_associated_with']
            RETURN v.id AS variant_id,
                   v.name AS variant_name,
                   g.id AS gene_id,
                   g.name AS gene_name,
                   collect(DISTINCT {{
                       disease_id: d.id,
                       disease_name: d.name,
                       relationship: type(rel)
                   }}) AS diseases
            ORDER BY variant_name
            """
            records2 = self._run_query(query2, **params)
            for record in records2:
                diseases = [
                    disease
                    for disease in record["diseases"]
                    if disease["disease_id"]
                ]
                results.append(
                    {
                        "variant_id": record["variant_id"],
                        "variant_name": record["variant_name"],
                        "gene_id": record["gene_id"],
                        "gene_name": record["gene_name"],
                        "diseases": diseases,
                    }
                )
        
        return results

    def get_variants_by_disease(self, disease_ids: Iterable[str]) -> List[Dict]:
        """Fetch variants associated with specific diseases.
        
        Variants can be associated with diseases via:
        - biolink:causes
        - biolink:genetically_associated_with
        """
        disease_list = list(dict.fromkeys(disease_ids))
        if not disease_list:
            return []
        
        query = f"""
        MATCH (v:`{BIOLINK_VARIANT}`)-[r]->(d:`{BIOLINK_DISEASE}`)
        WHERE d.id IN $disease_ids
          AND type(r) IN ['{BIOLINK_CAUSES}', 'biolink:causes', 'biolink:genetically_associated_with']
        OPTIONAL MATCH (v)-[r2:`biolink:is_sequence_variant_of`]->(ge:`biolink:GenomicEntity`)
        WHERE '{BIOLINK_GENE}' IN labels(ge)
        RETURN v.id AS variant_id,
               v.name AS variant_name,
               ge.id AS gene_id,
               ge.name AS gene_name,
               d.id AS disease_id,
               d.name AS disease_name,
               type(r) AS relationship
        ORDER BY variant_name
        """
        records = self._run_query(query, disease_ids=disease_list)
        results: List[Dict] = []
        for record in records:
            results.append(
                {
                    "variant_id": record["variant_id"],
                    "variant_name": record["variant_name"],
                    "gene_id": record.get("gene_id"),
                    "gene_name": record.get("gene_name"),
                    "diseases": [{
                        "disease_id": record["disease_id"],
                        "disease_name": record["disease_name"],
                        "relationship": record["relationship"],
                    }],
                }
            )
        return results

    def search_diseases_by_phenotypes(self, hpo_ids: Iterable[str]) -> List[Dict]:
        """Return diseases ranked by the number of matching phenotypes."""
        import logging
        logger = logging.getLogger(__name__)

        hpo_list = list(dict.fromkeys(hpo_ids))
        if not hpo_list:
            return []

        logger.info(f"🔍 MonarchService: Searching diseases for HPO IDs: {hpo_list}")

        query = f"""
        MATCH (p:`{BIOLINK_PHENOTYPE}`)
        WHERE p.id IN $hpo_ids
        MATCH (p)<-[:`{BIOLINK_HAS_PHENOTYPE}`]-(d:`{BIOLINK_DISEASE}`)
        WITH d, collect(DISTINCT p.id) AS matched_hpo_ids
        RETURN d.id AS disease_id,
               d.name AS disease_name,
               matched_hpo_ids,
               size(matched_hpo_ids) AS match_count
        ORDER BY match_count DESC, disease_name
        """
        records = self._run_query(query, hpo_ids=hpo_list)

        results = [
            {
                "disease_id": record["disease_id"],
                "disease_name": record["disease_name"],
                "matched_hpo_ids": record["matched_hpo_ids"],
                "match_count": record["match_count"],
            }
            for record in records
        ]

        logger.info(f"✅ MonarchService: Found {len(results)} diseases from Neo4j")
        if results:
            logger.info(f"📊 Top 10 diseases by match count:")
            for i, disease in enumerate(results[:10], 1):
                logger.info(f"   {i}. {disease['disease_name']} - {disease['match_count']} matches - {disease['disease_id']}")

        return results

    # ------------------------------------------------------------------
    # Helpers

    def _resolve_disease_ids(self, disease_codes_or_ids: Optional[Iterable[str]]) -> List[str]:
        """Normalize disease identifiers."""
        if not disease_codes_or_ids:
            disease_codes_or_ids = DMD_DISEASE_IDS

        resolved: Set[str] = set()
        for value in disease_codes_or_ids:
            if ":" in value:
                resolved.add(value)
            else:
                resolved.update(get_monarch_disease_ids(value))
        return sorted(resolved)

    def _resolve_gene_ids(self, gene_codes_or_ids: Optional[Iterable[str]]) -> List[str]:
        """Normalize gene identifiers."""
        if not gene_codes_or_ids:
            gene_codes_or_ids = DMD_GENE_IDS

        resolved: Set[str] = set()
        for value in gene_codes_or_ids:
            if ":" in value:
                resolved.add(value)
            else:
                resolved.update(get_monarch_gene_ids(value))
        return sorted(resolved)


