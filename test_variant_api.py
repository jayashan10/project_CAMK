#!/usr/bin/env python3
"""
Test script for variant API endpoints with real ClinVar integration.
Demonstrates how the API queries NCBI ClinVar API using the NCBI_API_KEY from .env
"""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_BASE = "http://localhost:8000/api"


def test_health():
    """Test health check endpoint."""
    print("\n" + "=" * 60)
    print("1. HEALTH CHECK")
    print("=" * 60)

    response = requests.get("http://localhost:8000/health")
    data = response.json()

    print(f"Status: {data['status']}")
    print(f"Service: {data['service']}")
    print(f"\nData Sources:")
    for key, value in data['data_source'].items():
        print(f"  • {key}: {value}")


def test_interpret_variant():
    """Test variant interpretation with ClinVar lookup."""
    print("\n" + "=" * 60)
    print("2. VARIANT INTERPRETATION (Curated + ClinVar)")
    print("=" * 60)

    # Test DMD deletion exons 45-47
    query = {
        "gene": "DMD",
        "exons": [45, 46, 47],
        "variant_type": "deletion"
    }

    print(f"\nQuery: {json.dumps(query, indent=2)}")
    print(f"\nCalling: POST {API_BASE}/variants/interpret")

    response = requests.post(f"{API_BASE}/variants/interpret", json=query)

    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ SUCCESS")
        print(f"\nGene: {data['gene']}")
        print(f"Exons: {data['exons']}")
        print(f"Variant Type: {data['variant_type']}")

        print(f"\n📊 CURATED CLINICAL DATA:")
        clinical = data['clinical_data']
        print(f"  • Reading Frame: {clinical['reading_frame']}")
        print(f"  • Phenotype: {clinical['predicted_phenotype']}")
        print(f"  • Severity: {clinical['severity']}")
        print(f"  • Eligible Treatments:")
        for treatment in clinical['eligible_treatments']:
            print(f"    - {treatment}")
        if clinical.get('notes'):
            print(f"  • Notes: {clinical['notes']}")

        if data.get('clinvar_data'):
            print(f"\n🔬 CLINVAR REFERENCE DATA:")
            clinvar = data['clinvar_data']
            print(f"  • ClinVar ID: {clinvar.get('clinvar_id', 'N/A')}")
            print(f"  • Significance: {clinvar.get('clinical_significance', 'N/A')}")
            print(f"  • Review Status: {clinvar.get('review_status', 'N/A')}")
            print(f"  • Submitters: {clinvar.get('submitter_count', 'N/A')}")
            if clinvar.get('url'):
                print(f"  • URL: {clinvar['url']}")
        else:
            print(f"\n⚠️ ClinVar data not available (ENABLE_CLINVAR may be false)")

    else:
        print(f"\n❌ FAILED: {response.status_code}")
        print(response.text)


def test_search_variants():
    """Test searching all variants for a gene."""
    print("\n" + "=" * 60)
    print("3. SEARCH VARIANTS BY GENE")
    print("=" * 60)

    gene = "DMD"
    print(f"\nSearching gene: {gene}")
    print(f"Calling: GET {API_BASE}/variants/search/{gene}")

    response = requests.get(f"{API_BASE}/variants/search/{gene}?variant_type=deletion")

    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ SUCCESS")
        print(f"\nGene: {data['gene']}")
        print(f"Variant Count: {data['variant_count']}")
        print(f"ClinVar Enabled: {data['clinvar_enabled']}")
        print(f"Data Sources: {', '.join(data['data_sources'])}")

        print(f"\n📋 VARIANTS (showing first 5):")
        for variant in data['variants'][:5]:
            print(f"\n  Variant: {variant['gene']} {variant['variant_type']}")
            if variant.get('exons'):
                print(f"  Exons: {variant['exons']}")
            print(f"  Phenotype: {variant['clinical_data']['predicted_phenotype']}")
            print(f"  Severity: {variant['clinical_data']['severity']}")

            treatments = variant['clinical_data']['eligible_treatments']
            if treatments:
                print(f"  Treatments: {', '.join(treatments)}")

            if variant.get('clinvar_data'):
                print(f"  ClinVar: {variant['clinvar_data'].get('clinical_significance', 'N/A')}")

    else:
        print(f"\n❌ FAILED: {response.status_code}")
        print(response.text)


