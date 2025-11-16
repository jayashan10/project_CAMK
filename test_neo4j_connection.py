"""Test Neo4j connection and explore the database.

This script will:
1. Load environment variables from .env
2. Connect to Neo4j
3. Show basic database info
4. Explore the schema (especially useful for Monarch Initiative dump)
"""

import os
import sys
from pathlib import Path

# Load .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed. Install with: pip install python-dotenv")
    print("Trying to use environment variables directly...")

from neo4j import GraphDatabase
from backend.knowledge_graph.service import KnowledgeGraphService


def test_direct_connection():
    """Test direct Neo4j connection using environment variables."""
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    password = os.getenv("NEO4J_PASSWORD")
    database = os.getenv("NEO4J_DATABASE", "neo4j")
    
    if not all([uri, user, password]):
        print("ERROR: Missing Neo4j environment variables!")
        print("Required: NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD")
        print("\nCurrent values:")
        print(f"  NEO4J_URI: {uri or 'NOT SET'}")
        print(f"  NEO4J_USER: {user or 'NOT SET'}")
        print(f"  NEO4J_PASSWORD: {'*' * len(password) if password else 'NOT SET'}")
        print(f"  NEO4J_DATABASE: {database}")
        return None
    
    print("=" * 70)
    print("Testing Direct Neo4j Connection")
    print("=" * 70)
    print(f"URI: {uri}")
    print(f"User: {user}")
    print(f"Database: {database}")
    print()
    
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        
        # Test basic connection
        with driver.session(database=database) as session:
            result = session.run("RETURN 1 as test")
            test_value = result.single()["test"]
            print(f"✓ Connection test successful: {test_value}")
            
            # Get node count
            node_result = session.run("MATCH (n) RETURN count(n) as count")
            node_count = node_result.single()["count"]
            print(f"✓ Total nodes in database: {node_count:,}")
            
            # Get relationship count
            rel_result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
            rel_count = rel_result.single()["count"]
            print(f"✓ Total relationships: {rel_count:,}")
            
            # Get all labels
            label_result = session.run("CALL db.labels()")
            labels = [record["label"] for record in label_result]
            print(f"\n✓ Found {len(labels)} node labels:")
            for label in labels[:20]:  # Show first 20
                count_result = session.run(f"MATCH (n:{label}) RETURN count(n) as count")
                count = count_result.single()["count"]
                print(f"    - {label}: {count:,} nodes")
            if len(labels) > 20:
                print(f"    ... and {len(labels) - 20} more labels")
            
            # Get relationship types
            rel_type_result = session.run("CALL db.relationshipTypes()")
            rel_types = [record["relationshipType"] for record in rel_type_result]
            print(f"\n✓ Found {len(rel_types)} relationship types:")
            for rel_type in rel_types[:20]:  # Show first 20
                count_result = session.run(
                    f"MATCH ()-[r:{rel_type}]->() RETURN count(r) as count"
                )
                count = count_result.single()["count"]
                print(f"    - {rel_type}: {count:,} relationships")
            if len(rel_types) > 20:
                print(f"    ... and {len(rel_types) - 20} more types")
            
            # Sample nodes
            print("\n✓ Sample nodes (first 5):")
            sample_result = session.run(
                "MATCH (n) RETURN labels(n) as labels, keys(n) as keys LIMIT 5"
            )
            for i, record in enumerate(sample_result, 1):
                labels = record["labels"]
                keys = record["keys"]
                print(f"    {i}. Labels: {labels}, Properties: {keys[:5]}...")
        
        driver.close()
        return True
        
    except Exception as e:
        print(f"\n✗ Connection failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_knowledge_graph_service():
    """Test the KnowledgeGraphService connection."""
    print("\n" + "=" * 70)
    print("Testing KnowledgeGraphService")
    print("=" * 70)
    
    try:
        service = KnowledgeGraphService()
        
        if service._driver:
            print("✓ KnowledgeGraphService connected to Neo4j")
            
            # Test getting disease profiles
            try:
                profiles = service.get_disease_profiles()
                print(f"✓ Retrieved {len(profiles)} disease profiles")
                if profiles:
                    print("   Sample diseases:")
                    for code, profile in list(profiles.items())[:3]:
                        print(f"     - {code}: {profile.get('name', 'N/A')}")
            except Exception as e:
                print(f"⚠ Could not retrieve disease profiles: {e}")
                print("   (This is OK if using Monarch Initiative schema)")
            
            return True
        else:
            print("⚠ KnowledgeGraphService fell back to in-memory store")
            print("   This means Neo4j connection failed or wasn't configured")
            return False
            
    except Exception as e:
        print(f"✗ KnowledgeGraphService error: {e}")
        import traceback
        traceback.print_exc()
        return False


def explore_monarch_schema():
    """Explore Monarch Initiative schema if detected."""
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    password = os.getenv("NEO4J_PASSWORD")
    database = os.getenv("NEO4J_DATABASE", "neo4j")
    
    if not all([uri, user, password]):
        return
    
    print("\n" + "=" * 70)
    print("Exploring Database Schema (Monarch Initiative Detection)")
    print("=" * 70)
    
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        
        with driver.session(database=database) as session:
            # Check for Monarch-specific patterns
            monarch_queries = [
                ("Disease nodes", "MATCH (n) WHERE 'Disease' IN labels(n) RETURN count(n) as count LIMIT 1"),
                ("Gene nodes", "MATCH (n) WHERE 'Gene' IN labels(n) RETURN count(n) as count LIMIT 1"),
                ("Phenotype nodes", "MATCH (n) WHERE 'Phenotype' IN labels(n) OR 'HP' IN labels(n) RETURN count(n) as count LIMIT 1"),
                ("Monarch associations", "MATCH ()-[r]->() WHERE type(r) CONTAINS 'ASSOCIATED' RETURN count(r) as count LIMIT 1"),
            ]
            
            for name, query in monarch_queries:
                try:
                    result = session.run(query)
                    record = result.single()
                    if record:
                        count = record["count"]
                        print(f"✓ {name}: {count:,}")
                except Exception as e:
                    print(f"⚠ {name}: Query failed ({e})")
            
            # Try to find some interesting patterns
            print("\n✓ Sample queries to explore:")
            sample_queries = [
                ("Find diseases", "MATCH (d) WHERE 'Disease' IN labels(d) RETURN d LIMIT 3"),
                ("Find genes", "MATCH (g) WHERE 'Gene' IN labels(g) RETURN g LIMIT 3"),
                ("Disease-Gene relationships", "MATCH (d)-[r]->(g) WHERE 'Disease' IN labels(d) AND 'Gene' IN labels(g) RETURN type(r), count(*) as count LIMIT 5"),
            ]
            
            for name, query in sample_queries:
                try:
                    result = session.run(query)
                    records = list(result)
                    if records:
                        print(f"\n  {name}:")
                        for record in records[:3]:
                            print(f"    {dict(record)}")
                except Exception as e:
                    print(f"  ⚠ {name}: {e}")
        
        driver.close()
        
    except Exception as e:
        print(f"✗ Schema exploration failed: {e}")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("Neo4j Connection Test")
    print("=" * 70)
    print()
    
    # Check if .env file exists
    env_file = Path(".env")
    if env_file.exists():
        print(f"✓ Found .env file: {env_file.absolute()}")
    else:
        print(f"⚠ No .env file found at {env_file.absolute()}")
        print("  Make sure you've created it with NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD")
    
    print()
    
    # Test direct connection
    success = test_direct_connection()
    
    if success:
        # Explore schema
        explore_monarch_schema()
        
        # Test KnowledgeGraphService
        test_knowledge_graph_service()
        
        print("\n" + "=" * 70)
        print("✓ All tests completed!")
        print("=" * 70)
    else:
        print("\n" + "=" * 70)
        print("✗ Connection test failed. Please check your .env file and Neo4j setup.")
        print("=" * 70)
        sys.exit(1)

