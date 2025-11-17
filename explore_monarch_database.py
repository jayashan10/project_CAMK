#!/usr/bin/env python3
"""
Comprehensive exploration of the Monarch Initiative Neo4j database.
This script systematically explores the database schema and content.
"""

import os
import json
from neo4j import GraphDatabase
from dotenv import load_dotenv
from collections import defaultdict
from typing import Dict, List, Any

# Load environment variables
load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://127.0.0.1:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "monarch")


class MonarchExplorer:
    """Explorer for Monarch Initiative database."""

    def __init__(self):
        """Initialize database connection."""
        print(f"Connecting to {NEO4J_URI}, database: {NEO4J_DATABASE}...")
        self.driver = GraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USER, NEO4J_PASSWORD)
        )
        self.driver.verify_connectivity()
        print("✓ Connected successfully!\n")

    def close(self):
        """Close database connection."""
        self.driver.close()

    def run_query(self, query: str, params: Dict = None) -> List[Dict]:
        """Execute a Cypher query and return results."""
        with self.driver.session(database=NEO4J_DATABASE) as session:
            result = session.run(query, params or {})
            return [dict(record) for record in result]

    def explore_schema(self) -> Dict[str, Any]:
        """Explore database schema - node labels and relationship types."""
        print("=" * 80)
        print("EXPLORING DATABASE SCHEMA")
        print("=" * 80)

        schema_info = {}

        # Get all node labels
        print("\n1. NODE LABELS:")
        print("-" * 80)
        query = "CALL db.labels() YIELD label RETURN label ORDER BY label"
        labels = self.run_query(query)
        schema_info['node_labels'] = [r['label'] for r in labels]

        for label in schema_info['node_labels']:
            print(f"  - {label}")
        print(f"\nTotal node labels: {len(schema_info['node_labels'])}")

        # Get all relationship types
        print("\n2. RELATIONSHIP TYPES:")
        print("-" * 80)
        query = "CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType ORDER BY relationshipType"
        rel_types = self.run_query(query)
        schema_info['relationship_types'] = [r['relationshipType'] for r in rel_types]

        for rel_type in schema_info['relationship_types']:
            print(f"  - {rel_type}")
        print(f"\nTotal relationship types: {len(schema_info['relationship_types'])}")

        # Get node counts by label
        print("\n3. NODE COUNTS BY LABEL:")
        print("-" * 80)
        schema_info['node_counts'] = {}
        for label in schema_info['node_labels'][:20]:  # Limit to first 20 for speed
            query = f"MATCH (n:`{label}`) RETURN count(n) as count"
            result = self.run_query(query)
            count = result[0]['count'] if result else 0
            schema_info['node_counts'][label] = count
            print(f"  {label}: {count:,}")

        # Get relationship counts by type
        print("\n4. RELATIONSHIP COUNTS BY TYPE:")
        print("-" * 80)
        schema_info['relationship_counts'] = {}
        for rel_type in schema_info['relationship_types'][:20]:  # Limit to first 20
            query = f"MATCH ()-[r:`{rel_type}`]->() RETURN count(r) as count"
            result = self.run_query(query)
            count = result[0]['count'] if result else 0
            schema_info['relationship_counts'][rel_type] = count
            print(f"  {rel_type}: {count:,}")

        return schema_info

    def explore_node_properties(self, label: str, limit: int = 5) -> Dict[str, Any]:
        """Explore properties of nodes with a given label."""
        print(f"\n{'=' * 80}")
        print(f"EXPLORING {label} NODES")
        print("=" * 80)

        node_info = {'label': label, 'properties': {}, 'sample_nodes': []}

        # Get property keys for this label
        query = f"""
        MATCH (n:`{label}`)
        WITH n LIMIT 100
        UNWIND keys(n) as key
        RETURN DISTINCT key ORDER BY key
        """
        props = self.run_query(query)
        node_info['property_keys'] = [p['key'] for p in props]

        print(f"\nProperty keys for {label}:")
        for key in node_info['property_keys']:
            print(f"  - {key}")

        # Get sample nodes
        query = f"""
        MATCH (n:`{label}`)
        RETURN n LIMIT {limit}
        """
        samples = self.run_query(query)

        print(f"\nSample {label} nodes:")
        print("-" * 80)
        for i, record in enumerate(samples, 1):
            node = dict(record['n'])
            node_info['sample_nodes'].append(node)
            print(f"\nNode {i}:")
            for key, value in node.items():
                # Truncate long values
                str_value = str(value)
                if len(str_value) > 100:
                    str_value = str_value[:100] + "..."
                print(f"  {key}: {str_value}")

        return node_info

    def explore_disease_phenotype_associations(self) -> Dict[str, Any]:
        """Explore disease-phenotype associations."""
        print(f"\n{'=' * 80}")
        print("EXPLORING DISEASE-PHENOTYPE ASSOCIATIONS")
        print("=" * 80)

        assoc_info = {}

        # Find disease-phenotype relationship patterns
        query = """
        MATCH (d)-[r]->(p)
        WHERE (d:Disease OR d:`biolink:Disease` OR d:NamedThing)
        AND (p:Phenotype OR p:`biolink:PhenotypicFeature` OR p:NamedThing)
        WITH type(r) as relType, labels(d) as dLabels, labels(p) as pLabels, count(*) as cnt
        RETURN relType, dLabels, pLabels, cnt
        ORDER BY cnt DESC
        LIMIT 10
        """
        patterns = self.run_query(query)

        print("\nDisease-Phenotype relationship patterns:")
        print("-" * 80)
        for pattern in patterns:
            print(f"  {pattern['dLabels']} -[{pattern['relType']}]-> {pattern['pLabels']}: {pattern['cnt']:,} associations")

        assoc_info['patterns'] = patterns

        # Get sample associations
        query = """
        MATCH (d)-[r]->(p)
        WHERE (d:Disease OR d:`biolink:Disease`)
        AND (p:Phenotype OR p:`biolink:PhenotypicFeature`)
        RETURN d.id as disease_id, d.name as disease_name,
               type(r) as relationship,
               p.id as phenotype_id, p.name as phenotype_name
        LIMIT 10
        """
        samples = self.run_query(query)

        print("\nSample disease-phenotype associations:")
        print("-" * 80)
        for assoc in samples:
            print(f"  {assoc['disease_name']} ({assoc['disease_id']})")
            print(f"    -[{assoc['relationship']}]->")
            print(f"  {assoc['phenotype_name']} ({assoc['phenotype_id']})")
            print()

        assoc_info['samples'] = samples

        return assoc_info

    def explore_gene_disease_associations(self) -> Dict[str, Any]:
        """Explore gene-disease associations."""
        print(f"\n{'=' * 80}")
        print("EXPLORING GENE-DISEASE ASSOCIATIONS")
        print("=" * 80)

        assoc_info = {}

        # Find gene-disease relationship patterns
        query = """
        MATCH (g)-[r]-(d)
        WHERE (g:Gene OR g:`biolink:Gene`)
        AND (d:Disease OR d:`biolink:Disease`)
        WITH type(r) as relType, labels(g) as gLabels, labels(d) as dLabels, count(*) as cnt
        RETURN relType, gLabels, dLabels, cnt
        ORDER BY cnt DESC
        LIMIT 10
        """
        patterns = self.run_query(query)

        print("\nGene-Disease relationship patterns:")
        print("-" * 80)
        for pattern in patterns:
            print(f"  {pattern['gLabels']} -[{pattern['relType']}]- {pattern['dLabels']}: {pattern['cnt']:,} associations")

        assoc_info['patterns'] = patterns

        # Get sample associations
        query = """
        MATCH (g)-[r]-(d)
        WHERE (g:Gene OR g:`biolink:Gene`)
        AND (d:Disease OR d:`biolink:Disease`)
        RETURN g.id as gene_id, g.name as gene_name,
               type(r) as relationship,
               d.id as disease_id, d.name as disease_name
        LIMIT 10
        """
        samples = self.run_query(query)

        print("\nSample gene-disease associations:")
        print("-" * 80)
        for assoc in samples:
            print(f"  {assoc['gene_name']} ({assoc['gene_id']})")
            print(f"    -[{assoc['relationship']}]-")
            print(f"  {assoc['disease_name']} ({assoc['disease_id']})")
            print()

        assoc_info['samples'] = samples

        return assoc_info

    def explore_muscular_dystrophies(self) -> Dict[str, Any]:
        """Explore muscular dystrophy specific data."""
        print(f"\n{'=' * 80}")
        print("EXPLORING MUSCULAR DYSTROPHY DATA")
        print("=" * 80)

        md_info = {}

        # Search for muscular dystrophy diseases
        print("\nSearching for muscular dystrophy diseases...")
        print("-" * 80)

        query = """
        MATCH (d)
        WHERE (d:Disease OR d:`biolink:Disease` OR d:NamedThing)
        AND (toLower(d.name) CONTAINS 'muscular dystrophy'
             OR toLower(d.name) CONTAINS 'duchenne'
             OR toLower(d.name) CONTAINS 'becker')
        RETURN d.id as id, d.name as name, labels(d) as labels
        LIMIT 20
        """
        diseases = self.run_query(query)

        md_info['diseases'] = diseases
        print(f"Found {len(diseases)} muscular dystrophy diseases:")
        for disease in diseases:
            print(f"  - {disease['name']} ({disease['id']})")
            print(f"    Labels: {disease['labels']}")

        # For each disease, get associated genes and phenotypes
        print("\nExploring detailed associations for key diseases...")
        print("-" * 80)

        key_diseases = ['MONDO:0007254', 'MONDO:0008114']  # DMD and BMD Mondo IDs
        md_info['detailed_associations'] = {}

        for disease_id in key_diseases:
            print(f"\nDisease: {disease_id}")

            # Get disease info
            query = f"""
            MATCH (d)
            WHERE d.id = '{disease_id}'
            RETURN d.name as name, d.id as id, properties(d) as props
            """
            disease_info = self.run_query(query)
            if disease_info:
                print(f"  Name: {disease_info[0]['name']}")

                # Get associated genes
                query = f"""
                MATCH (d)-[r]-(g)
                WHERE d.id = '{disease_id}'
                AND (g:Gene OR g:`biolink:Gene`)
                RETURN g.id as gene_id, g.name as gene_name, type(r) as relationship
                LIMIT 10
                """
                genes = self.run_query(query)
                print(f"  Associated genes ({len(genes)}):")
                for gene in genes:
                    print(f"    - {gene['gene_name']} ({gene['gene_id']}) via {gene['relationship']}")

                # Get associated phenotypes
                query = f"""
                MATCH (d)-[r]->(p)
                WHERE d.id = '{disease_id}'
                AND (p:Phenotype OR p:`biolink:PhenotypicFeature`)
                RETURN p.id as phenotype_id, p.name as phenotype_name, type(r) as relationship
                LIMIT 15
                """
                phenotypes = self.run_query(query)
                print(f"  Associated phenotypes ({len(phenotypes)}):")
                for pheno in phenotypes:
                    print(f"    - {pheno['phenotype_name']} ({pheno['phenotype_id']}) via {pheno['relationship']}")

                md_info['detailed_associations'][disease_id] = {
                    'info': disease_info[0],
                    'genes': genes,
                    'phenotypes': phenotypes
                }

        return md_info

    def explore_dmd_gene(self) -> Dict[str, Any]:
        """Explore the DMD gene specifically."""
        print(f"\n{'=' * 80}")
        print("EXPLORING DMD GENE (DYSTROPHIN)")
        print("=" * 80)

        dmd_info = {}

        # Find DMD gene
        query = """
        MATCH (g)
        WHERE (g:Gene OR g:`biolink:Gene`)
        AND (g.id CONTAINS 'DMD' OR g.name CONTAINS 'dystrophin' OR g.symbol = 'DMD')
        RETURN g.id as id, g.name as name, g.symbol as symbol, properties(g) as props, labels(g) as labels
        LIMIT 5
        """
        genes = self.run_query(query)

        print(f"\nFound {len(genes)} DMD/dystrophin gene nodes:")
        for gene in genes:
            print(f"\n  Gene: {gene.get('name')} ({gene['id']})")
            print(f"  Symbol: {gene.get('symbol')}")
            print(f"  Labels: {gene['labels']}")

        if genes:
            dmd_gene_id = genes[0]['id']
            dmd_info['gene'] = genes[0]

            # Get associated diseases
            query = f"""
            MATCH (g)-[r]-(d)
            WHERE g.id = '{dmd_gene_id}'
            AND (d:Disease OR d:`biolink:Disease`)
            RETURN d.id as disease_id, d.name as disease_name, type(r) as relationship
            LIMIT 20
            """
            diseases = self.run_query(query)

            print(f"\n  Associated diseases ({len(diseases)}):")
            for disease in diseases:
                print(f"    - {disease['disease_name']} ({disease['disease_id']}) via {disease['relationship']}")

            dmd_info['associated_diseases'] = diseases

            # Get associated phenotypes
            query = f"""
            MATCH (g)-[r]-(p)
            WHERE g.id = '{dmd_gene_id}'
            AND (p:Phenotype OR p:`biolink:PhenotypicFeature`)
            RETURN p.id as phenotype_id, p.name as phenotype_name, type(r) as relationship
            LIMIT 20
            """
            phenotypes = self.run_query(query)

            print(f"\n  Associated phenotypes ({len(phenotypes)}):")
            for pheno in phenotypes:
                print(f"    - {pheno['phenotype_name']} ({pheno['phenotype_id']}) via {pheno['relationship']}")

            dmd_info['associated_phenotypes'] = phenotypes

        return dmd_info

    def save_report(self, data: Dict, filename: str):
        """Save exploration data to JSON file."""
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        print(f"\n✓ Report saved to {filename}")


