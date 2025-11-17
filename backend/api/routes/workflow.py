"""API endpoints for workflow visualization data."""
from typing import Dict, List, Any
from fastapi import APIRouter, HTTPException

from backend.api.routes.scenarios import _scenario_cache

router = APIRouter()


def build_workflow_graph(scenario_response) -> Dict[str, Any]:
    """Build React Flow compatible graph structure from scenario response.

    The graph shows the clinical reasoning workflow:
    Symptoms → HPO Terms → Phenotype Matching → Diseases → Variant Analysis → Treatments

    Args:
        scenario_response: Processed scenario response

    Returns:
        Dict with 'nodes' and 'edges' lists compatible with React Flow
    """
    nodes = []
    edges = []
    node_id_counter = 0

    # Layout configuration (horizontal flow, left to right)
    LAYER_SPACING = 300  # pixels between layers
    NODE_SPACING = 100   # pixels between nodes in same layer

    # Layer 1: Symptoms (input symptoms from scenario)
    symptom_nodes = []
    if hasattr(scenario_response, '_scenario') and scenario_response._scenario:
        symptoms = scenario_response._scenario.presenting_symptoms or []
    else:
        # Fallback: extract from differential diagnoses supporting features
        symptoms = []
        for dx in scenario_response.differential_diagnoses[:1]:
            symptoms.extend(dx.supporting_features[:5])

    for i, symptom in enumerate(symptoms[:5]):  # Limit to 5 for visualization
        node_id = f"symptom-{node_id_counter}"
        node_id_counter += 1
        nodes.append({
            "id": node_id,
            "type": "symptom",
            "position": {"x": 0, "y": i * NODE_SPACING},
            "data": {
                "label": symptom,
                "category": "symptom"
            }
        })
        symptom_nodes.append(node_id)

    # Layer 2: HPO Terms (mapped from symptoms)
    # Note: HPO mapping data may not be stored in response, showing conceptually
    hpo_node_id = f"hpo-mapping-{node_id_counter}"
    node_id_counter += 1
    nodes.append({
        "id": hpo_node_id,
        "type": "hpo",
        "position": {"x": LAYER_SPACING, "y": len(symptom_nodes) * NODE_SPACING / 2},
        "data": {
            "label": "HPO Term Mapping",
            "description": "Clinical features mapped to standardized phenotype ontology",
            "category": "processing"
        }
    })

    # Connect symptoms to HPO mapping
    for symptom_id in symptom_nodes:
        edges.append({
            "id": f"e-{symptom_id}-{hpo_node_id}",
            "source": symptom_id,
            "target": hpo_node_id,
            "label": "maps to",
            "animated": True
        })

    # Layer 3: Phenotype Matching Node
    matching_node_id = f"matching-{node_id_counter}"
    node_id_counter += 1
    nodes.append({
        "id": matching_node_id,
        "type": "processing",
        "position": {"x": LAYER_SPACING * 2, "y": len(symptom_nodes) * NODE_SPACING / 2},
        "data": {
            "label": "Phenotype Matching",
            "description": "Knowledge graph query for disease-phenotype associations",
            "category": "processing"
        }
    })

    edges.append({
        "id": f"e-{hpo_node_id}-{matching_node_id}",
        "source": hpo_node_id,
        "target": matching_node_id,
        "label": "query KG",
        "animated": True
    })

    # Layer 4: Diseases (differential diagnoses)
    disease_nodes = []
    for i, dx in enumerate(scenario_response.differential_diagnoses[:5]):  # Top 5 diagnoses
        node_id = f"disease-{node_id_counter}"
        node_id_counter += 1
        nodes.append({
            "id": node_id,
            "type": "disease",
            "position": {"x": LAYER_SPACING * 3, "y": i * NODE_SPACING},
            "data": {
                "label": dx.disease_name,
                "confidence": dx.confidence_score,
                "supporting_features": dx.supporting_features,
                "recommended_tests": dx.recommended_tests,
                "category": "disease",
                "rank": i + 1
            }
        })
        disease_nodes.append((node_id, dx))

        # Connect matching to disease with score label
        edges.append({
            "id": f"e-{matching_node_id}-{node_id}",
            "source": matching_node_id,
            "target": node_id,
            "label": f"score: {dx.confidence_score:.0f}",
            "data": {"score": dx.confidence_score}
        })

    # Layer 5: Variant Analysis (if genetic data provided)
    if scenario_response.variant_interpretation:
        variant_node_id = f"variant-{node_id_counter}"
        node_id_counter += 1

        # Get variant details
        variant_data = scenario_response.variant_interpretation
        variant_label = "Variant Analysis"
        if "gene" in variant_data:
            variant_label = f"{variant_data['gene']} Variant"

        nodes.append({
            "id": variant_node_id,
            "type": "variant",
            "position": {"x": LAYER_SPACING * 4, "y": NODE_SPACING},
            "data": {
                "label": variant_label,
                "interpretation": variant_data,
                "category": "variant"
            }
        })

        # Connect top disease(s) to variant analysis
        for disease_id, dx in disease_nodes[:2]:  # Top 2 diseases
            edges.append({
                "id": f"e-{disease_id}-{variant_node_id}",
                "source": disease_id,
                "target": variant_node_id,
                "label": "inform",
                "animated": True
            })

    # Layer 6: Treatments (from recommendations)
    treatment_recommendations = [
        rec for rec in scenario_response.recommendations
        if rec.category == "treatment"
    ]

    treatment_nodes = []
    for i, rec in enumerate(treatment_recommendations[:5]):  # Top 5 treatments
        node_id = f"treatment-{node_id_counter}"
        node_id_counter += 1
        nodes.append({
            "id": node_id,
            "type": "treatment",
            "position": {"x": LAYER_SPACING * 5, "y": i * NODE_SPACING},
            "data": {
                "label": rec.recommendation[:50] + "..." if len(rec.recommendation) > 50 else rec.recommendation,
                "full_text": rec.recommendation,
                "evidence_level": rec.evidence_level,
                "urgency": rec.urgency,
                "category": "treatment"
            }
        })
        treatment_nodes.append(node_id)

        # Connect from primary disease or variant to treatment
        source_id = variant_node_id if scenario_response.variant_interpretation else (disease_nodes[0][0] if disease_nodes else matching_node_id)
        edges.append({
            "id": f"e-{source_id}-{node_id}",
            "source": source_id,
            "target": node_id,
            "label": rec.urgency or "routine"
        })

    return {
        "nodes": nodes,
        "edges": edges
    }


@router.get("/workflow-data/{scenario_id}")
async def get_workflow_data(scenario_id: str) -> Dict[str, Any]:
    """Get React Flow compatible workflow graph data for a processed scenario.

    Args:
        scenario_id: Unique scenario identifier

    Returns:
        Graph structure with nodes and edges showing the clinical reasoning workflow

    Raises:
        HTTPException: If scenario not found
    """
    if scenario_id not in _scenario_cache:
        raise HTTPException(
            status_code=404,
            detail=f"Scenario {scenario_id} not found. Process a scenario first."
        )

    scenario_response = _scenario_cache[scenario_id]
    graph_data = build_workflow_graph(scenario_response)

    return {
        "scenario_id": scenario_id,
        "workflow": graph_data
    }
