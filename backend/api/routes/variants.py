"""API endpoints for variant interpretation using ClinVar."""
import logging
import os
from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from backend.knowledge_graph.service import KnowledgeGraphService
from backend.knowledge_graph.clinvar_service import ClinVarService
from backend.api.dependencies import get_kg_service

logger = logging.getLogger(__name__)
router = APIRouter()


# Pydantic models for request/response
class VariantQuery(BaseModel):
    """Request model for variant lookup."""
    gene: str = Field(..., description="Gene symbol (e.g., 'DMD', 'LAMA2', 'CAPN3')")
    hgvs: Optional[str] = Field(None, description="HGVS expression (e.g., 'NM_004006.2:c.6439-?_6762+?del')")
    exons: Optional[List[int]] = Field(None, description="List of affected exons for deletions")
    variant_type: Optional[str] = Field("deletion", description="Variant type (deletion, missense, nonsense, etc.)")


class ClinVarData(BaseModel):
    """ClinVar reference data."""
    clinvar_id: Optional[str] = Field(None, description="ClinVar variation ID")
    clinical_significance: Optional[str] = Field(None, description="Clinical significance (Pathogenic, Benign, VUS, etc.)")
    review_status: Optional[str] = Field(None, description="Review status (practice guideline, reviewed by expert panel, etc.)")
    submitter_count: Optional[int] = Field(None, description="Number of submitters")
    last_evaluated: Optional[str] = Field(None, description="Last evaluation date")
    url: Optional[str] = Field(None, description="ClinVar URL")


class CuratedVariantData(BaseModel):
    """Curated clinical interpretation data."""
    source: str = Field("curated", description="Data source (curated/fallback)")
    reading_frame: Optional[str] = Field(None, description="Reading frame prediction (in-frame/out-of-frame/exception)")
    predicted_phenotype: Optional[str] = Field(None, description="Predicted phenotype/disease")
    severity: Optional[str] = Field(None, description="Severity (severe/moderate/mild/variable)")
    eligible_treatments: List[str] = Field(default_factory=list, description="FDA-approved therapies")
    notes: Optional[str] = Field(None, description="Clinical notes")


class VariantInterpretation(BaseModel):
    """Complete variant interpretation combining curated and ClinVar data."""
    gene: str
    variant_type: str
    exons: Optional[List[int]] = None
    hgvs: Optional[str] = None
    protein_change: Optional[str] = None

    # Curated clinical data
    clinical_data: CuratedVariantData

    # ClinVar reference data (optional)
    clinvar_data: Optional[ClinVarData] = None


class VariantSearchResponse(BaseModel):
    """Response for variant search by gene."""
    gene: str
    variant_count: int
    variants: List[VariantInterpretation]
    clinvar_enabled: bool
    data_sources: List[str]