def main():
    """Main exploration function."""
    explorer = MonarchExplorer()

    try:
        # Create a comprehensive report
        report = {
            'database': NEO4J_DATABASE,
            'uri': NEO4J_URI,
            'exploration_date': '2025-11-15'
        }

        # 1. Explore schema
        report['schema'] = explorer.explore_schema()

        # 2. Explore key node types
        key_labels = ['biolink:Disease', 'biolink:Gene', 'biolink:PhenotypicFeature']
        report['node_details'] = {}

        for label in key_labels:
            if label in report['schema']['node_labels']:
                report['node_details'][label] = explorer.explore_node_properties(label)

        # 3. Explore associations
        report['disease_phenotype_associations'] = explorer.explore_disease_phenotype_associations()
        report['gene_disease_associations'] = explorer.explore_gene_disease_associations()

        # 4. Explore muscular dystrophies
        report['muscular_dystrophies'] = explorer.explore_muscular_dystrophies()

        # 5. Explore DMD gene
        report['dmd_gene'] = explorer.explore_dmd_gene()

        # Save comprehensive report
        explorer.save_report(report, 'monarch_exploration_report.json')

        print("\n" + "=" * 80)
        print("EXPLORATION COMPLETE!")
        print("=" * 80)
        print("\nKey findings:")
        print(f"  - Total node labels: {len(report['schema']['node_labels'])}")
        print(f"  - Total relationship types: {len(report['schema']['relationship_types'])}")
        print(f"  - Muscular dystrophy diseases found: {len(report['muscular_dystrophies']['diseases'])}")
        print(f"\nFull report saved to: monarch_exploration_report.json")

    finally:
        explorer.close()


if __name__ == "__main__":
    main()
