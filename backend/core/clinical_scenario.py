"""
Clinical Scenario Data Models and Processing
"""
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


class Sex(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class Patient(BaseModel):
    age: str = Field(..., description="Patient age (e.g., '8 years', '6 months')")
    sex: Sex
    ethnicity: Optional[str] = None
    family_history: Optional[str] = None


class LabResult(BaseModel):
    test_name: str
    value: str
    unit: str
    normal_range: Optional[str] = None
    interpretation: Optional[str] = None


class GeneticFinding(BaseModel):
    gene: str
    variant: Optional[str] = None
    variant_type: Optional[str] = None  # deletion, duplication, point mutation
    exons_affected: Optional[List[int]] = None
    zygosity: Optional[str] = None  # homozygous, heterozygous, hemizygous
    inheritance_pattern: Optional[str] = None


class ClinicalScenario(BaseModel):
    """
    Comprehensive clinical scenario input model
    """
    scenario_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

    # Patient demographics
    patient: Patient

    # Clinical presentation
    chief_complaint: str
    presenting_symptoms: List[str]
    symptom_onset: Optional[str] = None
    progression_pattern: Optional[str] = None  # static, slowly progressive, rapidly progressive

    # Physical examination findings
    physical_exam: Optional[Dict[str, str]] = None

    # Laboratory findings
    lab_results: Optional[List[LabResult]] = None

    # Genetic testing
    genetic_findings: Optional[List[GeneticFinding]] = None

    # Imaging findings
    imaging_findings: Optional[Dict[str, str]] = None

    # Specific clinical questions
    clinical_questions: List[str] = Field(
        default_factory=lambda: [
            "What is the most likely diagnosis?",
            "What additional testing is recommended?",
            "What treatment options are available?",
            "What is the prognosis?"
        ]
    )

    # Previous evaluations
    prior_diagnoses: Optional[List[str]] = None
    current_medications: Optional[List[str]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "patient": {
                    "age": "7 years",
                    "sex": "male",
                    "family_history": "Maternal uncle used wheelchair by age 15"
                },
                "chief_complaint": "Progressive difficulty walking",
                "presenting_symptoms": [
                    "Frequent falls",
                    "Difficulty climbing stairs",
                    "Toe walking",
                    "Calf muscle enlargement"
                ],
                "symptom_onset": "Age 4 years",
                "progression_pattern": "slowly progressive",
                "physical_exam": {
                    "gowers_sign": "positive",
                    "proximal_weakness": "4/5 hip flexors, 4/5 shoulder abduction",
                    "calf_muscles": "pseudohypertrophy noted",
                    "reflexes": "diminished throughout"
                },
                "lab_results": [
                    {
                        "test_name": "Creatine Kinase",
                        "value": "12000",
                        "unit": "U/L",
                        "normal_range": "30-200",
                        "interpretation": "Markedly elevated"
                    },
                    {
                        "test_name": "AST",
                        "value": "250",
                        "unit": "U/L",
                        "normal_range": "10-40"
                    }
                ],
                "genetic_findings": [
                    {
                        "gene": "DMD",
                        "variant_type": "deletion",
                        "exons_affected": [45, 46, 47],
                        "zygosity": "hemizygous"
                    }
                ],
                "clinical_questions": [
                    "Is this Duchenne or Becker muscular dystrophy?",
                    "What treatments are available?",
                    "What surveillance is needed?"
                ]
            }
        }


class DifferentialDiagnosis(BaseModel):
    """
    Differential diagnosis output model
    """
    disease_name: str
    confidence_score: float = Field(..., ge=0, le=100)
    supporting_features: List[str]
    inconsistent_features: Optional[List[str]] = None
    recommended_tests: List[str]
    key_distinguishing_features: Optional[List[str]] = None


