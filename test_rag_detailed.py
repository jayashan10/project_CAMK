"""Test script with detailed response inspection."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.rag.gemini_file_search import GeminiFileSearchService
from google.genai import types

def test_rag_detailed():
    """Test RAG with detailed response inspection."""

    print("=" * 80)
    print("TESTING GEMINI RAG - DETAILED RESPONSE")
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

    # Query
    query = "What are the corticosteroid therapy recommendations for DMD?"
    print(f"QUERY: {query}\n")

    # Make direct API call to inspect response
    config = types.GenerateContentConfig(
        tools=[
            types.Tool(
                file_search=types.FileSearch(
                    file_search_store_names=[service.store.name]
                )
            )
        ]
    )

    response = service.client.models.generate_content(
        model="gemini-2.5-flash",
        contents=query,
        config=config,
    )

    print("RESPONSE TEXT:")
    print("-" * 80)
    print(response.text)
    print("-" * 80)

    print("\nGROUNDING METADATA:")
    print("-" * 80)
    if hasattr(response, 'grounding_metadata'):
        print(f"Has grounding_metadata: Yes")
        grounding = response.grounding_metadata
        print(f"Grounding type: {type(grounding)}")
        print(f"Grounding dir: {dir(grounding)}")

        if hasattr(grounding, 'grounding_chunks'):
            print(f"\nGrounding chunks count: {len(grounding.grounding_chunks)}")
            for idx, chunk in enumerate(grounding.grounding_chunks[:3]):
                print(f"\nChunk {idx + 1}:")
                print(f"  Type: {type(chunk)}")
                print(f"  Dir: {dir(chunk)}")
                if hasattr(chunk, 'web') and chunk.web:
                    print(f"  Web: {chunk.web}")
                if hasattr(chunk, 'retrievalMetadata'):
                    print(f"  Retrieval Metadata: {chunk.retrievalMetadata}")

        if hasattr(grounding, 'grounding_supports'):
            print(f"\nGrounding supports count: {len(grounding.grounding_supports)}")

        if hasattr(grounding, 'search_entry_point'):
            print(f"\nSearch entry point: {grounding.search_entry_point}")

        if hasattr(grounding, 'web_search_queries'):
            print(f"\nWeb search queries: {grounding.web_search_queries}")

        # Print full grounding metadata
        print(f"\nFull grounding metadata: {grounding}")
    else:
        print("No grounding_metadata in response")

    print("\nFULL RESPONSE ATTRIBUTES:")
    print("-" * 80)
    print(f"Response type: {type(response)}")
    print(f"Response dir: {[attr for attr in dir(response) if not attr.startswith('_')]}")

    print("\n" + "=" * 80)
    print("✅ DETAILED TEST COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    test_rag_detailed()
