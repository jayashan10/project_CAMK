"""
Clinical guideline upload script for Gemini File Search.

This script batch uploads clinical guidelines (PDFs) to Google Gemini File Search
with rich metadata for semantic retrieval. Guidelines are organized by disease type
and include evidence levels, publication years, and guideline types.

Usage:
    python backend/rag/upload_guidelines.py [--dry-run]

Prerequisites:
    - GOOGLE_API_KEY set in .env file
    - Clinical guideline PDFs placed in data/guidelines/ directory
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.rag.gemini_file_search import GeminiFileSearchService

# Base directory for clinical guidelines
GUIDELINES_DIR = project_root / "data" / "guidelines"

# Guideline metadata definitions
# NOTE: User should place corresponding PDF files in the specified paths
GUIDELINE_METADATA = {
    # Duchenne Muscular Dystrophy (DMD) Guidelines
    # NOTE: Using actual uploaded filenames
    "DMD/dmd_part1.pdf": {
        "disease_code": "DMD",
        "guideline_type": "management",
        "publication_year": 2018,
        "evidence_level": "Level_A",
        "part": 1,
        "topics": "diagnosis,genetic_testing,newborn_screening",
        "organization": "DMD_Care_Considerations_Working_Group",
        "journal": "Lancet_Neurology",
    },
    "DMD/DMD-diagnosis-and-management-part-2.pdf": {
        "disease_code": "DMD",
        "guideline_type": "management",
        "publication_year": 2018,
        "evidence_level": "Level_A",
        "part": 2,
        "topics": "rehabilitation,physical_therapy,occupational_therapy",
        "organization": "DMD_Care_Considerations_Working_Group",
        "journal": "Lancet_Neurology",
    },
    "DMD/DMD-diagnosis-and-management-part-3.pdf": {
        "disease_code": "DMD",
        "guideline_type": "management",
        "publication_year": 2018,
        "evidence_level": "Level_A",
        "part": 3,
        "topics": "cardiac_care,respiratory_management,gastroenterology",
        "organization": "DMD_Care_Considerations_Working_Group",
        "journal": "Lancet_Neurology",
    },
    "DMD/treat_nmd_dmd_corticosteroids.pdf": {
        "disease_code": "DMD",
        "guideline_type": "standards_of_care",
        "publication_year": 2020,
        "evidence_level": "Level_A",
        "topics": "corticosteroids,prednisone,deflazacort,dosing",
        "organization": "TREAT-NMD",
    },
    "DMD/fda_eteplirsen_approval_2016.pdf": {
        "disease_code": "DMD",
        "guideline_type": "fda_approval",
        "publication_year": 2016,
        "therapy_type": "exon_skipping",
        "drug_name": "Eteplirsen",
        "brand_name": "Exondys_51",
        "target_exon": 51,
        "topics": "exon_51_deletion,mutation_amenable",
    },
    "DMD/fda_casimersen_approval_2021.pdf": {
        "disease_code": "DMD",
        "guideline_type": "fda_approval",
        "publication_year": 2021,
        "therapy_type": "exon_skipping",
        "drug_name": "Casimersen",
        "brand_name": "Amondys_45",
        "target_exon": 45,
        "topics": "exon_45_deletion,mutation_amenable",
    },
    "DMD/fda_golodirsen_approval_2019.pdf": {
        "disease_code": "DMD",
        "guideline_type": "fda_approval",
        "publication_year": 2019,
        "therapy_type": "exon_skipping",
        "drug_name": "Golodirsen",
        "brand_name": "Vyondys_53",
        "target_exon": 53,
        "topics": "exon_53_deletion,mutation_amenable",
    },
    # Becker Muscular Dystrophy (BMD) Guidelines
    "BMD/bmd_cardiac_surveillance_guidelines.pdf": {
        "disease_code": "BMD",
        "guideline_type": "management",
        "topics": "cardiac_surveillance,echocardiography,arrhythmia",
    },
    # Variant Interpretation Guidelines
    "variant_interpretation/acmg_2015_standards.pdf": {
        "guideline_type": "variant_interpretation",
        "publication_year": 2015,
        "standard": "ACMG_AMP",
        "organization": "ACMG",
        "topics": "variant_classification,pathogenicity,VUS,PP,PM,PVS",
    },
    "variant_interpretation/genereviews_dystrophinopathies.pdf": {
        "disease_code": "DMD_BMD",
        "guideline_type": "clinical_review",
        "organization": "GeneReviews_NCBI",
        "topics": "genotype_phenotype,genetic_counseling,carrier_testing",
    },
    # Limb-Girdle MD (LGMD) Guidelines
    "LGMD/lgmdr1_clinical_overview.pdf": {
        "disease_code": "LGMDR1",
        "guideline_type": "clinical_overview",
        "topics": "calpainopathy,CAPN3,differential_diagnosis",
    },
    # General Guidelines
    "general/genetic_counseling_x_linked.pdf": {
        "guideline_type": "genetic_counseling",
        "inheritance": "X_linked",
        "topics": "carrier_screening,prenatal_testing,family_planning",
    },
}

# Optional: Define guideline availability status
# Set to True for guidelines you have already acquired
GUIDELINE_AVAILABILITY = {
    path: False  # Set to True when you have the PDF
    for path in GUIDELINE_METADATA.keys()
}


def upload_all_guidelines(dry_run: bool = False, force: bool = False):
    """
    Upload all clinical guidelines with metadata to Gemini File Search.

    Args:
        dry_run: If True, print what would be uploaded without actually uploading.
        force: If True, upload all guidelines regardless of availability status.
    """
    print("=" * 70)
    print("CLINICAL GUIDELINE UPLOAD TO GEMINI FILE SEARCH")
    print("=" * 70)

    # Initialize service
    service = GeminiFileSearchService()

    if not service.client:
        print("❌ ERROR: Gemini client not initialized.")
        print("   Please set GOOGLE_API_KEY in your .env file.")
        print("   You can get a free API key from: https://aistudio.google.com/app/apikey")
        return False

    # Initialize File Search store
    print("\n📦 Initializing File Search store...")
    if not service.initialize_store("md_clinical_guidelines"):
        print("❌ ERROR: Failed to initialize File Search store.")
        return False

    print(f"✅ File Search store ready: {service.store.name}")

    # Upload guidelines
    print(f"\n📁 Scanning guidelines directory: {GUIDELINES_DIR}")
    print(f"   Found {len(GUIDELINE_METADATA)} guideline definitions\n")

    uploaded_count = 0
    skipped_count = 0
    error_count = 0

    for relative_path, metadata in GUIDELINE_METADATA.items():
        file_path = GUIDELINES_DIR / relative_path

        # Check if file exists
        if not file_path.exists():
            if not force and not GUIDELINE_AVAILABILITY.get(relative_path, False):
                print(f"⏭️  SKIP: {relative_path}")
                print(f"    File not found (mark as available when acquired)")
                skipped_count += 1
                continue
            else:
                print(f"❌ ERROR: {relative_path}")
                print(f"    File not found: {file_path}")
                error_count += 1
                continue

        # Dry run mode
        if dry_run:
            print(f"🔍 DRY-RUN: Would upload {relative_path}")
            print(f"    Metadata: {metadata}")
            continue

        # Upload guideline
        print(f"📤 Uploading: {relative_path}")
        success = service.upload_guideline(
            file_path=str(file_path), metadata=metadata, display_name=file_path.name
        )

        if success:
            print(f"✅ SUCCESS: {relative_path}")
            uploaded_count += 1
        else:
            print(f"❌ ERROR: Failed to upload {relative_path}")
            error_count += 1

    # Summary
    print("\n" + "=" * 70)
    print("UPLOAD SUMMARY")
    print("=" * 70)
    if dry_run:
        print(f"Dry run mode - no files uploaded")
        print(f"  Available: {len([p for p, avail in GUIDELINE_AVAILABILITY.items() if avail or (GUIDELINES_DIR / p).exists()])}")
        print(f"  Missing:   {skipped_count}")
    else:
        print(f"  Uploaded:  {uploaded_count}")
        print(f"  Skipped:   {skipped_count}")
        print(f"  Errors:    {error_count}")

    if uploaded_count > 0:
        print(f"\n🎉 Successfully uploaded {uploaded_count} clinical guidelines!")
        print(f"   You can now query these guidelines using the GeminiFileSearchService")

    if skipped_count > 0:
        print(f"\n📋 Next steps:")
        print(f"   1. Acquire missing guideline PDFs (see GUIDELINE_METADATA for list)")
        print(f"   2. Place PDFs in data/guidelines/ directory")
        print(f"   3. Run this script again to upload remaining guidelines")

    return uploaded_count > 0


def list_uploaded_guidelines():
    """List all guidelines currently uploaded to Gemini File Search."""
    print("=" * 70)
    print("UPLOADED GUIDELINES")
    print("=" * 70)

    service = GeminiFileSearchService()
    if not service.client:
        print("❌ ERROR: Gemini client not initialized.")
        return

    if not service.initialize_store("md_clinical_guidelines"):
        print("❌ ERROR: Failed to initialize File Search store.")
        return

    files = service.list_uploaded_files()

    if not files:
        print("No guidelines uploaded yet.")
        return

    print(f"Found {len(files)} uploaded guidelines:\n")
    for idx, file in enumerate(files, 1):
        size_mb = file.get("size", 0) / (1024 * 1024)
        print(f"{idx}. {file['name']}")
        print(f"   Size: {size_mb:.2f} MB")
        print(f"   ID: {file['id']}")
        print()


def main():
    """Main entry point for guideline upload script."""
    parser = argparse.ArgumentParser(description="Upload clinical guidelines to Gemini File Search")

    parser.add_argument("--dry-run", action="store_true", help="Preview upload without actually uploading")

    parser.add_argument("--force", action="store_true", help="Upload all guidelines, including missing ones (will error)")

    parser.add_argument("--list", action="store_true", help="List currently uploaded guidelines")

    args = parser.parse_args()

    if args.list:
        list_uploaded_guidelines()
    else:
        upload_all_guidelines(dry_run=args.dry_run, force=args.force)


if __name__ == "__main__":
    main()
