"""Clean up wrong uploads and upload correct guideline PDFs."""
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.rag.gemini_file_search import GeminiFileSearchService

def main():
    print("=" * 80)
    print("CLEANING UP AND RE-UPLOADING GUIDELINES")
    print("=" * 80)

    # Initialize service
    import os
    print(f"API Key: {'SET' if os.getenv('GOOGLE_API_KEY') else 'NOT SET'}")

    service = GeminiFileSearchService()

    print(f"Client initialized: {service.client is not None}")
    print(f"Store initialized: {service.store is not None}")

    if not service.client:
        print("❌ ERROR: Gemini client not initialized - check GOOGLE_API_KEY")
        return

    # Step 0: Delete all files FIRST
    print("\n🗑️  STEP 0: Deleting all uploaded files...")
    print("-" * 80)
    try:
        files = list(service.client.files.list())
        print(f"Found {len(files)} file(s)")

        for file in files:
            file_id = file.name
            display_name = getattr(file, 'display_name', file_id)
            print(f"   Deleting: {display_name}")
            try:
                service.client.files.delete(name=file_id)
                print(f"   ✅ Deleted")
            except Exception as e:
                print(f"   ❌ Failed: {e}")
    except Exception as e:
        print(f"❌ Error listing/deleting files: {e}")

    # Wait for deletions to propagate
    import time
    print("\n⏳ Waiting 3 seconds for file deletions to propagate...")
    time.sleep(3)

    # Now delete all existing stores (should be empty now)
    print("\n🗑️  Deleting all existing stores (now empty)...")
    print("-" * 80)
    try:
        stores = list(service.client.file_search_stores.list())
        print(f"Found {len(stores)} existing store(s)")

        for store in stores:
            print(f"   Deleting store: {store.name}")
            try:
                service.client.file_search_stores.delete(name=store.name)
                print(f"   ✅ Deleted")
            except Exception as e:
                print(f"   ❌ Failed to delete: {e}")
    except Exception as e:
        print(f"❌ Error listing/deleting stores: {e}")

    print("\n⏳ Waiting 2 seconds for store deletions to propagate...")
    time.sleep(2)

    # Create NEW store
    new_store_name = "dmd_clinical_guidelines_v2"
    print(f"\n📦 Creating NEW store: {new_store_name}")
    print("-" * 80)
    try:
        service.store = service.client.file_search_stores.create(
            config={'display_name': new_store_name}
        )
        print(f"✅ Created new store: {service.store.name}\n")
    except Exception as e:
        print(f"❌ ERROR: Failed to create store: {e}")
        return

    # Step 1: Upload guideline files to the new store
    print("STEP 1: Uploading guideline PDFs to new store...")
    print("-" * 80)

    guidelines_dir = Path("data/guidelines")

    # Define the 3 DMD PDFs we want to upload
    files_to_upload = [
        {
            "path": guidelines_dir / "DMD" / "dmd_part1.pdf",
            "display_name": "DMD Part 1 - Diagnosis and Management (Birnkrant 2018)",
            "metadata": {
                "disease_code": "DMD",
                "guideline_type": "management",
                "publication_year": 2018,
                "evidence_level": "Level_A",
                "part": 1,
                "topics": "diagnosis,genetic_testing,newborn_screening",
            }
        },
        {
            "path": guidelines_dir / "DMD" / "DMD-diagnosis-and-management-part-2.pdf",
            "display_name": "DMD Part 2 - Rehabilitation and Therapy (Birnkrant 2018)",
            "metadata": {
                "disease_code": "DMD",
                "guideline_type": "management",
                "publication_year": 2018,
                "evidence_level": "Level_A",
                "part": 2,
                "topics": "rehabilitation,physical_therapy,occupational_therapy",
            }
        },
        {
            "path": guidelines_dir / "DMD" / "DMD-diagnosis-and-management-part-3.pdf",
            "display_name": "DMD Part 3 - Cardiac and Respiratory Care (Birnkrant 2018)",
            "metadata": {
                "disease_code": "DMD",
                "guideline_type": "management",
                "publication_year": 2018,
                "evidence_level": "Level_A",
                "part": 3,
                "topics": "cardiac_care,respiratory_management,gastroenterology",
            }
        },
    ]

    for i, file_info in enumerate(files_to_upload, 1):
        file_path = file_info["path"]
        display_name = file_info["display_name"]
        metadata = file_info["metadata"]

        if not file_path.exists():
            print(f"\n{i}. ❌ File not found: {file_path}")
            continue

        size_mb = file_path.stat().st_size / (1024 * 1024)
        print(f"\n{i}. Uploading: {file_path.name}")
        print(f"   Display name: {display_name}")
        print(f"   Size: {size_mb:.1f} MB")
        print(f"   Metadata: {metadata}")

        try:
            success = service.upload_guideline(
                file_path=str(file_path),
                metadata=metadata,
                display_name=display_name
            )

            if success:
                print(f"   ✅ Uploaded successfully")
            else:
                print(f"   ❌ Upload failed")

        except Exception as e:
            print(f"   ❌ Error: {e}")

    # Step 2: Verify uploads
    print("\n\nSTEP 2: Verifying uploads...")
    print("-" * 80)

    import time
    time.sleep(3)  # Wait for uploads to propagate

    new_files = service.list_uploaded_files()
    print(f"\n📁 Now showing {len(new_files)} files:")

    for i, file in enumerate(new_files, 1):
        print(f"\n{i}. {file.get('name', 'Unknown')}")
        print(f"   ID: {file.get('id', 'Unknown')}")
        size = file.get('size_bytes', 0)
        size_str = f"{size / (1024*1024):.1f} MB" if size else "Unknown"
        print(f"   Size: {size_str}")

    print("\n" + "=" * 80)
    print("✅ CLEANUP AND RE-UPLOAD COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()
