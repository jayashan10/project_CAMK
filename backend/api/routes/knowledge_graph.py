"""API endpoints for knowledge graph visualization."""
from typing import Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from backend.knowledge_graph.service import KnowledgeGraphService
from backend.api.dependencies import get_kg_service

router = APIRouter()


class KnowledgeGraphSubgraph(BaseModel):
    """Knowledge graph subgraph response model."""
    nodes: list = Field(..., description="List of graph nodes")
    links: list = Field(..., description="List of graph edges/links")
    metadata: Dict = Field(..., description="Metadata about the subgraph")


@router.get("/knowledge-graph/{disease_code}", response_model=KnowledgeGraphSubgraph)
async def get_disease_subgraph(
    disease_code: str,
    max_phenotypes: Optional[int] = Query(20, ge=1, le=100, description="Maximum number of phenotypes to include"),
    kg_service: KnowledgeGraphService = Depends(get_kg_service),
) -> KnowledgeGraphSubgraph:
    """Export a disease-centric knowledge graph subgraph for visualization.

    This endpoint returns a graph structure suitable for visualization with react-force-graph-2d,
    showing:
    - Disease node (center)
    - Gene associations from Monarch Initiative
    - Phenotype associations (HPO terms)
    - Variant annotations (if available)
    - Treatment recommendations

    Args:
        disease_code: Disease code (e.g., "DMD", "BMD", "LGMDR1", "MDC1A")
        max_phenotypes: Maximum number of phenotype nodes to include (default: 20)
        kg_service: Knowledge graph service (injected)

    Returns:
        Knowledge graph subgraph with nodes and links arrays:
        {
            "nodes": [
                {"id": str, "label": str, "type": str, "group": str, ...}
            ],
            "links": [
                {"source": str, "target": str, "relationship": str, ...}
            ],
            "metadata": {
                "disease_code": str,
                "disease_name": str,
                "node_count": int,
                "link_count": int
            }
        }

    Raises:
        HTTPException: If disease code not found or export fails
    """
    try:
        # Export disease subgraph
        subgraph = kg_service.export_disease_subgraph(
            disease_code=disease_code.upper(),
            max_phenotypes=max_phenotypes
        )

        # Check if disease was found
        if not subgraph.get("nodes"):
            raise HTTPException(
                status_code=404,
                detail=f"Disease code '{disease_code}' not found in knowledge graph"
            )

        return KnowledgeGraphSubgraph(**subgraph)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to export disease subgraph: {str(e)}"
        )


@router.get("/knowledge-graph/diseases/list")
async def list_available_diseases(
    kg_service: KnowledgeGraphService = Depends(get_kg_service),
) -> Dict:
    """List all available diseases in the knowledge graph.

    Returns:
        Dictionary with disease codes and names:
        {
            "diseases": [
                {"code": str, "name": str, "inheritance": str, "onset": list}
            ],
            "count": int
        }
    """
    try:
        disease_profiles = kg_service.get_disease_profiles()

        diseases = [
            {
                "code": code,
                "name": profile.get("name", code),
                "inheritance": profile.get("inheritance"),
                "onset": profile.get("typical_onset"),
            }
            for code, profile in disease_profiles.items()
        ]

        return {
            "diseases": diseases,
            "count": len(diseases)
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list diseases: {str(e)}"
        )


@router.get("/knowledge-graph/stats")
async def get_knowledge_graph_stats(
    kg_service: KnowledgeGraphService = Depends(get_kg_service),
) -> Dict:
    """Get statistics about the knowledge graph.

    Returns:
        Statistics including data sources and coverage:
        {
            "data_sources": {...},
            "disease_count": int,
            "diseases": {...}
        }
    """
    try:
        # Get data source information
        data_source_info = kg_service.get_data_source_info()

        # Get disease profiles
        disease_profiles = kg_service.get_disease_profiles()

        # Calculate statistics
        total_phenotypes = sum(
            len(profile.get("phenotypes", []))
            for profile in disease_profiles.values()
        )

        return {
            "data_sources": data_source_info,
            "disease_count": len(disease_profiles),
            "total_phenotypes": total_phenotypes,
            "diseases": {
                code: {
                    "name": profile.get("name", code),
                    "phenotype_count": len(profile.get("phenotypes", []))
                }
                for code, profile in disease_profiles.items()
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get knowledge graph stats: {str(e)}"
        )