def test_clinvar_direct():
    """Test direct ClinVar API query (no curated data)."""
    print("\n" + "=" * 60)
    print("4. DIRECT CLINVAR API QUERY (Showcase)")
    print("=" * 60)

    clinvar_enabled = os.getenv("ENABLE_CLINVAR", "false").lower() in ("true", "1", "yes")

    if not clinvar_enabled:
        print("\n⚠️ SKIPPED: ClinVar is disabled (ENABLE_CLINVAR=false)")
        print("   To enable: Set ENABLE_CLINVAR=true in .env")
        return

    gene = "DMD"
    max_results = 5

    print(f"\nQuerying ClinVar for gene: {gene}")
    print(f"Max results: {max_results}")
    print(f"Calling: GET {API_BASE}/variants/clinvar/gene/{gene}")

    response = requests.get(f"{API_BASE}/variants/clinvar/gene/{gene}?max_results={max_results}")

    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ SUCCESS")
        print(f"\nSource: {data['source']}")
        print(f"Gene: {data['gene']}")
        print(f"Variant Count: {data['variant_count']}")

        print(f"\n🔬 RAW CLINVAR RESULTS (first 3):")
        for i, variant in enumerate(data['variants'][:3], 1):
            print(f"\n  [{i}] ClinVar ID: {variant.get('clinvar_id', 'N/A')}")
            print(f"      Significance: {variant.get('clinical_significance', 'N/A')}")
            print(f"      Review Status: {variant.get('review_status', 'N/A')}")
            if variant.get('phenotypes'):
                print(f"      Phenotypes: {', '.join(variant['phenotypes'][:2])}")

    elif response.status_code == 503:
        print(f"\n⚠️ ClinVar is disabled")
        print(response.json())
    else:
        print(f"\n❌ FAILED: {response.status_code}")
        print(response.text)


def test_fda_therapies():
    """Test listing FDA-approved therapies."""
    print("\n" + "=" * 60)
    print("5. FDA-APPROVED THERAPIES")
    print("=" * 60)

    print(f"Calling: GET {API_BASE}/variants/therapies")

    response = requests.get(f"{API_BASE}/variants/therapies")

    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ SUCCESS")
        print(f"\nTotal Therapies: {data['therapy_count']}")

        print(f"\n💊 THERAPIES:")
        for therapy in data['therapies']:
            print(f"\n  • {therapy['name']}")
            print(f"    Gene: {therapy['gene']}")
            print(f"    Eligible Variants: {therapy['variant_count']}")
            if therapy.get('eligible_exons'):
                exon_list = ', '.join([str(e) if isinstance(e, int) else str(e) for e in therapy['eligible_exons'][:3]])
                print(f"    Example Exons: {exon_list}")

    else:
        print(f"\n❌ FAILED: {response.status_code}")
        print(response.text)


def main():
    """Run all API tests."""
    print("\n" + "=" * 60)
    print("VARIANT API TEST SUITE")
    print("Testing real ClinVar API integration")
    print("=" * 60)

    # Check if server is running
    try:
        requests.get("http://localhost:8000/health", timeout=2)
    except requests.exceptions.RequestException:
        print("\n❌ ERROR: API server is not running!")
        print("\nTo start the server:")
        print("  uv run uvicorn backend.api.main:app --reload")
        print("\nOr:")
        print("  uvicorn backend.api.main:app --reload")
        return

    # Check environment
    print(f"\n🔧 Environment:")
    print(f"  ENABLE_CLINVAR: {os.getenv('ENABLE_CLINVAR', 'false')}")
    api_key_set = "yes" if os.getenv('NCBI_API_KEY') else "no"
    print(f"  NCBI_API_KEY: {api_key_set}")

    if os.getenv('ENABLE_CLINVAR', 'false').lower() not in ('true', '1', 'yes'):
        print(f"\n⚠️ WARNING: ClinVar is disabled")
        print(f"   To enable: Set ENABLE_CLINVAR=true in .env")

    # Run tests
    test_health()
    test_interpret_variant()
    test_search_variants()
    test_clinvar_direct()
    test_fda_therapies()

    print("\n" + "=" * 60)
    print("✅ TEST SUITE COMPLETE")
    print("=" * 60)
    print(f"\nAPI Documentation: http://localhost:8000/docs")
    print(f"Alternative Docs: http://localhost:8000/redoc")


if __name__ == "__main__":
    main()
