"""Test script to demonstrate RAG backend logging."""
import logging
from backend.knowledge_graph.service import KnowledgeGraphService

# Set up logging to show INFO level
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:     %(message)s'
)

print("\n" + "=" * 80)
print("TESTING RAG BACKEND LOGGING")
print("=" * 80)

# Initialize service
kg_service = KnowledgeGraphService()

if not kg_service._gemini_rag:
    print("❌ RAG service not available")
    exit(1)

print(f"\n✅ RAG service initialized")
print(f"   Store: {kg_service._gemini_rag.store.name if kg_service._gemini_rag.store else 'N/A'}")

# Test 1: List uploaded files
print("\n" + "=" * 80)
print("TEST 1: List Uploaded Files")
print("=" * 80)

files = kg_service._gemini_rag.list_uploaded_files()
print(f"\n📁 Found {len(files)} files:")
for i, file in enumerate(files, 1):
    size = file.get('size_bytes', 0)
    size_str = f"{size / (1024*1024):.1f} MB" if size else "Unknown"
    print(f"   {i}. {file.get('name', 'Unknown')}")
    print(f"      Size: {size_str}")
    print(f"      MIME: {file.get('mime_type', 'Unknown')}")
    print(f"      ID: {file.get('id', 'Unknown')}")

# Test 2: Custom RAG query
print("\n" + "=" * 80)
print("TEST 2: Custom RAG Query (with detailed logging)")
print("=" * 80)

query = "What are the cardiac surveillance recommendations for DMD?"
print(f"\n🔍 Querying: '{query}'")
print("\n" + "-" * 80)
print("BACKEND OUTPUT:")
print("-" * 80)

# This will trigger the detailed logging we just added
evidence_list = kg_service._gemini_rag.search_guidelines(
    query=query,
    disease_code="DMD",
    max_results=3
)

print("\n" + "-" * 80)
print("RESULTS SUMMARY:")
print("-" * 80)

for i, evidence in enumerate(evidence_list, 1):
    print(f"\n{i}. {evidence.recommendation[:100]}...")
    print(f"   Source: {evidence.source}")
    print(f"   Confidence: {evidence.confidence}")
    if evidence.retrieved_text:
        print(f"   Retrieved text: {evidence.retrieved_text[:150]}...")

print("\n" + "=" * 80)
print("✅ TEST COMPLETE")
print("=" * 80)
print("\nNote: The detailed query/response logging is shown in the 'BACKEND OUTPUT' section above.")
print("This same logging will appear in your uvicorn server logs when using the API.")
