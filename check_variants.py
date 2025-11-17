#!/usr/bin/env python3
"""
Check if SequenceVariant nodes are populated in Monarch database.
"""

import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "monarch")


def check_variants():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    driver.verify_connectivity()
    print("✓ Connected to Monarch database\n")

    with driver.session(database=NEO4J_DATABASE) as session:
        # 1. Count SequenceVariant nodes
        print("=" * 80)
        print("1. COUNTING SEQUENCE VARIANT NODES")
        print("=" * 80)
        result = session.run("""
            MATCH (v:`biolink:SequenceVariant`)
            RETURN count(v) as count
        """)
        count = result.single()['count']
        print(f"Total SequenceVariant nodes: {count:,}\n")

        if count == 0:
            print("No variant nodes found.")
            driver.close()
            return

        # 2. Sample some variants
        print("=" * 80)
        print("2. SAMPLE SEQUENCE VARIANTS")
        print("=" * 80)
        result = session.run("""
            MATCH (v:`biolink:SequenceVariant`)
            RETURN v
            LIMIT 10
        """)

        for i, record in enumerate(result, 1):
            variant = dict(record['v'])
            print(f"\nVariant {i}:")
            for key, value in variant.items():
                str_value = str(value)
                if len(str_value) > 100:
                    str_value = str_value[:100] + "..."
                print(f"  {key}: {str_value}")

        # 3. Check variant properties
        print("\n" + "=" * 80)
        print("3. VARIANT PROPERTY KEYS")
        print("=" * 80)
        result = session.run("""
            MATCH (v:`biolink:SequenceVariant`)
            WITH v LIMIT 100
            UNWIND keys(v) as key
            RETURN DISTINCT key ORDER BY key
        """)

        props = [r['key'] for r in result]
        print("Property keys found:")
        for prop in props:
            print(f"  - {prop}")

        # 4. Check variant relationships
        print("\n" + "=" * 80)
        print("4. VARIANT RELATIONSHIPS")
        print("=" * 80)
        result = session.run("""
            MATCH (v:`biolink:SequenceVariant`)-[r]->(target)
            WITH type(r) as relType, labels(target) as targetLabels, count(*) as cnt
            RETURN relType, targetLabels, cnt
            ORDER BY cnt DESC
            LIMIT 10
        """)

        print("Outgoing relationships:")
        for record in result:
            print(f"  {record['relType']} -> {record['targetLabels']}: {record['cnt']:,}")

        # 5. Look for DMD gene variants specifically
        print("\n" + "=" * 80)
        print("5. VARIANTS FOR DMD GENE")
        print("=" * 80)
        result = session.run("""
            MATCH (g:`biolink:Gene`)-[r]-(v:`biolink:SequenceVariant`)
            WHERE g.symbol = 'DMD' OR g.id CONTAINS 'DMD'
            RETURN g.id as gene_id, g.symbol as symbol,
                   type(r) as relationship,
                   v.id as variant_id, v.name as variant_name
            LIMIT 20
        """)

        variants = [dict(r) for r in result]
        if variants:
            print(f"Found {len(variants)} DMD variants:")
            for v in variants:
                print(f"  Gene: {v['symbol']} ({v['gene_id']})")
                print(f"    Variant: {v.get('variant_name', 'N/A')} ({v['variant_id']})")
                print(f"    Relationship: {v['relationship']}")
        else:
            print("No variants found for DMD gene.")

            # Try broader search
            print("\nTrying broader search for human DMD gene...")
            result = session.run("""
                MATCH (g:`biolink:Gene`)
                WHERE g.symbol = 'DMD'
                AND (g.in_taxon = 'NCBITaxon:9606' OR g.in_taxon_label = 'Homo sapiens')
                RETURN g.id as gene_id, g.symbol as symbol
            """)
            gene = result.single()
            if gene:
                print(f"Found gene: {gene['symbol']} ({gene['gene_id']})")

                # Check all relationships for this gene
                result = session.run("""
                    MATCH (g:`biolink:Gene` {id: $gene_id})-[r]->(target)
                    WITH type(r) as relType, labels(target) as targetLabels, count(*) as cnt
                    RETURN relType, targetLabels, cnt
                    ORDER BY cnt DESC
                """, {"gene_id": gene['gene_id']})

                print("\nAll outgoing relationships from DMD gene:")
                for record in result:
                    print(f"  {record['relType']} -> {record['targetLabels']}: {record['cnt']:,}")

        # 6. Sample variant with all details
        print("\n" + "=" * 80)
        print("6. DETAILED VARIANT EXAMPLE")
        print("=" * 80)
        result = session.run("""
            MATCH (v:`biolink:SequenceVariant`)
            OPTIONAL MATCH (v)-[r1]->(gene:`biolink:Gene`)
            OPTIONAL MATCH (v)-[r2]->(disease:`biolink:Disease`)
            RETURN v,
                   collect(DISTINCT {gene: gene.symbol, gene_id: gene.id, rel: type(r1)}) as genes,
                   collect(DISTINCT {disease: disease.name, disease_id: disease.id, rel: type(r2)}) as diseases
            LIMIT 1
        """)

        record = result.single()
        if record:
            variant = dict(record['v'])
            print("Variant properties:")
            for key, value in variant.items():
                print(f"  {key}: {value}")

            print("\nAssociated genes:")
            for gene in record['genes']:
                if gene['gene']:
                    print(f"  {gene['gene']} ({gene['gene_id']}) via {gene['rel']}")

            print("\nAssociated diseases:")
            for disease in record['diseases']:
                if disease['disease']:
                    print(f"  {disease['disease']} ({disease['disease_id']}) via {disease['rel']}")

    driver.close()


if __name__ == "__main__":
    check_variants()
