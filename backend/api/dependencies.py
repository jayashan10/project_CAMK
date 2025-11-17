"""FastAPI dependency injection for shared services."""
from typing import Optional
from backend.knowledge_graph.service import KnowledgeGraphService

# Global singleton instance
_kg_service: Optional[KnowledgeGraphService] = None


def get_kg_service() -> KnowledgeGraphService:
    """Get or create the knowledge graph service singleton.

    This ensures we reuse the same Neo4j connection across all requests
    instead of creating a new connection for each API call.
    """
    global _kg_service
    if _kg_service is None:
        _kg_service = KnowledgeGraphService()
    return _kg_service


def cleanup_kg_service() -> None:
    """Close the knowledge graph service connection.

    Should be called during application shutdown.
    """
    global _kg_service
    if _kg_service is not None:
        _kg_service.close()
        _kg_service = None
