/**
 * TypeScript types mirroring Python Pydantic models
 * from backend/core/clinical_scenario.py
 */

export type Sex = "male" | "female" | "other";

export interface Patient {
  age: string;
  sex: Sex;
  ethnicity?: string;
  family_history?: string;
}

export interface LabResult {
  test_name: string;
  value: string;
  unit: string;
  normal_range?: string;
  interpretation?: string;
}

export interface GeneticFinding {
  gene: string;
  variant?: string;
  variant_type?: string; // deletion, duplication, point mutation
  exons_affected?: number[];
  zygosity?: string; // homozygous, heterozygous, hemizygous
  inheritance_pattern?: string;
}

export interface ClinicalScenario {
  scenario_id?: string;
  timestamp?: string;

  // Patient demographics
  patient: Patient;

  // Clinical presentation
  chief_complaint: string;
  presenting_symptoms: string[];
  symptom_onset?: string;
  progression_pattern?: string; // static, slowly progressive, rapidly progressive

  // Physical examination findings
  physical_exam?: Record<string, string>;

  // Laboratory findings
  lab_results?: LabResult[];

  // Genetic testing
  genetic_findings?: GeneticFinding[];

  // Imaging findings
  imaging_findings?: Record<string, string>;

  // Specific clinical questions
  clinical_questions?: string[];

  // Previous evaluations
  prior_diagnoses?: string[];
  current_medications?: string[];
}

export interface DifferentialDiagnosis {
  disease_name: string;
  confidence_score: number; // 0-100
  supporting_features: string[];
  inconsistent_features?: string[];
  recommended_tests: string[];
  key_distinguishing_features?: string[];
}

export interface ClinicalRecommendation {
  category: string; // diagnosis, treatment, surveillance, genetic_counseling
  recommendation: string;
  evidence_level?: string; // Level A, B, C
  references?: string[];
  urgency?: string; // immediate, urgent, routine

  // RAG-specific fields (only present for RAG-sourced recommendations)
  source_type?: "static" | "RAG"; // Source: static (clinical_data.py) or RAG (Gemini File Search)
  citation?: string; // File URI or citation for RAG-sourced recommendations
  confidence?: number; // Confidence score 0.0-1.0 for RAG-sourced recommendations
  chunk_id?: string; // Grounding chunk identifier for RAG-sourced recommendations
  retrieved_text?: string; // Actual text passage retrieved from clinical guideline
}

export interface MonarchMatch {
  disease_id: string;
  disease_name: string;
  match_count: number; // Number of HPO terms matched
  matched_hpo_ids: string[];
  code?: string; // Project disease code (DMD, BMD, etc.) if mapped
}

export interface MonarchSearchSummary {
  total_diseases_found: number;
  hpo_ids_searched: string[];
  diseases_by_match_count: Record<string, number>; // e.g., {"2": 8, "1": 84}
}

export interface ScoringComponent {
  component_name: string;
  points_added: number;
  reasoning: string;
}

export interface ScoringBreakdown {
  disease_code: string;
  disease_name: string;
  base_score: number;
  scoring_components: ScoringComponent[];
  final_score: number;
  included_in_differential: boolean;
  exclusion_reason?: string;
}

export interface ScenarioResponse {
  scenario_id: string;
  processing_timestamp: string;

  // Differential diagnosis
  differential_diagnoses: DifferentialDiagnosis[];
  primary_diagnosis?: string;

  // Variant interpretation (if genetic data provided)
  variant_interpretation?: Record<string, any>;

  // Clinical recommendations
  recommendations: ClinicalRecommendation[];

  // Answers to specific questions
  question_answers: Record<string, string>;

  // Supporting evidence and references
  evidence_summary?: string;
  key_references?: string[];

  // Confidence and limitations
  overall_confidence?: number;
  limitations?: string[];

  // ═══════════════════════════════════════════════════════════════
  // NEW: Enhanced reasoning flow data for visualization
  // ═══════════════════════════════════════════════════════════════

  // HPO mappings: symptom → standardized HPO terms
  hpo_mappings?: HPOMapping[];

  // Monarch search results
  monarch_search_summary?: MonarchSearchSummary;

  // Top diseases from Monarch (for graph visualization)
  top_monarch_matches?: MonarchMatch[];

  // Detailed scoring breakdown for all diseases
  scoring_details?: ScoringBreakdown[];
}

export interface HPOMapping {
  clinical_feature: string;
  hpo_id: string;
  hpo_term: string;
  specificity_score?: number;
}

// Workflow visualization types
export interface WorkflowNode {
  id: string;
  type: string;
  position: { x: number; y: number };
  data: Record<string, any>;
}

export interface WorkflowEdge {
  id: string;
  source: string;
  target: string;
  label?: string;
  animated?: boolean;
  data?: Record<string, any>;
}

export interface WorkflowData {
  scenario_id: string;
  workflow: {
    nodes: WorkflowNode[];
    edges: WorkflowEdge[];
  };
}