class ClinicalRecommendation(BaseModel):
    """
    Clinical recommendation output (enhanced with RAG support)
    """
    category: str  # diagnosis, treatment, surveillance, genetic_counseling
    recommendation: str
    evidence_level: Optional[str] = None  # Level A, B, C
    references: Optional[List[str]] = None
    urgency: Optional[str] = None  # immediate, urgent, routine

    # RAG-specific fields (optional, only present for RAG-sourced recommendations)
    source_type: Optional[str] = Field(
        default="static",
        description="Source of recommendation: 'static' (clinical_data.py) or 'RAG' (Gemini File Search)"
    )
    citation: Optional[str] = Field(
        default=None,
        description="File URI or citation for RAG-sourced recommendations"
    )
    confidence: Optional[float] = Field(
        default=None,
        ge=0,
        le=1,
        description="Confidence score for RAG-sourced recommendations (0.0-1.0)"
    )
    chunk_id: Optional[str] = Field(
        default=None,
        description="Grounding chunk identifier for RAG-sourced recommendations"
    )
    retrieved_text: Optional[str] = Field(
        default=None,
        description="Actual text passage retrieved from clinical guideline (for RAG-sourced recommendations)"
    )


class HPOMapping(BaseModel):
    """
    Human Phenotype Ontology term mapping
    """
    clinical_feature: str
    hpo_id: str
    hpo_term: str
    specificity_score: Optional[float] = None  # How specific this feature is for certain diseases


class MonarchMatch(BaseModel):
    """Individual disease match from Monarch knowledge graph"""
    disease_id: str
    disease_name: str
    match_count: int = Field(..., description="Number of HPO terms matched")
    matched_hpo_ids: List[str]
    code: Optional[str] = None  # Project disease code (DMD, BMD, etc.) if mapped


class MonarchSearchSummary(BaseModel):
    """Summary of Monarch knowledge graph search results"""
    total_diseases_found: int
    hpo_ids_searched: List[str]
    diseases_by_match_count: Dict[str, int] = Field(
        description="Breakdown like {'2': 8, '1': 84}"
    )


class ScoringComponent(BaseModel):
    """Individual component of disease scoring"""
    component_name: str
    points_added: float
    reasoning: str


class ScoringBreakdown(BaseModel):
    """Detailed scoring breakdown for a disease"""
    disease_code: str
    disease_name: str
    base_score: float
    scoring_components: List[ScoringComponent]
    final_score: float
    included_in_differential: bool
    exclusion_reason: Optional[str] = None


class ScenarioResponse(BaseModel):
    """
    Comprehensive response to clinical scenario
    """
    scenario_id: str
    processing_timestamp: datetime = Field(default_factory=datetime.now)

    # Differential diagnosis
    differential_diagnoses: List[DifferentialDiagnosis]
    primary_diagnosis: Optional[str] = None

    # Variant interpretation (if genetic data provided)
    variant_interpretation: Optional[Dict[str, Any]] = None

    # Clinical recommendations
    recommendations: List[ClinicalRecommendation]

    # Answers to specific questions
    question_answers: Dict[str, str]

    # Supporting evidence and references
    evidence_summary: Optional[str] = None
    key_references: Optional[List[str]] = None

    # Confidence and limitations
    overall_confidence: Optional[float] = None
    limitations: Optional[List[str]] = None

    # ═══════════════════════════════════════════════════════════════
    # NEW: Enhanced reasoning flow data for visualization
    # ═══════════════════════════════════════════════════════════════

    # HPO mappings: symptom → standardized HPO terms
    hpo_mappings: Optional[List[HPOMapping]] = Field(
        default=None,
        description="Clinical features mapped to HPO terms"
    )

    # Monarch search results
    monarch_search_summary: Optional[MonarchSearchSummary] = Field(
        default=None,
        description="Summary of diseases found in Monarch knowledge graph"
    )

    # Top diseases from Monarch (for graph visualization)
    top_monarch_matches: Optional[List[MonarchMatch]] = Field(
        default=None,
        description="Top 20 diseases from Monarch knowledge graph search"
    )

    # Detailed scoring breakdown for all diseases
    scoring_details: Optional[List[ScoringBreakdown]] = Field(
        default=None,
        description="Detailed scoring for all evaluated diseases"
    )


