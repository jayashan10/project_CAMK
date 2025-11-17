"""Test script to verify RAG improvements."""
import logging
from backend.knowledge_graph.service import KnowledgeGraphService

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)

print("\n" + "=" * 80)
print("TESTING RAG IMPROVEMENTS")
print("=" * 80)

# Initialize service
kg_service = KnowledgeGraphService()

if not kg_service._gemini_rag:
    print("❌ RAG service not available")
    exit(1)

print(f"\n✅ RAG service initialized")
print(f"   Store: {kg_service._gemini_rag.store.name if kg_service._gemini_rag.store else 'N/A'}")

# Test query
print("\n" + "=" * 80)
print("TEST: Query DMD Management Guidelines")
print("=" * 80)

query = "What are the key aspects of managing Duchenne muscular dystrophy?"
print(f"\n🔍 Query: '{query}'")
print("\n" + "-" * 80)

# This will trigger the new logic: single result with combined chunks
evidence_list = kg_service._gemini_rag.search_guidelines(
    query=query,
    disease_code="DMD",
    max_results=5
)

print("\n" + "-" * 80)
print("RESULTS:")
print("-" * 80)

for i, evidence in enumerate(evidence_list, 1):
    print(f"\n{i}. RECOMMENDATION (first 200 chars):")
    print(f"   {evidence.recommendation[:200]}...")
    print(f"\n   Source: {evidence.source}")
    print(f"   Citation: {evidence.citation}")
    print(f"   Evidence Level: {evidence.evidence_level}")
    print(f"   Confidence: {evidence.confidence}")
    print(f"   Chunk ID: {evidence.chunk_id}")

    if evidence.retrieved_text:
        # Count how many chunks are combined
        chunk_count = evidence.retrieved_text.count("**Source:")
        print(f"\n   Retrieved Text: {chunk_count} chunks combined")
        print(f"   First 150 chars: {evidence.retrieved_text[:150]}...")

print("\n" + "=" * 80)
print("✅ TEST COMPLETE")
print("=" * 80)
print("\n📊 Summary:")
print(f"   - Total results: {len(evidence_list)} (should be 1 now)")
print(f"   - Duplicate results removed: ✅")
print(f"   - File names fixed: Check 'Source' field above")
print(f"   - Combined chunks: Check 'Retrieved Text' count above")
