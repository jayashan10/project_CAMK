"""Test connection to the Monarch Initiative database and explore its schema."""

import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed")

from neo4j import GraphDatabase


def test_monarch_connection():
    """Test connection to the monarch database and explore its schema."""
    uri = os.getenv("NEO4J_URI", "neo4j://127.0.0.1:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "")
    database = os.getenv("NEO4J_DATABASE", "monarch")  # Default to monarch
    
    print("=" * 70)
    print("Monarch Initiative Database Explorer")
    print("=" * 70)
    print(f"URI: {uri}")
    print(f"User: {user}")
    print(f"Database: {database}")
    print()
    
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        
        with driver.session(database=database) as session:
            # Test connection
            result = session.run("RETURN 1 as test")
            test_value = result.single()["test"]
            print(f"✓ Connection successful: {test_value}")
            
            # Get node count
            node_result = session.run("MATCH (n) RETURN count(n) as count")
            node_count = node_result.single()["count"]
            print(f"✓ Total nodes: {node_count:,}")
            
            # Get relationship count
            rel_result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
            rel_count = rel_result.single()["count"]
            print(f"✓ Total relationships: {rel_count:,}")
            
            # Get all labels
            print("\n" + "=" * 70)
            print("Node Labels")
            print("=" * 70)
            label_result = session.run("CALL db.labels()")
            labels = [record["label"] for record in label_result]
            print(f"Found {len(labels)} node labels:\n")
            
            label_counts = {}
            for label in labels:
                # Escape labels that contain colons (like biolink:Disease)
                label_escaped = f"`{label}`" if ":" in label else label
                try:
                    count_result = session.run(f"MATCH (n:{label_escaped}) RETURN count(n) as count")
                    count = count_result.single()["count"]
                    label_counts[label] = count
                    if count > 0:
                        print(f"  {label:30s} {count:>12,} nodes")
                except Exception as e:
                    # Skip if query fails
                    pass
            
            # Get relationship types
            print("\n" + "=" * 70)
            print("Relationship Types")
            print("=" * 70)
            rel_type_result = session.run("CALL db.relationshipTypes()")
            rel_types = [record["relationshipType"] for record in rel_type_result]
            print(f"Found {len(rel_types)} relationship types:\n")
            
            for rel_type in rel_types[:50]:  # Show first 50
                # Escape relationship types that contain colons (like biolink:located_in)
                rel_type_escaped = rel_type.replace(":", "`:`") if ":" in rel_type else rel_type
                try:
                    count_result = session.run(
                        f"MATCH ()-[r:`{rel_type}`]->() RETURN count(r) as count"
                    )
                    count = count_result.single()["count"]
                    if count > 0:
                        print(f"  {rel_type:40s} {count:>12,} relationships")
                except Exception as e:
                    # Skip if query fails
                    pass
            
            if len(rel_types) > 50:
                print(f"\n  ... and {len(rel_types) - 50} more relationship types")
            
            # Sample nodes from key labels
            print("\n" + "=" * 70)
            print("Sample Nodes")
            print("=" * 70)
            
            # Find labels that might be diseases, genes, or phenotypes
            disease_labels = [l for l in labels if "disease" in l.lower() or "mondo" in l.lower()]
            gene_labels = [l for l in labels if "gene" in l.lower()]
            phenotype_labels = [l for l in labels if "phenotype" in l.lower() or "hp" in l.lower()]
            
            for label_list, name in [(disease_labels, "Disease"), (gene_labels, "Gene"), (phenotype_labels, "Phenotype")]:
                if label_list:
                    label = label_list[0]
                    if label_counts.get(label, 0) > 0:
                        label_escaped = f"`{label}`" if ":" in label else label
                        print(f"\nSample {name} nodes (label: {label}):")
                        try:
                            sample_result = session.run(
                                f"MATCH (n:{label_escaped}) RETURN n LIMIT 3"
                            )
                            for i, record in enumerate(sample_result, 1):
                                node = record["n"]
                                props = dict(node.items())
                                # Show key properties
                                key_props = {k: v for k, v in list(props.items())[:5]}
                                print(f"  {i}. {key_props}")
                        except Exception as e:
                            print(f"  Could not retrieve samples: {e}")
                        break
            
            # Check for Monarch-specific patterns
            print("\n" + "=" * 70)
            print("Monarch Initiative Patterns")
            print("=" * 70)
            
            monarch_queries = [
                ("Disease-Gene associations", 
                 "MATCH (d)-[r]->(g) WHERE 'Disease' IN labels(d) AND 'Gene' IN labels(g) RETURN count(r) as count LIMIT 1"),
                ("Disease-Phenotype associations",
                 "MATCH (d)-[r]->(p) WHERE 'Disease' IN labels(d) AND ('Phenotype' IN labels(p) OR 'HP' IN labels(p)) RETURN count(r) as count LIMIT 1"),
                ("Gene-Phenotype associations",
                 "MATCH (g)-[r]->(p) WHERE 'Gene' IN labels(g) AND ('Phenotype' IN labels(p) OR 'HP' IN labels(p)) RETURN count(r) as count LIMIT 1"),
            ]
            
            for name, query in monarch_queries:
                try:
                    result = session.run(query)
                    record = result.single()
                    if record and "count" in record:
                        count = record["count"]
                        print(f"✓ {name}: {count:,}")
                except Exception as e:
                    print(f"⚠ {name}: {e}")
            
            # Get database info
            print("\n" + "=" * 70)
            print("Database Information")
            print("=" * 70)
            try:
                db_info = session.run("CALL db.info()")
                info = db_info.single()
                if info:
                    print(f"Database: {info.get('name', 'N/A')}")
                    print(f"Store format: {info.get('storeFormat', 'N/A')}")
            except:
                pass
        
        driver.close()
        print("\n" + "=" * 70)
        print("✓ Exploration complete!")
        print("=" * 70)
        return True
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_monarch_connection()
    sys.exit(0 if success else 1)

