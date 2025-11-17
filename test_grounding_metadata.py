"""Test script to verify grounding metadata and citations are working."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.rag.gemini_file_search import GeminiFileSearchService
from google.genai import types

def test_grounding_metadata():
    """Test grounding metadata extraction from File Search responses."""

    print("=" * 80)
    print("TESTING GROUNDING METADATA & CITATIONS")
    print("=" * 80)

    # Initialize service
    service = GeminiFileSearchService()

    if not service.client:
        print("❌ ERROR: Gemini client not initialized")
        return

    # Initialize store
    if not service.initialize_store("md_clinical_guidelines"):
        print("❌ ERROR: Failed to initialize store")
        return

    print(f"✅ Using File Search store: {service.store.name}\n")

    # Test Query
    query = "What are the corticosteroid therapy recommendations for DMD?"
    print(f"QUERY: {query}\n")

    # Use search_guidelines method to see if it extracts grounding properly
    print("=" * 80)
    print("METHOD 1: Using search_guidelines() method")
    print("=" * 80)

    evidence_list = service.search_guidelines(
        query=query,
        disease_code="DMD",
        max_results=5
    )

    print(f"\n📊 Retrieved {len(evidence_list)} evidence passages:\n")

    for idx, evidence in enumerate(evidence_list, 1):
        print(f"{idx}. {'-' * 76}")
        print(f"   RECOMMENDATION: {evidence.recommendation[:150]}...")
        print(f"   SOURCE: {evidence.source}")
        print(f"   EVIDENCE LEVEL: {evidence.evidence_level or 'Not specified'}")
        print(f"   CITATION: {evidence.citation or 'No URI'}")
        print(f"   CONFIDENCE: {evidence.confidence:.2f}")
        print(f"   CHUNK ID: {evidence.chunk_id or 'N/A'}")
        print()

    # Direct API call to inspect full response structure
    print("=" * 80)
    print("METHOD 2: Direct API call with detailed inspection")
    print("=" * 80)

    config = types.GenerateContentConfig(
        tools=[
            types.Tool(
                file_search=types.FileSearch(
                    file_search_store_names=[service.store.name],
                    metadata_filter='disease_code="DMD"'
                )
            )
        ]
    )

    response = service.client.models.generate_content(
        model="gemini-2.5-flash",
        contents=query,
        config=config,
    )

    # Check candidates
    print(f"\nResponse has candidates: {hasattr(response, 'candidates')}")
    if hasattr(response, 'candidates'):
        print(f"Number of candidates: {len(response.candidates)}")

        if len(response.candidates) > 0:
            candidate = response.candidates[0]
            print(f"\nCandidate 0 attributes: {[attr for attr in dir(candidate) if not attr.startswith('_')]}")

            # Check for grounding_metadata
            if hasattr(candidate, 'grounding_metadata'):
                print("\n✅ GROUNDING METADATA FOUND in candidates[0]!")
                grounding = candidate.grounding_metadata
                print(f"\nGrounding metadata type: {type(grounding)}")
                print(f"Grounding attributes: {[attr for attr in dir(grounding) if not attr.startswith('_')]}")

                # Check for chunks
                if hasattr(grounding, 'grounding_chunks'):
                    chunks = grounding.grounding_chunks
                    print(f"\n✅ Found {len(chunks)} grounding chunks!")

                    for i, chunk in enumerate(chunks[:3]):
                        print(f"\nChunk {i}:")
                        print(f"  Type: {type(chunk)}")
                        print(f"  Attributes: {[attr for attr in dir(chunk) if not attr.startswith('_')]}")

                        # Try to access retrieved_context
                        if hasattr(chunk, 'retrieved_context'):
                            print(f"  ✅ Has retrieved_context")
                            ctx = chunk.retrieved_context
                            print(f"     Title: {getattr(ctx, 'title', 'N/A')}")
                            print(f"     URI: {getattr(ctx, 'uri', 'N/A')}")
                            if hasattr(ctx, 'text'):
                                print(f"     Text preview: {ctx.text[:100]}...")

                # Check for supports
                if hasattr(grounding, 'grounding_supports'):
                    supports = grounding.grounding_supports
                    print(f"\n✅ Found {len(supports)} grounding supports!")

                    for i, support in enumerate(supports[:3]):
                        print(f"\nSupport {i}:")
                        print(f"  Grounding chunk indices: {getattr(support, 'grounding_chunk_indices', 'N/A')}")
                        if hasattr(support, 'segment'):
                            seg = support.segment
                            print(f"  Segment: start={getattr(seg, 'start_index', 'N/A')}, end={getattr(seg, 'end_index', 'N/A')}")

                # Print full grounding metadata
                print(f"\nFull grounding metadata:")
                print(grounding)

            else:
                print("\n❌ No grounding_metadata in candidate")
                print(f"Available attributes: {[attr for attr in dir(candidate) if not attr.startswith('_')]}")

    print("\n" + "=" * 80)
    print("✅ GROUNDING TEST COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    test_grounding_metadata()
