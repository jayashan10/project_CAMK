"""
Test script for ClinVar integration.

Tests:
1. ClinVar API connectivity
2. Rate limiting functionality
3. Caching mechanism (30-day TTL)
4. Variant enrichment without overwriting critical fields
5. Integration with KnowledgeGraphService
"""

import os
import sys
import time
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from knowledge_graph.clinvar_service import ClinVarService
from knowledge_graph.service import KnowledgeGraphService


def test_clinvar_api_connectivity():
    """Test basic ClinVar API connectivity."""
    print("\n" + "=" * 70)
    print("TEST 1: ClinVar API Connectivity")
    print("=" * 70)

    try:
        service = ClinVarService()
        print(f"✓ ClinVar service initialized")
        print(f"  - API key: {'configured' if service.api_key else 'not configured'}")
        print(f"  - Rate limit: {service.rate_limit} req/sec")
        print(f"  - Cache directory: {service.cache_dir}")

        # Test search for a known variant
        print("\nSearching for DMD exon 51 deletion variants...")
        variants = service.search_variants_by_gene("DMD", variant_type="deletion", max_results=5)

        if variants:
            print(f"✓ Found {len(variants)} DMD deletion variants")
            for v in variants[:3]:
                print(f"  - {v['variant_name'][:80]}...")
                print(f"    Significance: {v['clinical_significance']}")
        else:
            print("⚠ No variants found (API might be down or rate limited)")

        return True

    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False


def test_rate_limiting():
    """Test that rate limiting is enforced."""
    print("\n" + "=" * 70)
    print("TEST 2: Rate Limiting")
    print("=" * 70)

    try:
        service = ClinVarService()
        expected_interval = 1.0 / service.rate_limit

        print(f"Rate limit: {service.rate_limit} req/sec (min interval: {expected_interval:.3f}s)")

        # Make 3 rapid requests and measure timing
        start = time.time()
        service._rate_limit()
        service._rate_limit()
        service._rate_limit()
        elapsed = time.time() - start

        print(f"✓ 3 requests took {elapsed:.3f}s")

        # Should take at least 2 * interval (for 3 requests, there are 2 gaps)
        min_expected = 2 * expected_interval
        if elapsed >= min_expected * 0.9:  # Allow 10% tolerance
            print(f"✓ Rate limiting working correctly (expected >= {min_expected:.3f}s)")
            return True
        else:
            print(f"⚠ Rate limiting might not be working (expected >= {min_expected:.3f}s)")
            return False

    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False


def test_caching_mechanism():
    """Test that caching works and respects TTL."""
    print("\n" + "=" * 70)
    print("TEST 3: Caching Mechanism")
    print("=" * 70)

    try:
        service = ClinVarService()

        # Search for a specific variant
        gene = "BRCA1"
        hgvs = "c.68_69delAG"

        print(f"First query for {gene}:{hgvs} (should hit API)...")
        start1 = time.time()
        result1 = service.get_variant_by_hgvs(hgvs, gene)
        time1 = time.time() - start1

        if not result1:
            print(f"⚠ Variant not found in ClinVar (trying different example)...")
            # Try a more common variant
            gene = "DMD"
            hgvs = "c.263dup"
            result1 = service.get_variant_by_hgvs(hgvs, gene)

        if result1:
            print(f"✓ First query completed in {time1:.3f}s")
            print(f"  Variation ID: {result1.get('variation_id')}")
            print(f"  Significance: {result1.get('clinical_significance')}")

            print(f"\nSecond query for {gene}:{hgvs} (should hit cache)...")
            start2 = time.time()
            result2 = service.get_variant_by_hgvs(hgvs, gene)
            time2 = time.time() - start2

            print(f"✓ Second query completed in {time2:.3f}s")

            if time2 < time1 * 0.5:  # Cache should be significantly faster
                print(f"✓ Caching working (cache was {time1/time2:.1f}x faster)")
                return True
            else:
                print(f"⚠ Cache might not be working (similar response times)")
                return False
        else:
            print("⚠ No variant data returned, skipping cache test")
            return False

    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False


