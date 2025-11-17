"""
Utilities for mapping Monarch (Biolink Model) data to the project's schema.

The Monarch Initiative stores data using Biolink labels/relationships, whereas
the rest of this project expects simplified names such as Disease, Gene,
Phenotype, and Variant. This module centralizes that translation logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Sequence

# ---------------------------------------------------------------------------
# Biolink labels and relationships of interest

BIOLINK_DISEASE = "biolink:Disease"
BIOLINK_GENE = "biolink:Gene"
BIOLINK_PHENOTYPE = "biolink:PhenotypicFeature"
BIOLINK_VARIANT = "biolink:SequenceVariant"

BIOLINK_HAS_PHENOTYPE = "biolink:has_phenotype"
BIOLINK_GENE_ASSOCIATED = "biolink:gene_associated_with_condition"
BIOLINK_CAUSES = "biolink:causes"
BIOLINK_VARIANT_OF = "biolink:is_sequence_variant_of"

PROJECT_RELATIONSHIPS = {
    BIOLINK_HAS_PHENOTYPE: "HAS_PHENOTYPE",
    BIOLINK_GENE_ASSOCIATED: "ASSOCIATED_WITH",
    BIOLINK_CAUSES: "ASSOCIATED_WITH",
    BIOLINK_VARIANT_OF: "AFFECTS",
}

# ---------------------------------------------------------------------------
# Identifier mappings (Monarch → project codes)

DMD_DISEASE_IDS: Sequence[str] = ("MONDO:0010679", "OMIM:310200", "ORPHA:98896")
BMD_DISEASE_IDS: Sequence[str] = ("MONDO:0010311", "OMIM:300376", "ORPHA:98895", "MONDO:0010759")
LGMD_DISEASE_IDS: Sequence[str] = ("MONDO:0015152",)  # Autosomal recessive limb-girdle muscular dystrophy
LAMA2_CMD_DISEASE_IDS: Sequence[str] = ("MONDO:0011925", "MONDO:0100228")  # Congenital merosin-deficient MD 1A / LAMA2-related MD

DMD_GENE_IDS: Sequence[str] = ("HGNC:2928", "NCBIGene:1756", "ENSEMBL:ENSG00000198947")
LAMA2_GENE_IDS: Sequence[str] = ("HGNC:6482", "ENSEMBL:ENSG00000196569", "OMIM:156225")
CAPN3_GENE_IDS: Sequence[str] = ("HGNC:1480",)  # Calpain-3 (LGMD R1/2A)

DISEASE_CODE_MAP: Dict[str, Sequence[str]] = {
    "DMD": DMD_DISEASE_IDS,
    "BMD": BMD_DISEASE_IDS,
    "LGMD": LGMD_DISEASE_IDS,
    "LAMA2-CMD": LAMA2_CMD_DISEASE_IDS,
}

GENE_CODE_MAP: Dict[str, Sequence[str]] = {
    "DMD": DMD_GENE_IDS,
    "LAMA2": LAMA2_GENE_IDS,
    "CAPN3": CAPN3_GENE_IDS,
}


def get_monarch_disease_ids(code: str) -> Sequence[str]:
    """Return Monarch identifiers for a project disease code (e.g., DMD)."""
    return DISEASE_CODE_MAP.get(code.upper(), ())


def get_monarch_gene_ids(gene_symbol: str) -> Sequence[str]:
    """Return Monarch identifiers for a project gene symbol (e.g., DMD)."""
    return GENE_CODE_MAP.get(gene_symbol.upper(), ())


def map_relationship(biolink_rel: str) -> str:
    """Translate a Biolink relationship to the project's terminology."""
    return PROJECT_RELATIONSHIPS.get(biolink_rel, biolink_rel)


@dataclass(frozen=True)
class MonarchDiseaseRecord:
    """Normalized disease representation returned by the adapter."""

    code: str
    identifiers: Sequence[str]


def iter_disease_codes(codes: Iterable[str]) -> Iterable[MonarchDiseaseRecord]:
    """Yield disease records with resolved Monarch identifiers."""
    for code in codes:
        ids = get_monarch_disease_ids(code)
        if ids:
            yield MonarchDiseaseRecord(code=code.upper(), identifiers=ids)

