"""Test uploading a single file with metadata and querying it."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.rag.gemini_file_search import GeminiFileSearchService
from google.genai import types

def test_single_upload():
    """Upload a single file with metadata and test grounding."""

    print("=" * 80)
    print("TEST: SINGLE FILE UPLOAD WITH METADATA")
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

    # Upload a single file with rich metadata
    file_path = "data/guidelines/DMD/dmd_part1.pdf"

    if not Path(file_path).exists():
        print(f"❌ File not found: {file_path}")
        return

    print(f"📤 Uploading file: {file_path}")
    print("   With metadata:")

    metadata = {
        "disease_code": "DMD",
        "guideline_type": "management",
        "publication_year": 2018,
        "evidence_level": "Level_A",
        "part": 1,
        "topics": "diagnosis,genetic_testing,newborn_screening",
        "organization": "DMD_Care_Considerations_Working_Group",
        "journal": "Lancet_Neurology",
    }

    for key, value in metadata.items():
        print(f"     {key}: {value}")

    success = service.upload_guideline(
        file_path=file_path,
        metadata=metadata,
        display_name="DMD_Diagnosis_Part1_2018.pdf"
    )

    if success:
        print("\n✅ Upload successful!")
    else:
        print("\n❌ Upload failed")
        return

    # Now test querying with metadata filter
    print("\n" + "=" * 80)
    print("TEST: QUERY WITH METADATA FILTER")
    print("=" * 80)

    query = "What are the recommended diagnostic tests for DMD?"
    print(f"\nQuery: {query}")
    print(f"Filter: disease_code=\"DMD\" AND guideline_type=\"management\"")

    # Try query without filter first
    print("\n--- Query WITHOUT metadata filter ---")
    config1 = types.GenerateContentConfig(
        tools=[
            types.Tool(
                file_search=types.FileSearch(
                    file_search_store_names=[service.store.name]
                )
            )
        ]
    )

    response1 = service.client.models.generate_content(
        model="gemini-2.5-flash",
        contents=query,
        config=config1,
    )

    print(f"Response length: {len(response1.text)} chars")
    print(f"Response preview: {response1.text[:200]}...")

    if hasattr(response1, 'candidates') and len(response1.candidates) > 0:
        grounding1 = response1.candidates[0].grounding_metadata
        print(f"Grounding metadata: {grounding1 is not None}")

    # Try query WITH metadata filter
    print("\n--- Query WITH metadata filter ---")
    config2 = types.GenerateContentConfig(
        tools=[
            types.Tool(
                file_search=types.FileSearch(
                    file_search_store_names=[service.store.name],
                    metadata_filter='disease_code="DMD"'
                )
            )
        ]
    )

    response2 = service.client.models.generate_content(
        model="gemini-2.5-flash",
        contents=query,
        config=config2,
    )

    print(f"Response length: {len(response2.text)} chars")
    print(f"Response preview: {response2.text[:200]}...")

    if hasattr(response2, 'candidates') and len(response2.candidates) > 0:
        grounding2 = response2.candidates[0].grounding_metadata
        print(f"Grounding metadata: {grounding2 is not None}")

        if grounding2:
            print("\n✅ GROUNDING METADATA FOUND!")
            if hasattr(grounding2, 'grounding_chunks'):
                print(f"   Chunks: {len(grounding2.grounding_chunks)}")
            if hasattr(grounding2, 'grounding_supports'):
                print(f"   Supports: {len(grounding2.grounding_supports)}")

    print("\n" + "=" * 80)
    print("✅ TEST COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    test_single_upload()