@router.post("/variants/interpret", response_model=VariantInterpretation)
async def interpret_variant(
    query: VariantQuery,
    kg_service: KnowledgeGraphService = Depends(get_kg_service),
) -> VariantInterpretation:
    """
    Interpret a genetic variant using curated database + real-time ClinVar lookup.

    This endpoint:
    1. Matches variant against curated database (reading frame, treatments)
    2. Queries NCBI ClinVar API for clinical significance (if enabled)
    3. Returns combined interpretation

    Args:
        query: Variant query with gene, exons, or HGVS expression
        kg_service: Knowledge graph service (injected)

    Returns:
        Complete variant interpretation with curated + ClinVar data

    Example:
        POST /api/variants/interpret
        {
            "gene": "DMD",
            "exons": [45, 46, 47],
            "variant_type": "deletion"
        }

    Response:
        {
            "gene": "DMD",
            "exons": [45, 46, 47],
            "clinical_data": {
                "reading_frame": "out-of-frame",
                "predicted_phenotype": "Duchenne Muscular Dystrophy",
                "severity": "severe",
                "eligible_treatments": ["Casimersen (Amondys 45)"]
            },
            "clinvar_data": {
                "clinvar_id": "VCV000123456",
                "clinical_significance": "Pathogenic",
                "review_status": "practice guideline",
                "url": "https://www.ncbi.nlm.nih.gov/clinvar/variation/123456"
            }
        }
    """
    try:
        logger.info(f"🔬 Interpreting variant: {query.gene} {query.variant_type}")
        if query.exons:
            logger.info(f"   Exons: {query.exons}")
        if query.hgvs:
            logger.info(f"   HGVS: {query.hgvs}")

        # Get curated variant annotations
        annotations = kg_service.get_variant_annotations(
            gene=query.gene,
            variant_type=query.variant_type
        )

        # Find matching annotation
        matched = None
        if query.exons:
            exon_set = set(query.exons)
            for annotation in annotations:
                annotated_exons = set(annotation.get("exons", []))
                if annotated_exons == exon_set:
                    matched = annotation
                    logger.info(f"✅ Matched curated variant")
                    break

        if not matched and query.hgvs:
            # Try to match by HGVS
            for annotation in annotations:
                if annotation.get("hgvs") == query.hgvs:
                    matched = annotation
                    logger.info(f"✅ Matched curated variant by HGVS")
                    break

        if not matched:
            raise HTTPException(
                status_code=404,
                detail=f"No curated annotation found for {query.gene} variant. Try using exons or HGVS expression."
            )

        # Build curated clinical data
        clinical_data = CuratedVariantData(
            source="curated",
            reading_frame=matched.get("reading_frame"),
            predicted_phenotype=matched.get("predicted_phenotype"),
            severity=matched.get("severity"),
            eligible_treatments=matched.get("eligible_treatments", []),
            notes=matched.get("notes")
        )

        # Try to get ClinVar data (if enabled)
        clinvar_data = None
        clinvar_enabled = os.getenv("ENABLE_CLINVAR", "false").lower() in ("true", "1", "yes")

        if clinvar_enabled:
            logger.info("🔍 Querying ClinVar API...")
            try:
                clinvar_service = ClinVarService()

                # Query ClinVar by HGVS if available
                hgvs_expr = query.hgvs or matched.get("hgvs")
                if hgvs_expr:
                    clinvar_result = clinvar_service.get_variant_by_hgvs(
                        gene_symbol=query.gene,
                        hgvs_expression=hgvs_expr
                    )

                    if clinvar_result:
                        logger.info(f"✅ Found in ClinVar: {clinvar_result.get('clinvar_id')}")
                        clinvar_data = ClinVarData(
                            clinvar_id=clinvar_result.get("clinvar_id"),
                            clinical_significance=clinvar_result.get("clinical_significance"),
                            review_status=clinvar_result.get("review_status"),
                            submitter_count=clinvar_result.get("submitter_count"),
                            last_evaluated=clinvar_result.get("last_evaluated"),
                            url=f"https://www.ncbi.nlm.nih.gov/clinvar/variation/{clinvar_result.get('clinvar_id', '').replace('VCV', '')}" if clinvar_result.get('clinvar_id') else None
                        )
                    else:
                        logger.info("⚠️ Specific variant not found in ClinVar")
                else:
                    # No HGVS available - show gene-level ClinVar data instead
                    logger.info(f"ℹ️ No HGVS for precise lookup, fetching gene-level ClinVar data for {query.gene}")
                    gene_variants = clinvar_service.search_variants_by_gene(
                        gene_symbol=query.gene,
                        max_results=5
                    )

                    if gene_variants:
                        # Use first pathogenic variant as representative
                        representative = gene_variants[0]
                        logger.info(f"✅ Showing representative ClinVar data for {query.gene} gene")
                        clinvar_data = ClinVarData(
                            clinvar_id=f"Gene: {query.gene}",
                            clinical_significance=f"{len(gene_variants)}+ variants in ClinVar",
                            review_status=representative.get("review_status", "Multiple entries"),
                            submitter_count=len(gene_variants),
                            last_evaluated=None,
                            url=f"https://www.ncbi.nlm.nih.gov/clinvar?term={query.gene}[gene]"
                        )

            except Exception as e:
                logger.warning(f"⚠️ ClinVar query failed: {e}")
                # Continue without ClinVar data
        else:
            logger.info("ℹ️ ClinVar disabled (ENABLE_CLINVAR=false)")

        # Build response
        interpretation = VariantInterpretation(
            gene=query.gene,
            variant_type=query.variant_type,
            exons=query.exons or matched.get("exons"),
            hgvs=query.hgvs or matched.get("hgvs"),
            protein_change=matched.get("protein_change"),
            clinical_data=clinical_data,
            clinvar_data=clinvar_data
        )

        return interpretation

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Variant interpretation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to interpret variant: {str(e)}"
        )


