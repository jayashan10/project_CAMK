"""API endpoints for clinical scenario processing."""
import uuid
from typing import Dict
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime

from backend.core.clinical_scenario import ClinicalScenario, ScenarioResponse
from backend.core.scenario_processor import ScenarioProcessor
from backend.knowledge_graph.service import KnowledgeGraphService
from backend.api.dependencies import get_kg_service

router = APIRouter()

# In-memory cache for processed scenarios (for workflow endpoint)
# In production, this would be a proper cache/database
_scenario_cache: Dict[str, ScenarioResponse] = {}


@router.post("/scenarios/process", response_model=ScenarioResponse)
async def process_scenario(
    scenario: ClinicalScenario,
    kg_service: KnowledgeGraphService = Depends(get_kg_service),
) -> ScenarioResponse:
    """Process a clinical scenario and return diagnostic recommendations.

    Args:
        scenario: Clinical scenario with patient data, symptoms, labs, and genetic findings
        kg_service: Knowledge graph service (injected)

    Returns:
        Comprehensive clinical decision support response including:
        - Differential diagnoses with confidence scores
        - Variant interpretation (if genetic data provided)
        - Clinical recommendations with evidence levels
        - Answers to specific clinical questions

    Raises:
        HTTPException: If processing fails
    """
    try:
        # Generate scenario ID if not provided
        if not scenario.scenario_id:
            scenario.scenario_id = str(uuid.uuid4())

        # Initialize scenario processor with knowledge graph service
        processor = ScenarioProcessor(knowledge_service=kg_service)

        # Process the scenario
        response = processor.process_scenario(scenario)

        # Cache the response for workflow endpoint
        _scenario_cache[response.scenario_id] = response

        return response

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing scenario: {str(e)}"
        ) from e


@router.get("/scenarios/{scenario_id}", response_model=ScenarioResponse)
async def get_scenario(scenario_id: str) -> ScenarioResponse:
    """Retrieve a previously processed scenario.

    Args:
        scenario_id: Unique scenario identifier

    Returns:
        Cached scenario response

    Raises:
        HTTPException: If scenario not found
    """
    if scenario_id not in _scenario_cache:
        raise HTTPException(
            status_code=404,
            detail=f"Scenario {scenario_id} not found"
        )

    return _scenario_cache[scenario_id]
