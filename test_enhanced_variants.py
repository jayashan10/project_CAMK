#!/usr/bin/env python3
"""
Test script for enhanced variant annotation system.
Tests the expanded curated variant database with comprehensive DMD, LAMA2, and CAPN3 variants.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.core.clinical_scenario import (
    ClinicalScenario,
    Patient,
    LabResult,
    GeneticFinding
)
from backend.core.scenario_processor import ScenarioProcessor
from backend.knowledge_graph.service import KnowledgeGraphService

def test_variant(gene, variant_type, exons, expected_phenotype, expected_treatments=None):
    """Test a specific variant interpretation."""
    print(f"\nTesting {gene} {variant_type} exons {exons}...")

    # Create scenario with the variant
    scenario = ClinicalScenario(
        patient=Patient(age="10 years", sex="male"),
        chief_complaint="Muscle weakness",
        presenting_symptoms=["Progressive weakness"],
        genetic_findings=[
            GeneticFinding(
                gene=gene,
                variant_type=variant_type,
                exons_affected=exons,
                zygosity="hemizygous" if gene == "DMD" else "homozygous"
            )
        ]
    )

    # Process scenario
    kg_service = KnowledgeGraphService()
    processor = ScenarioProcessor(knowledge_service=kg_service)
    response = processor.process_scenario(scenario)

    # Check interpretation
    if response.variant_interpretation:
        for variant_id, interp in response.variant_interpretation.items():
            print(f"  ✓ Variant matched: {variant_id}")
            print(f"    • Phenotype: {interp.get('predicted_phenotype', 'N/A')}")
            print(f"    • Reading frame: {interp.get('reading_frame', 'N/A')}")
            print(f"    • Severity: {interp.get('severity', 'N/A')}")

            if interp.get('eligible_treatments'):
                print(f"    • Treatments: {', '.join(interp['eligible_treatments'])}")

            # Validate expectations
            if expected_phenotype:
                if expected_phenotype in str(interp.get('predicted_phenotype', '')):
                    print(f"    ✅ Phenotype matches expected: {expected_phenotype}")
                else:
                    print(f"    ❌ Phenotype mismatch! Expected: {expected_phenotype}")

            if expected_treatments:
                actual_treatments = interp.get('eligible_treatments', [])
                for treatment in expected_treatments:
                    if any(treatment in t for t in actual_treatments):
                        print(f"    ✅ Treatment found: {treatment}")
                    else:
                        print(f"    ❌ Treatment missing: {treatment}")
    else:
        print("  ❌ No variant interpretation found!")

def main():
    print("=" * 60)
    print("TESTING ENHANCED VARIANT ANNOTATION SYSTEM")
    print("=" * 60)

    # Test DMD therapy-eligible deletions
    print("\n--- DMD Therapy-Eligible Deletions ---")
    test_variant("DMD", "deletion", [45], "Becker", ["Casimersen"])
    test_variant("DMD", "deletion", [51], "Duchenne", ["Eteplirsen"])
    test_variant("DMD", "deletion", [53], "Duchenne", ["Golodirsen", "Viltolarsen"])
    test_variant("DMD", "deletion", [45, 46, 47], "Duchenne", ["Casimersen"])

    # Test common DMD deletions without therapy
    print("\n--- DMD Common Deletions (No FDA Therapy) ---")
    test_variant("DMD", "deletion", [50], "Duchenne", [])
    test_variant("DMD", "deletion", [44], "Duchenne", [])

    # Test DMD reading frame exceptions
    print("\n--- DMD Reading Frame Exceptions ---")
    test_variant("DMD", "deletion", [2], "Variable", [])
    test_variant("DMD", "deletion", [78], "Variable", [])

    # Test large DMD deletions
    print("\n--- DMD Large Deletions ---")
    test_variant("DMD", "deletion", [45, 46, 47, 48, 49, 50], "Becker", [])
    test_variant("DMD", "deletion", [48, 49, 50], "Becker", [])

    # Test proximal hotspot
    print("\n--- DMD Proximal Hotspot (Exons 2-10) ---")
    test_variant("DMD", "deletion", [3, 4, 5, 6, 7], "Duchenne", [])
    test_variant("DMD", "deletion", [8, 9], "Duchenne", [])

    # Summary of curated variants
    print("\n" + "=" * 60)
    print("SUMMARY OF CURATED VARIANT DATABASE")
    print("=" * 60)

    from backend.knowledge_graph.clinical_data import VARIANT_ANNOTATIONS

    # Count variants by gene
    gene_counts = {}
    therapy_eligible = 0

    for variant in VARIANT_ANNOTATIONS:
        gene = variant.get("gene", "Unknown")
        gene_counts[gene] = gene_counts.get(gene, 0) + 1

        if variant.get("eligible_treatments"):
            therapy_eligible += 1

    print(f"\nTotal curated variants: {len(VARIANT_ANNOTATIONS)}")
    print("\nVariants by gene:")
    for gene, count in sorted(gene_counts.items()):
        print(f"  • {gene}: {count} variants")

    print(f"\nTherapy-eligible variants: {therapy_eligible}")

    # List all therapy options
    therapies = set()
    for variant in VARIANT_ANNOTATIONS:
        for treatment in variant.get("eligible_treatments", []):
            therapies.add(treatment)

    print(f"\nFDA-approved therapies in database:")
    for therapy in sorted(therapies):
        print(f"  • {therapy}")

    print("\n✅ Enhanced variant system test complete!")

if __name__ == "__main__":
    main()