@router.get("/variants/search/{gene}", response_model=VariantSearchResponse)
async def search_variants_by_gene(
    gene: str,
    variant_type: Optional[str] = Query(None, description="Filter by variant type"),
    include_clinvar: bool = Query(True, description="Include ClinVar data for each variant"),
    kg_service: KnowledgeGraphService = Depends(get_kg_service),
) -> VariantSearchResponse:
    """
    Search all curated variants for a gene, optionally enriched with ClinVar data.

    This endpoint:
    1. Returns all curated variants for the gene
    2. Optionally enriches each with ClinVar lookup (if enabled and HGVS available)

    Args:
        gene: Gene symbol (e.g., 'DMD', 'LAMA2', 'CAPN3')
        variant_type: Optional filter by variant type
        include_clinvar: Whether to include ClinVar data (default: True)
        kg_service: Knowledge graph service (injected)

    Returns:
        List of variants with curated + ClinVar data

    Example:
        GET /api/variants/search/DMD?variant_type=deletion

    Response:
        {
            "gene": "DMD",
            "variant_count": 19,
            "clinvar_enabled": true,
            "variants": [...]
        }
    """
    try:
        logger.info(f"🔍 Searching variants for gene: {gene}")

        # Get curated annotations
        annotations = kg_service.get_variant_annotations(
            gene=gene.upper(),
            variant_type=variant_type
        )

        if not annotations:
            raise HTTPException(
                status_code=404,
                detail=f"No curated variants found for gene '{gene}'"
            )

        logger.info(f"   Found {len(annotations)} curated variants")

        # Check if ClinVar is enabled
        clinvar_enabled = os.getenv("ENABLE_CLINVAR", "false").lower() in ("true", "1", "yes")
        clinvar_service = None

        if clinvar_enabled and include_clinvar:
            logger.info("   ClinVar enrichment enabled")
            clinvar_service = ClinVarService()

        # Build variant interpretations
        variants = []
        for annotation in annotations:
            # Curated data
            clinical_data = CuratedVariantData(
                source="curated",
                reading_frame=annotation.get("reading_frame"),
                predicted_phenotype=annotation.get("predicted_phenotype"),
                severity=annotation.get("severity"),
                eligible_treatments=annotation.get("eligible_treatments", []),
                notes=annotation.get("notes")
            )

            # ClinVar data (if enabled and HGVS available)
            clinvar_data = None
            if clinvar_service and annotation.get("hgvs"):
                try:
                    result = clinvar_service.get_variant_by_hgvs(
                        gene_symbol=gene.upper(),
                        hgvs_expression=annotation["hgvs"]
                    )

                    if result:
                        clinvar_data = ClinVarData(
                            clinvar_id=result.get("clinvar_id"),
                            clinical_significance=result.get("clinical_significance"),
                            review_status=result.get("review_status"),
                            submitter_count=result.get("submitter_count"),
                            last_evaluated=result.get("last_evaluated"),
                            url=f"https://www.ncbi.nlm.nih.gov/clinvar/variation/{result.get('clinvar_id', '').replace('VCV', '')}" if result.get('clinvar_id') else None
                        )
                except Exception as e:
                    logger.warning(f"   ClinVar lookup failed for {annotation.get('hgvs')}: {e}")

            # Build interpretation
            interpretation = VariantInterpretation(
                gene=gene.upper(),
                variant_type=annotation.get("variant_type", variant_type or "unknown"),
                exons=annotation.get("exons"),
                hgvs=annotation.get("hgvs"),
                protein_change=annotation.get("protein_change"),
                clinical_data=clinical_data,
                clinvar_data=clinvar_data
            )

            variants.append(interpretation)

        data_sources = ["curated"]
        if clinvar_enabled and include_clinvar:
            data_sources.append("clinvar")

        return VariantSearchResponse(
            gene=gene.upper(),
            variant_count=len(variants),
            variants=variants,
            clinvar_enabled=clinvar_enabled,
            data_sources=data_sources
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Variant search failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search variants: {str(e)}"
        )


@router.get("/variants/clinvar/gene/{gene}")
async def query_clinvar_directly(
    gene: str,
    max_results: int = Query(50, ge=1, le=200, description="Maximum results to return"),
) -> Dict:
    """
    Query ClinVar API directly for all variants in a gene (no curated data).

    This is a showcase endpoint that demonstrates direct ClinVar API access
    without relying on curated annotations.

    Args:
        gene: Gene symbol
        max_results: Maximum number of results (default: 50)

    Returns:
        Raw ClinVar results from NCBI API

    Example:
        GET /api/variants/clinvar/gene/DMD?max_results=10
    """
    try:
        # Check if ClinVar is enabled
        clinvar_enabled = os.getenv("ENABLE_CLINVAR", "false").lower() in ("true", "1", "yes")
        if not clinvar_enabled:
            raise HTTPException(
                status_code=503,
                detail="ClinVar API is disabled. Set ENABLE_CLINVAR=true in .env"
            )

        logger.info(f"🔬 Querying ClinVar directly for gene: {gene}")

        clinvar_service = ClinVarService()
        results = clinvar_service.search_variants_by_gene(
            gene_symbol=gene.upper(),
            max_results=max_results
        )

        logger.info(f"✅ Retrieved {len(results)} variants from ClinVar")

        return {
            "gene": gene.upper(),
            "source": "ClinVar (NCBI E-utilities API)",
            "variant_count": len(results),
            "max_results": max_results,
            "variants": results,
            "note": "This is raw ClinVar data without curated clinical interpretations"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ ClinVar API query failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"ClinVar API query failed: {str(e)}"
        )


@router.get("/variants/therapies")
async def list_fda_therapies() -> Dict:
    """
    List all FDA-approved therapies for muscular dystrophies in our database.

    Returns:
        Dictionary of therapies with eligibility criteria
    """
    from backend.knowledge_graph.clinical_data import VARIANT_ANNOTATIONS

    # Extract all unique therapies
    therapy_map = {}
    for variant in VARIANT_ANNOTATIONS:
        for treatment in variant.get("eligible_treatments", []):
            if treatment not in therapy_map:
                therapy_map[treatment] = {
                    "name": treatment,
                    "gene": variant["gene"],
                    "eligible_exons": [],
                    "variant_count": 0
                }

            # Add exons if this is a deletion
            if variant.get("exons"):
                therapy_map[treatment]["eligible_exons"].append(variant["exons"])

            therapy_map[treatment]["variant_count"] += 1

    return {
        "therapy_count": len(therapy_map),
        "therapies": list(therapy_map.values()),
        "note": "FDA-approved exon-skipping therapies curated from clinical guidelines"
    }
