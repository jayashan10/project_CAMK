#!/usr/bin/env python3
"""
Targeted exploration of muscular dystrophy data in Monarch database.
Focuses on DMD, BMD, LGMD, and LAMA2-related diseases.
"""

import os
import json
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://127.0.0.1:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "monarch")


class MDExplorer:
    """Muscular Dystrophy specific explorer."""

    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        self.driver.verify_connectivity()
        print("✓ Connected to Monarch database\n")

    def close(self):
        self.driver.close()

    def run_query(self, query: str, params: dict = None):
        with self.driver.session(database=NEO4J_DATABASE) as session:
            result = session.run(query, params or {})
            return [dict(record) for record in result]

    def find_disease_by_name(self, search_term: str):
        """Find diseases matching a search term."""
        print(f"Searching for diseases matching: '{search_term}'")
        print("-" * 80)

        query = """
        MATCH (d:`biolink:Disease`)
        WHERE toLower(d.name) CONTAINS toLower($search_term)
           OR ANY(syn IN COALESCE(d.synonym, []) WHERE toLower(syn) CONTAINS toLower($search_term))
        RETURN d.id as id, d.name as name, d.synonym as synonyms,
               d.description as description
        LIMIT 10
        """
        results = self.run_query(query, {"search_term": search_term})

        for r in results:
            print(f"\nID: {r['id']}")
            print(f"Name: {r['name']}")
            if r.get('description'):
                desc = r['description'][:200] + "..." if len(str(r['description'])) > 200 else r['description']
                print(f"Description: {desc}")
            if r.get('synonyms'):
                syns = r['synonyms']
                if isinstance(syns, list):
                    print(f"Synonyms: {', '.join(syns[:3])}")

        return results

    def explore_disease_in_depth(self, disease_id: str):
        """Deep dive into a specific disease."""
        print(f"\n{'='*80}")
        print(f"DEEP DIVE: {disease_id}")
        print("="*80)

        # Get disease info
        query = """
        MATCH (d:`biolink:Disease`)
        WHERE d.id = $disease_id
        RETURN d
        """
        disease_result = self.run_query(query, {"disease_id": disease_id})

        if not disease_result:
            print(f"Disease {disease_id} not found!")
            return None

        disease = dict(disease_result[0]['d'])
        print(f"\n1. DISEASE INFO:")
        print(f"   Name: {disease.get('name')}")
        print(f"   ID: {disease.get('id')}")
        if disease.get('description'):
            print(f"   Description: {disease.get('description')[:300]}...")

        # Get associated genes
        print(f"\n2. ASSOCIATED GENES:")
        print("-" * 80)
        query = """
        MATCH (g:`biolink:Gene`)-[r]-(d:`biolink:Disease`)
        WHERE d.id = $disease_id
        RETURN g.id as gene_id, g.symbol as symbol, g.name as name,
               type(r) as relationship
        ORDER BY g.symbol
        """
        genes = self.run_query(query, {"disease_id": disease_id})

        for gene in genes:
            print(f"   {gene['symbol']} ({gene['gene_id']})")
            print(f"      Name: {gene.get('name', 'N/A')}")
            print(f"      Relationship: {gene['relationship']}")

        # Get associated phenotypes
        print(f"\n3. ASSOCIATED PHENOTYPES (TOP 20):")
        print("-" * 80)
        query = """
        MATCH (d:`biolink:Disease`)-[r:`biolink:has_phenotype`]->(p:`biolink:PhenotypicFeature`)
        WHERE d.id = $disease_id
        RETURN p.id as phenotype_id, p.name as phenotype_name
        ORDER BY p.name
        LIMIT 20
        """
        phenotypes = self.run_query(query, {"disease_id": disease_id})

        for pheno in phenotypes:
            print(f"   {pheno['phenotype_id']}: {pheno['phenotype_name']}")

        # Get mode of inheritance
        print(f"\n4. MODE OF INHERITANCE:")
        print("-" * 80)
        query = """
        MATCH (d:`biolink:Disease`)-[r:`biolink:has_mode_of_inheritance`]->(p:`biolink:PhenotypicFeature`)
        WHERE d.id = $disease_id
        RETURN p.id as phenotype_id, p.name as phenotype_name
        """
        inheritance = self.run_query(query, {"disease_id": disease_id})

        for inh in inheritance:
            print(f"   {inh['phenotype_id']}: {inh['phenotype_name']}")

        return {
            'disease': disease,
            'genes': genes,
            'phenotypes': phenotypes,
            'inheritance': inheritance
        }

    def explore_gene(self, gene_symbol: str):
        """Explore a specific gene."""
        print(f"\n{'='*80}")
        print(f"GENE EXPLORATION: {gene_symbol}")
        print("="*80)

        # Find the human gene
        query = """
        MATCH (g:`biolink:Gene`)
        WHERE g.symbol = $symbol
        AND (g.in_taxon = 'NCBITaxon:9606' OR g.in_taxon_label = 'Homo sapiens')
        RETURN g
        LIMIT 1
        """
        gene_result = self.run_query(query, {"symbol": gene_symbol})

        if not gene_result:
            print(f"Gene {gene_symbol} not found!")
            return None

        gene = dict(gene_result[0]['g'])
        print(f"\n1. GENE INFO:")
        print(f"   Symbol: {gene.get('symbol')}")
        print(f"   ID: {gene.get('id')}")
        print(f"   Name: {gene.get('name', gene.get('full_name', 'N/A'))}")
        print(f"   Taxon: {gene.get('in_taxon_label')}")

        gene_id = gene['id']

        # Get associated diseases
        print(f"\n2. ASSOCIATED DISEASES:")
        print("-" * 80)
        query = """
        MATCH (g:`biolink:Gene`)-[r]-(d:`biolink:Disease`)
        WHERE g.id = $gene_id
        RETURN d.id as disease_id, d.name as disease_name,
               type(r) as relationship
        ORDER BY d.name
        """
        diseases = self.run_query(query, {"gene_id": gene_id})

        for disease in diseases:
            print(f"   {disease['disease_name']}")
            print(f"      ID: {disease['disease_id']}")
            print(f"      Relationship: {disease['relationship']}")

        # Get variants
        print(f"\n3. ASSOCIATED VARIANTS (SAMPLE):")
        print("-" * 80)
        query = """
        MATCH (v:`biolink:SequenceVariant`)-[r:`biolink:is_sequence_variant_of`]->(g:`biolink:Gene`)
        WHERE g.id = $gene_id
        RETURN v.id as variant_id, v.name as variant_name
        LIMIT 10
        """
        variants = self.run_query(query, {"gene_id": gene_id})

        if variants:
            for variant in variants:
                print(f"   {variant['variant_id']}: {variant.get('variant_name', 'N/A')}")
        else:
            print("   No variants found")

        return {
            'gene': gene,
            'diseases': diseases,
            'variants': variants
        }

    def find_phenotype_overlap(self, disease1_id: str, disease2_id: str):
        """Find overlapping phenotypes between two diseases."""
        print(f"\n{'='*80}")
        print(f"PHENOTYPE OVERLAP")
        print(f"Disease 1: {disease1_id}")
        print(f"Disease 2: {disease2_id}")
        print("="*80)

        query = """
        MATCH (d1:`biolink:Disease`)-[:`biolink:has_phenotype`]->(p:`biolink:PhenotypicFeature`)
              <-[:`biolink:has_phenotype`]-(d2:`biolink:Disease`)
        WHERE d1.id = $disease1_id AND d2.id = $disease2_id
        RETURN p.id as phenotype_id, p.name as phenotype_name
        ORDER BY p.name
        """
        overlapping = self.run_query(query, {
            "disease1_id": disease1_id,
            "disease2_id": disease2_id
        })

        print(f"\nOverlapping phenotypes: {len(overlapping)}")
        for pheno in overlapping[:15]:
            print(f"   {pheno['phenotype_id']}: {pheno['phenotype_name']}")

        # Get unique phenotypes for each disease
        query = """
        MATCH (d1:`biolink:Disease`)-[:`biolink:has_phenotype`]->(p1:`biolink:PhenotypicFeature`)
        WHERE d1.id = $disease1_id
        AND NOT EXISTS {
            MATCH (d2:`biolink:Disease`)-[:`biolink:has_phenotype`]->(p1)
            WHERE d2.id = $disease2_id
        }
        RETURN p1.id as phenotype_id, p1.name as phenotype_name
        ORDER BY p1.name
        LIMIT 10
        """
        unique_d1 = self.run_query(query, {
            "disease1_id": disease1_id,
            "disease2_id": disease2_id
        })

        print(f"\nUnique to {disease1_id} (sample):")
        for pheno in unique_d1:
            print(f"   {pheno['phenotype_id']}: {pheno['phenotype_name']}")

        return overlapping


