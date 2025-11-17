"""API endpoints for RAG (Retrieval-Augmented Generation) queries."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.knowledge_graph.service import KnowledgeGraphService
from backend.api.dependencies import get_kg_service

router = APIRouter()


class RAGQuery(BaseModel):
    """Custom RAG query request"""
    query: str = Field(..., description="Question to ask the RAG system")
    disease_code: Optional[str] = Field(None, description="Optional disease filter (DMD, BMD, etc.)")
    max_results: int = Field(5, ge=1, le=20, description="Maximum number of results to return")


class RAGResult(BaseModel):
    """RAG query result with retrieved evidence"""
    recommendation: str  # Synthesized answer from Gemini
    source: str  # Document title/ID
    evidence_level: Optional[str] = None
    citation: str
    confidence: float
    chunk_id: Optional[str] = None
    retrieved_text: Optional[str] = None  # Actual text from guideline


class RAGQueryResponse(BaseModel):
    """Response for custom RAG queries"""
    query: str
    results: List[RAGResult]
    total_results: int


class GuidelineInfo(BaseModel):
    """Information about an uploaded guideline"""
    name: str
    id: str
    create_time: Optional[str] = None
    size_bytes: Optional[int] = None
    mime_type: Optional[str] = None


class GuidelinesListResponse(BaseModel):
    """Response listing all uploaded guidelines"""
    guidelines: List[GuidelineInfo]
    total_count: int
    store_name: str


@router.post("/rag/query", response_model=RAGQueryResponse)
async def query_rag(
    query_request: RAGQuery,
    kg_service: KnowledgeGraphService = Depends(get_kg_service),
) -> RAGQueryResponse:
    """
    Query the RAG system with a custom question.

    This endpoint allows you to ask any clinical question and retrieve
    evidence-based answers from uploaded clinical guidelines.

    Args:
        query_request: RAG query with question and optional filters
        kg_service: Knowledge graph service (injected)

    Returns:
        RAG results with synthesized answers and retrieved guideline passages

    Example:
        POST /api/rag/query
        {
            "query": "What are the cardiac surveillance recommendations for DMD?",
            "disease_code": "DMD",
            "max_results": 5
        }
    """
    if not kg_service._gemini_rag:
        raise HTTPException(
            status_code=503,
            detail="RAG service is not available. Check GOOGLE_API_KEY and ENABLE_GEMINI_RAG settings."
        )

    try:
        # Query the RAG system
        evidence_list = kg_service._gemini_rag.search_guidelines(
            query=query_request.query,
            disease_code=query_request.disease_code,
            max_results=query_request.max_results
        )

        # Convert to API response format
        results = [
            RAGResult(
                recommendation=evidence.recommendation,
                source=evidence.source,
                evidence_level=evidence.evidence_level,
                citation=evidence.citation,
                confidence=evidence.confidence,
                chunk_id=evidence.chunk_id,
                retrieved_text=evidence.retrieved_text,
            )
            for evidence in evidence_list
        ]

        return RAGQueryResponse(
            query=query_request.query,
            results=results,
            total_results=len(results)
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"RAG query failed: {str(e)}"
        ) from e


@router.get("/rag/guidelines", response_model=GuidelinesListResponse)
async def list_guidelines(
    kg_service: KnowledgeGraphService = Depends(get_kg_service),
) -> GuidelinesListResponse:
    """
    List all uploaded clinical guidelines in the RAG system.

    Returns information about all PDFs uploaded to the Gemini File Search store.

    Returns:
        List of guidelines with names, IDs, and metadata
    """
    if not kg_service._gemini_rag:
        raise HTTPException(
            status_code=503,
            detail="RAG service is not available. Check GOOGLE_API_KEY and ENABLE_GEMINI_RAG settings."
        )

    try:
        # Get list of uploaded files
        files = kg_service._gemini_rag.list_uploaded_files()

        # Convert to API response format
        guidelines = [
            GuidelineInfo(
                name=file.get("name", "Unknown"),
                id=file.get("id", ""),
                create_time=file.get("create_time"),
                size_bytes=file.get("size_bytes"),
                mime_type=file.get("mime_type")
            )
            for file in files
        ]

        store_name = kg_service._gemini_rag.store.name if kg_service._gemini_rag.store else "Unknown"

        return GuidelinesListResponse(
            guidelines=guidelines,
            total_count=len(guidelines),
            store_name=store_name
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list guidelines: {str(e)}"
        ) from e
