"""Test script to query Gemini RAG for DMD treatment recommendations."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.rag.gemini_file_search import GeminiFileSearchService

def test_rag_query():
    """Test querying the RAG system for DMD treatment recommendations."""

    print("=" * 80)
    print("TESTING GEMINI RAG SYSTEM")
    print("=" * 80)

    # Initialize service
    print("\n1. Initializing Gemini File Search service...")
    service = GeminiFileSearchService()

    if not service.client:
        print("❌ ERROR: Gemini client not initialized")
        print("   Check your GOOGLE_API_KEY in .env file")
        return

    print("✅ Gemini client initialized")

    # Initialize store
    print("\n2. Initializing File Search store...")
    if not service.initialize_store("md_clinical_guidelines"):
        print("❌ ERROR: Failed to initialize File Search store")
        return

    print(f"✅ File Search store ready: {service.store.name}")

    # List uploaded files
    print("\n3. Listing uploaded files...")
    files = service.list_uploaded_files()
    print(f"   Found {len(files)} uploaded files:")
    for file in files:
        print(f"     - {file['name']}")

    # Query 1: Treatment recommendations
    print("\n" + "=" * 80)
    print("QUERY 1: What are the treatment recommendations for DMD?")
    print("=" * 80)

    evidence_list = service.search_guidelines(
        query="What are the evidence-based treatment and clinical management recommendations for Duchenne Muscular Dystrophy?",
        disease_code="DMD",
        max_results=5
    )

    print(f"\n📊 Retrieved {len(evidence_list)} evidence passages:\n")

    for idx, evidence in enumerate(evidence_list, 1):
        print(f"{idx}. {'-' * 76}")
        print(f"   RECOMMENDATION: {evidence.recommendation[:200]}...")
        print(f"   SOURCE: {evidence.source}")
        print(f"   EVIDENCE LEVEL: {evidence.evidence_level or 'Not specified'}")
        print(f"   CONFIDENCE: {evidence.confidence:.2f}")
        if evidence.citation:
            print(f"   CITATION: {evidence.citation}")
        print()

    # Query 2: Corticosteroid therapy
    print("\n" + "=" * 80)
    print("QUERY 2: What are the corticosteroid therapy recommendations for DMD?")
    print("=" * 80)

    evidence_list = service.search_guidelines(
        query="What are the corticosteroid therapy recommendations and dosing for DMD patients?",
        disease_code="DMD",
        max_results=3
    )

    print(f"\n📊 Retrieved {len(evidence_list)} evidence passages:\n")

    for idx, evidence in enumerate(evidence_list, 1):
        print(f"{idx}. {'-' * 76}")
        print(f"   RECOMMENDATION: {evidence.recommendation[:200]}...")
        print(f"   SOURCE: {evidence.source}")
        print(f"   EVIDENCE LEVEL: {evidence.evidence_level or 'Not specified'}")
        print()

    # Query 3: Cardiac care
    print("\n" + "=" * 80)
    print("QUERY 3: What are the cardiac surveillance recommendations for DMD?")
    print("=" * 80)

    evidence_list = service.search_guidelines(
        query="What are the cardiac surveillance and cardiomyopathy management recommendations for DMD?",
        disease_code="DMD",
        max_results=3
    )

    print(f"\n📊 Retrieved {len(evidence_list)} evidence passages:\n")

    for idx, evidence in enumerate(evidence_list, 1):
        print(f"{idx}. {'-' * 76}")
        print(f"   RECOMMENDATION: {evidence.recommendation[:200]}...")
        print(f"   SOURCE: {evidence.source}")
        print()

    print("\n" + "=" * 80)
    print("✅ RAG SYSTEM TEST COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    test_rag_query()