# Common phenotype patterns for muscular dystrophies
MUSCULAR_DYSTROPHY_PHENOTYPES = {
    "proximal_weakness": HPOMapping(
        clinical_feature="Proximal muscle weakness",
        hpo_id="HP:0003701",
        hpo_term="Proximal muscle weakness",
        specificity_score=0.6
    ),
    "gowers_sign": HPOMapping(
        clinical_feature="Gowers sign",
        hpo_id="HP:0003391",
        hpo_term="Gowers sign",
        specificity_score=0.85
    ),
    "calf_pseudohypertrophy": HPOMapping(
        clinical_feature="Calf pseudohypertrophy",
        hpo_id="HP:0003707",
        hpo_term="Calf muscle pseudohypertrophy",
        specificity_score=0.9
    ),
    "elevated_ck": HPOMapping(
        clinical_feature="Elevated CK",
        hpo_id="HP:0003236",
        hpo_term="Elevated serum creatine kinase",
        specificity_score=0.4
    ),
    "cardiomyopathy": HPOMapping(
        clinical_feature="Cardiomyopathy",
        hpo_id="HP:0001638",
        hpo_term="Cardiomyopathy",
        specificity_score=0.7
    ),
    "respiratory_insufficiency": HPOMapping(
        clinical_feature="Respiratory insufficiency",
        hpo_id="HP:0002093",
        hpo_term="Respiratory insufficiency",
        specificity_score=0.5
    )
}


def extract_hpo_terms(symptoms: List[str]) -> List[HPOMapping]:
    """
    Extract HPO terms from clinical symptoms
    This is a simplified version - in production would use NLP/ontology matching
    """
    hpo_terms = []
    symptom_keywords = {
        "weakness": ["weak", "weakness", "difficulty"],
        "gowers": ["gowers", "floor", "standing"],
        "pseudohypertrophy": ["enlarged", "pseudohypertrophy", "calf"],
        "ck": ["ck", "creatine kinase", "cpk"],
        "heart": ["cardiac", "cardiomyopathy", "heart"],
        "breathing": ["respiratory", "breathing", "ventilation"]
    }

    for symptom in symptoms:
        symptom_lower = symptom.lower()
        for pattern, keywords in symptom_keywords.items():
            if any(keyword in symptom_lower for keyword in keywords):
                if pattern == "weakness" and "proximal" in symptom_lower:
                    hpo_terms.append(MUSCULAR_DYSTROPHY_PHENOTYPES["proximal_weakness"])
                elif pattern == "gowers":
                    hpo_terms.append(MUSCULAR_DYSTROPHY_PHENOTYPES["gowers_sign"])
                elif pattern == "pseudohypertrophy":
                    hpo_terms.append(MUSCULAR_DYSTROPHY_PHENOTYPES["calf_pseudohypertrophy"])
                # Add more mappings as needed

    return hpo_terms


def calculate_phenotype_similarity(
    patient_phenotypes: List[HPOMapping],
    disease_phenotypes: List[HPOMapping]
) -> float:
    """
    Calculate similarity score between patient and disease phenotypes
    """
    if not patient_phenotypes or not disease_phenotypes:
        return 0.0

    patient_hpo_ids = {p.hpo_id for p in patient_phenotypes}
    disease_hpo_ids = {d.hpo_id for d in disease_phenotypes}

    # Simple Jaccard similarity - in production would use semantic similarity
    intersection = len(patient_hpo_ids & disease_hpo_ids)
    union = len(patient_hpo_ids | disease_hpo_ids)

    if union == 0:
        return 0.0

    return (intersection / union) * 100