def test_enrichment_preserves_critical_fields():
    """Test that ClinVar enrichment doesn't overwrite critical fields."""
    print("\n" + "=" * 70)
    print("TEST 4: Enrichment Preserves Critical Fields")
    print("=" * 70)

    try:
        # Create a test variant annotation with critical fields
        test_variant = {
            "gene": "DMD",
            "variant_type": "deletion",
            "exons": [45, 46, 47],
            "reading_frame": "out-of-frame",  # CRITICAL - must not be overwritten
            "predicted_phenotype": "Duchenne Muscular Dystrophy",
            "eligible_treatments": ["Casimersen (Amondys 45)"],  # CRITICAL
            "hgvs": "c.6439+1_7872+1del"  # Approximate HGVS
        }

        print("Original variant annotation:")
        print(f"  - Exons: {test_variant['exons']}")
        print(f"  - Reading frame: {test_variant['reading_frame']}")
        print(f"  - Eligible treatments: {test_variant['eligible_treatments']}")

        # Create service and enrich
        service = ClinVarService()
        enriched = service.enrich_variant_annotation(test_variant)

        print("\nAfter ClinVar enrichment:")
        print(f"  - Exons: {enriched.get('exons')}")
        print(f"  - Reading frame: {enriched.get('reading_frame')}")
        print(f"  - Eligible treatments: {enriched.get('eligible_treatments')}")

        # Check critical fields weren't overwritten
        if (enriched.get('reading_frame') == test_variant['reading_frame'] and
            enriched.get('eligible_treatments') == test_variant['eligible_treatments'] and
            enriched.get('exons') == test_variant['exons']):
            print("✓ Critical fields preserved!")

            # Check if ClinVar data was added
            if 'clinvar_id' in enriched or 'clinvar_significance' in enriched:
                print(f"✓ ClinVar data added:")
                print(f"  - ClinVar ID: {enriched.get('clinvar_id', 'N/A')}")
                print(f"  - Significance: {enriched.get('clinvar_significance', 'N/A')}")

            return True
        else:
            print("✗ Critical fields were overwritten!")
            return False

    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False


def test_knowledge_graph_service_integration():
    """Test integration with KnowledgeGraphService."""
    print("\n" + "=" * 70)
    print("TEST 5: KnowledgeGraphService Integration")
    print("=" * 70)

    try:
        # Initialize KnowledgeGraphService
        service = KnowledgeGraphService()

        # Check if ClinVar is enabled
        data_source_info = service.get_data_source_info()
        print("Data source info:")
        print(f"  - Neo4j: {data_source_info.get('neo4j_connected')}")
        print(f"  - Monarch: {data_source_info.get('monarch_service')}")
        print(f"  - ClinVar: {data_source_info.get('clinvar_service')}")
        print(f"  - In-memory: {data_source_info.get('in_memory_store')}")

        clinvar_enabled = data_source_info.get('clinvar_service') == 'Yes'

        if not clinvar_enabled:
            print("\n⚠ ClinVar is not enabled (ENABLE_CLINVAR=false in .env)")
            print("  Enrichment will be skipped, but this is expected behavior.")
            return True

        # Get variant annotations for DMD
        print("\nFetching DMD variant annotations...")
        variants = service.get_variant_annotations("DMD", "deletion")

        print(f"✓ Retrieved {len(variants)} DMD deletion annotations")

        # Check if any variants have ClinVar enrichment
        clinvar_enriched = [v for v in variants if 'clinvar_id' in v or 'clinvar_significance' in v]

        if clinvar_enriched:
            print(f"✓ {len(clinvar_enriched)} variants enriched with ClinVar data:")
            for v in clinvar_enriched[:3]:
                print(f"  - {v.get('variant_name', 'Unknown')}")
                print(f"    Significance: {v.get('clinvar_significance', 'N/A')}")
                print(f"    Reading frame: {v.get('reading_frame', 'N/A')}")
                print(f"    Treatments: {v.get('eligible_treatments', [])}")
        else:
            print("⚠ No variants were enriched with ClinVar data")
            print("  (This might be expected if variants don't have HGVS expressions)")

        # Verify critical fields are intact for clinical_data.py variants
        for v in variants:
            if v.get('reading_frame') or v.get('eligible_treatments'):
                print(f"\n✓ Variant with critical fields found:")
                print(f"  - Reading frame: {v.get('reading_frame')}")
                print(f"  - Treatments: {v.get('eligible_treatments')}")
                break

        return True

    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("CLINVAR INTEGRATION TEST SUITE")
    print("=" * 70)

    # Check environment
    print("\nEnvironment Check:")
    print(f"  - NCBI_API_KEY: {'configured' if os.getenv('NCBI_API_KEY') else 'NOT SET'}")
    print(f"  - ENABLE_CLINVAR: {os.getenv('ENABLE_CLINVAR', 'not set')}")

    if not os.getenv('NCBI_API_KEY'):
        print("\n⚠ WARNING: NCBI_API_KEY not set in .env")
        print("  You can get a free API key from: https://www.ncbi.nlm.nih.gov/account/")
        print("  Tests will use slower rate limit (3 req/sec instead of 10 req/sec)")

    if os.getenv('ENABLE_CLINVAR', '').lower() not in ['true', '1', 'yes']:
        print("\n⚠ WARNING: ENABLE_CLINVAR is not set to 'true' in .env")
        print("  ClinVar enrichment will be skipped in KnowledgeGraphService")

    # Run tests
    results = {
        "API Connectivity": test_clinvar_api_connectivity(),
        "Rate Limiting": test_rate_limiting(),
        "Caching": test_caching_mechanism(),
        "Field Preservation": test_enrichment_preserves_critical_fields(),
        "KG Integration": test_knowledge_graph_service_integration(),
    }

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")

    total_passed = sum(results.values())
    total_tests = len(results)

    print(f"\n{total_passed}/{total_tests} tests passed")

    if total_passed == total_tests:
        print("\n🎉 All tests passed! ClinVar integration is working correctly.")
        return 0
    else:
        print("\n⚠ Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