def main():
    explorer = MDExplorer()

    try:
        report = {}

        # 1. Find Duchenne muscular dystrophy
        print("="*80)
        print("STEP 1: FINDING DUCHENNE MUSCULAR DYSTROPHY")
        print("="*80)
        dmd_diseases = explorer.find_disease_by_name("Duchenne")
        report['dmd_search'] = dmd_diseases

        # 2. Find Becker muscular dystrophy
        print(f"\n{'='*80}")
        print("STEP 2: FINDING BECKER MUSCULAR DYSTROPHY")
        print("="*80)
        bmd_diseases = explorer.find_disease_by_name("Becker muscular")
        report['bmd_search'] = bmd_diseases

        # 3. Find LAMA2-related diseases
        print(f"\n{'='*80}")
        print("STEP 3: FINDING LAMA2-RELATED DISEASES")
        print("="*80)
        lama2_diseases = explorer.find_disease_by_name("LAMA2")
        report['lama2_search'] = lama2_diseases

        # 4. Find LGMD
        print(f"\n{'='*80}")
        print("STEP 4: FINDING LIMB-GIRDLE MUSCULAR DYSTROPHY")
        print("="*80)
        lgmd_diseases = explorer.find_disease_by_name("limb-girdle")
        report['lgmd_search'] = lgmd_diseases

        # 5. Deep dive into DMD (assuming MONDO:0010679 based on common knowledge)
        dmd_id = "MONDO:0010679"  # Duchenne muscular dystrophy
        report['dmd_detail'] = explorer.explore_disease_in_depth(dmd_id)

        # 6. Deep dive into BMD (assuming MONDO:0010311)
        bmd_id = "MONDO:0010311"  # Becker muscular dystrophy
        report['bmd_detail'] = explorer.explore_disease_in_depth(bmd_id)

        # 7. Explore DMD gene
        report['dmd_gene'] = explorer.explore_gene("DMD")

        # 8. Explore LAMA2 gene
        report['lama2_gene'] = explorer.explore_gene("LAMA2")

        # 9. Find phenotype overlap between DMD and BMD
        report['dmd_bmd_overlap'] = explorer.find_phenotype_overlap(dmd_id, bmd_id)

        # Save report
        with open('md_specific_report.json', 'w') as f:
            json.dump(report, f, indent=2, default=str)

        print("\n" + "="*80)
        print("EXPLORATION COMPLETE!")
        print("="*80)
        print("\nReport saved to: md_specific_report.json")

    finally:
        explorer.close()


if __name__ == "__main__":
    main()
