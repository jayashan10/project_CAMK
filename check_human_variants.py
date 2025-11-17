#!/usr/bin/env python3
"""
Check for HUMAN sequence variants in Monarch database.
"""

import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "monarch")


def check_human_variants():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    driver.verify_connectivity()
    print("✓ Connected to Monarch database\n")

    with driver.session(database=NEO4J_DATABASE) as session:
        # 1. Count HUMAN variants
        print("=" * 80)
        print("1. HUMAN SEQUENCE VARIANTS")
        print("=" * 80)
        result = session.run("""
            MATCH (v:`biolink:SequenceVariant`)
            WHERE v.in_taxon = 'NCBITaxon:9606' OR v.in_taxon_label = 'Homo sapiens'
            RETURN count(v) as count
        """)
        count = result.single()['count']
        print(f"Human SequenceVariant nodes: {count:,}\n")

        if count == 0:
            print("No HUMAN variant nodes found!")
            print("\nLet's check variant counts by species...")

            result = session.run("""
                MATCH (v:`biolink:SequenceVariant`)
                WITH v.in_taxon_label as species, count(v) as cnt
                RETURN species, cnt
                ORDER BY cnt DESC
                LIMIT 10
            """)

            print("\nVariant counts by species:")
            for record in result:
                print(f"  {record['species']}: {record['cnt']:,}")

            driver.close()
            return

        # 2. Sample human variants
        print("=" * 80)
        print("2. SAMPLE HUMAN VARIANTS")
        print("=" * 80)
        result = session.run("""
            MATCH (v:`biolink:SequenceVariant`)
            WHERE v.in_taxon = 'NCBITaxon:9606'
            RETURN v
            LIMIT 10
        """)

        for i, record in enumerate(result, 1):
            variant = dict(record['v'])
            print(f"\nVariant {i}:")
            for key, value in variant.items():
                str_value = str(value)
                if len(str_value) > 150:
                    str_value = str_value[:150] + "..."
                print(f"  {key}: {str_value}")

        # 3. Check human variant relationships to genes
        print("\n" + "=" * 80)
        print("3. HUMAN VARIANT-GENE ASSOCIATIONS")
        print("=" * 80)
        result = session.run("""
            MATCH (v:`biolink:SequenceVariant`)-[:`biolink:is_sequence_variant_of`]->(g:`biolink:Gene`)
            WHERE v.in_taxon = 'NCBITaxon:9606'
            AND g.in_taxon = 'NCBITaxon:9606'
            WITH g.symbol as gene_symbol, count(v) as variant_count
            RETURN gene_symbol, variant_count
            ORDER BY variant_count DESC
            LIMIT 20
        """)

        print("Genes with most human variants:")
        for record in result:
            print(f"  {record['gene_symbol']}: {record['variant_count']:,} variants")

        # 4. Look specifically for DMD variants
        print("\n" + "=" * 80)
        print("4. DMD GENE VARIANTS (HUMAN)")
        print("=" * 80)
        result = session.run("""
            MATCH (v:`biolink:SequenceVariant`)-[:`biolink:is_sequence_variant_of`]->(g:`biolink:Gene`)
            WHERE g.symbol = 'DMD'
            AND g.in_taxon = 'NCBITaxon:9606'
            AND v.in_taxon = 'NCBITaxon:9606'
            RETURN v.id as variant_id, v.name as variant_name,
                   properties(v) as props
            LIMIT 20
        """)

        variants = [dict(r) for r in result]
        if variants:
            print(f"Found {len(variants)} human DMD variants:")
            for v in variants:
                print(f"\n  ID: {v['variant_id']}")
                print(f"  Name: {v.get('variant_name', 'N/A')}")
                print(f"  Properties: {v['props']}")
        else:
            print("No human DMD variants found.")

        # 5. Check variant-disease associations
        print("\n" + "=" * 80)
        print("5. VARIANT-DISEASE ASSOCIATIONS (HUMAN)")
        print("=" * 80)
        result = session.run("""
            MATCH (v:`biolink:SequenceVariant`)-[r]->(d:`biolink:Disease`)
            WHERE v.in_taxon = 'NCBITaxon:9606'
            WITH type(r) as relationship, count(*) as cnt
            RETURN relationship, cnt
            ORDER BY cnt DESC
        """)

        print("Human variant -> disease relationships:")
        for record in result:
            print(f"  {record['relationship']}: {record['cnt']:,}")

        # Sample some variant-disease associations
        result = session.run("""
            MATCH (v:`biolink:SequenceVariant`)-[r:`biolink:causes`]->(d:`biolink:Disease`)
            WHERE v.in_taxon = 'NCBITaxon:9606'
            RETURN v.id as variant_id, v.name as variant_name,
                   d.id as disease_id, d.name as disease_name
            LIMIT 10
        """)

        print("\nSample variant-disease associations:")
        for record in result:
            print(f"  {record['variant_name']} ({record['variant_id']})")
            print(f"    -> causes -> {record['disease_name']} ({record['disease_id']})")

        # 6. Look for muscular dystrophy related variants
        print("\n" + "=" * 80)
        print("6. MUSCULAR DYSTROPHY VARIANTS")
        print("=" * 80)
        result = session.run("""
            MATCH (v:`biolink:SequenceVariant`)-[r]->(d:`biolink:Disease`)
            WHERE v.in_taxon = 'NCBITaxon:9606'
            AND toLower(d.name) CONTAINS 'muscular dystrophy'
            RETURN v.id as variant_id, v.name as variant_name,
                   type(r) as relationship,
                   d.id as disease_id, d.name as disease_name
            LIMIT 20
        """)

        variants = [dict(r) for r in result]
        if variants:
            print(f"Found {len(variants)} muscular dystrophy variants:")
            for v in variants:
                print(f"\n  Variant: {v.get('variant_name', 'N/A')} ({v['variant_id']})")
                print(f"  {v['relationship']} -> {v['disease_name']} ({v['disease_id']})")
        else:
            print("No muscular dystrophy variants found.")

    driver.close()


if __name__ == "__main__":
    check_human_variants()
