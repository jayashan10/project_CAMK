"""
Clinical Scenario Processor - Main orchestration logic
"""
from typing import List, Dict, Optional
from datetime import datetime
from .clinical_scenario import (
    ClinicalScenario,
    ScenarioResponse,
    DifferentialDiagnosis,
    ClinicalRecommendation,
    GeneticFinding,
    extract_hpo_terms,
    calculate_phenotype_similarity
)


class ScenarioProcessor:
    """
    Processes clinical scenarios and generates comprehensive responses
    """

    def __init__(self):
        # In production, these would come from knowledge graph
        self.disease_profiles = self._initialize_disease_profiles()
        self.treatment_database = self._initialize_treatments()
        self.diagnostic_pathways = self._initialize_diagnostic_pathways()

    def process_scenario(self, scenario: ClinicalScenario) -> ScenarioResponse:
        """
        Main processing pipeline for clinical scenarios
        """
        # Step 1: Extract clinical features and map to HPO terms
        hpo_terms = extract_hpo_terms(scenario.presenting_symptoms)

        # Step 2: Generate differential diagnosis
        differential = self._generate_differential_diagnosis(scenario, hpo_terms)

        # Step 3: Interpret genetic findings if present
        variant_interpretation = None
        if scenario.genetic_findings:
            variant_interpretation = self._interpret_variants(
                scenario.genetic_findings,
                differential[0].disease_name if differential else None
            )

        # Step 4: Generate clinical recommendations
        recommendations = self._generate_recommendations(
            scenario,
            differential[0] if differential else None,
            variant_interpretation
        )

        # Step 5: Answer specific clinical questions
        question_answers = self._answer_clinical_questions(
            scenario.clinical_questions,
            differential,
            variant_interpretation,
            recommendations
        )

        # Step 6: Compile response
        return ScenarioResponse(
            scenario_id=scenario.scenario_id or f"scenario_{datetime.now().timestamp()}",
            differential_diagnoses=differential,
            primary_diagnosis=differential[0].disease_name if differential else None,
            variant_interpretation=variant_interpretation,
            recommendations=recommendations,
            question_answers=question_answers,
            overall_confidence=differential[0].confidence_score if differential else 0,
            limitations=self._identify_limitations(scenario)
        )

    def _generate_differential_diagnosis(
        self,
        scenario: ClinicalScenario,
        hpo_terms
    ) -> List[DifferentialDiagnosis]:
        """
        Generate differential diagnosis based on clinical presentation
        """
        differentials = []

        for disease, profile in self.disease_profiles.items():
            # Calculate match score based on clinical features
            score = self._calculate_disease_match_score(scenario, profile)

            # Additional scoring factors
            if scenario.patient.sex == "male" and profile.get("inheritance") == "X-linked":
                score += 10

            if scenario.lab_results:
                for lab in scenario.lab_results:
                    if lab.test_name == "Creatine Kinase" and "elevated" in lab.interpretation.lower():
                        if disease in ["DMD", "BMD", "LGMD"]:
                            score += 15

            # Age-based adjustments
            age_value = self._extract_age_years(scenario.patient.age)
            if age_value:
                if disease == "DMD" and 3 <= age_value <= 8:
                    score += 10
                elif disease == "BMD" and age_value > 10:
                    score += 10
                elif disease == "LAMA2-CMD" and age_value < 2:
                    score += 15

            # Create differential diagnosis entry
            if score > 30:  # Minimum threshold
                diff = DifferentialDiagnosis(
                    disease_name=disease,
                    confidence_score=min(score, 95),
                    supporting_features=self._get_supporting_features(scenario, profile),
                    inconsistent_features=self._get_inconsistent_features(scenario, profile),
                    recommended_tests=profile.get("diagnostic_tests", [])
                )
                differentials.append(diff)

        # Sort by confidence score
        differentials.sort(key=lambda x: x.confidence_score, reverse=True)
        return differentials[:5]  # Return top 5

    def _interpret_variants(
        self,
        genetic_findings: List[GeneticFinding],
        primary_diagnosis: Optional[str]
    ) -> Dict:
        """
        Interpret genetic variants in clinical context
        """
        interpretations = {}

        for finding in genetic_findings:
            if finding.gene == "DMD":
                interpretation = self._interpret_dmd_variant(finding, primary_diagnosis)
                interpretations[f"{finding.gene}_{finding.variant}"] = interpretation
            # Add other gene interpretations as needed

        return interpretations

    def _interpret_dmd_variant(self, finding: GeneticFinding, clinical_context: str) -> Dict:
        """
        DMD-specific variant interpretation
        """
        interpretation = {
            "gene": finding.gene,
            "variant": finding.variant,
            "variant_type": finding.variant_type
        }

        if finding.variant_type == "deletion" and finding.exons_affected:
            # Reading frame analysis
            reading_frame = self._check_reading_frame(finding.exons_affected)
            interpretation["reading_frame"] = reading_frame

            if reading_frame == "out-of-frame":
                interpretation["predicted_phenotype"] = "Duchenne Muscular Dystrophy"
                interpretation["severity"] = "severe"
            else:
                interpretation["predicted_phenotype"] = "Becker Muscular Dystrophy"
                interpretation["severity"] = "mild to moderate"

            # Treatment eligibility
            eligible_treatments = []
            if 45 in finding.exons_affected:
                eligible_treatments.append("Casimersen (Amondys 45)")
            if 51 in finding.exons_affected:
                eligible_treatments.append("Eteplirsen (Exondys 51)")
            if 53 in finding.exons_affected:
                eligible_treatments.extend(["Golodirsen (Vyondys 53)", "Viltolarsen (Viltepso)"])

            interpretation["eligible_treatments"] = eligible_treatments

        return interpretation

    def _check_reading_frame(self, exons_affected: List[int]) -> str:
        """
        Simplified reading frame checker for DMD deletions
        """
        # This is a simplified version - real implementation would use
        # actual exon boundaries and reading frame rules

        # Common out-of-frame deletions
        out_of_frame_patterns = [
            [45, 46, 47],  # Out-of-frame
            [3, 4, 5, 6, 7],  # Out-of-frame
            [48, 49, 50],  # Out-of-frame
        ]

        # Common in-frame deletions
        in_frame_patterns = [
            [45],  # In-frame (single exon)
            [48, 49],  # In-frame
            [45, 46, 47, 48],  # In-frame
        ]

        if exons_affected in out_of_frame_patterns:
            return "out-of-frame"
        elif exons_affected in in_frame_patterns:
            return "in-frame"
        else:
            # Default logic: deletions starting/ending at specific exons
            # This is oversimplified - real implementation needs exon boundary data
            if len(exons_affected) % 3 == 0:
                return "in-frame"
            else:
                return "out-of-frame"

    def _generate_recommendations(
        self,
        scenario: ClinicalScenario,
        primary_diagnosis: Optional[DifferentialDiagnosis],
        variant_interpretation: Optional[Dict]
    ) -> List[ClinicalRecommendation]:
        """
        Generate clinical recommendations based on diagnosis
        """
        recommendations = []

        if not primary_diagnosis:
            # General recommendations when diagnosis uncertain
            recommendations.append(
                ClinicalRecommendation(
                    category="diagnosis",
                    recommendation="Consider comprehensive neuromuscular panel genetic testing",
                    urgency="routine"
                )
            )
            return recommendations

        disease = primary_diagnosis.disease_name

        if disease == "DMD":
            # DMD-specific recommendations
            recommendations.extend([
                ClinicalRecommendation(
                    category="treatment",
                    recommendation="Initiate corticosteroid therapy (prednisone 0.75 mg/kg/day or deflazacort 0.9 mg/kg/day)",
                    evidence_level="Level A",
                    references=["Birnkrant et al., Lancet Neurol 2018"],
                    urgency="urgent"
                ),
                ClinicalRecommendation(
                    category="surveillance",
                    recommendation="Baseline cardiac evaluation (ECG and echocardiogram)",
                    evidence_level="Level A",
                    urgency="urgent"
                ),
                ClinicalRecommendation(
                    category="surveillance",
                    recommendation="Pulmonary function testing (baseline)",
                    evidence_level="Level A",
                    urgency="routine"
                ),
                ClinicalRecommendation(
                    category="treatment",
                    recommendation="Physical therapy referral for stretching and contracture prevention",
                    evidence_level="Level B",
                    urgency="routine"
                ),
                ClinicalRecommendation(
                    category="genetic_counseling",
                    recommendation="Genetic counseling for family members (X-linked inheritance)",
                    evidence_level="Level A",
                    urgency="routine"
                )
            ])

            # Add treatment-specific recommendations if eligible
            if variant_interpretation:
                for variant_data in variant_interpretation.values():
                    if variant_data.get("eligible_treatments"):
                        for treatment in variant_data["eligible_treatments"]:
                            recommendations.append(
                                ClinicalRecommendation(
                                    category="treatment",
                                    recommendation=f"Patient is eligible for {treatment} - consider referral to neuromuscular specialist",
                                    evidence_level="Level A",
                                    urgency="urgent"
                                )
                            )

        elif disease == "BMD":
            recommendations.extend([
                ClinicalRecommendation(
                    category="surveillance",
                    recommendation="Annual cardiac evaluation (critical - cardiomyopathy can occur independent of skeletal muscle involvement)",
                    evidence_level="Level A",
                    urgency="urgent"
                ),
                ClinicalRecommendation(
                    category="treatment",
                    recommendation="Consider ACE inhibitor or ARB for cardiac protection",
                    evidence_level="Level B",
                    urgency="routine"
                )
            ])

        elif disease == "LGMD":
            recommendations.extend([
                ClinicalRecommendation(
                    category="diagnosis",
                    recommendation="Genetic testing for CAPN3 mutations (LGMD R1/2A)",
                    urgency="routine"
                ),
                ClinicalRecommendation(
                    category="surveillance",
                    recommendation="Regular muscle strength assessment",
                    urgency="routine"
                )
            ])

        return recommendations

    def _answer_clinical_questions(
        self,
        questions: List[str],
        differential: List[DifferentialDiagnosis],
        variant_interpretation: Optional[Dict],
        recommendations: List[ClinicalRecommendation]
    ) -> Dict[str, str]:
        """
        Answer specific clinical questions
        """
        answers = {}

        for question in questions:
            question_lower = question.lower()

            if "diagnosis" in question_lower or "likely" in question_lower:
                if differential:
                    answers[question] = (
                        f"Most likely diagnosis: {differential[0].disease_name} "
                        f"(confidence: {differential[0].confidence_score:.1f}%). "
                        f"Key supporting features: {', '.join(differential[0].supporting_features[:3])}"
                    )
                else:
                    answers[question] = "Insufficient information for definitive diagnosis. Consider genetic testing."

            elif "duchenne" in question_lower and "becker" in question_lower:
                if variant_interpretation:
                    for variant_data in variant_interpretation.values():
                        if "predicted_phenotype" in variant_data:
                            answers[question] = (
                                f"Based on the {variant_data['reading_frame']} deletion, "
                                f"this is consistent with {variant_data['predicted_phenotype']}. "
                                f"Expected severity: {variant_data['severity']}."
                            )
                            break
                else:
                    answers[question] = "Genetic analysis needed to distinguish DMD from BMD based on reading frame."

            elif "treatment" in question_lower:
                treatment_recs = [r for r in recommendations if r.category == "treatment"]
                if treatment_recs:
                    answers[question] = " ".join([r.recommendation for r in treatment_recs[:2]])
                else:
                    answers[question] = "Treatment recommendations depend on confirmed diagnosis."

            elif "surveillance" in question_lower or "monitor" in question_lower:
                surveillance_recs = [r for r in recommendations if r.category == "surveillance"]
                if surveillance_recs:
                    answers[question] = " ".join([r.recommendation for r in surveillance_recs])
                else:
                    answers[question] = "Surveillance recommendations depend on confirmed diagnosis."

            elif "prognosis" in question_lower:
                if differential and differential[0].disease_name == "DMD":
                    answers[question] = (
                        "DMD typically leads to wheelchair dependence by age 12 and "
                        "life expectancy of 20s-30s with standard care. Early treatment "
                        "and cardiac management can improve outcomes."
                    )
                elif differential and differential[0].disease_name == "BMD":
                    answers[question] = (
                        "BMD has a milder course with ambulation into 30s-50s and "
                        "near-normal life expectancy. Cardiac surveillance is critical."
                    )
                else:
                    answers[question] = "Prognosis depends on specific diagnosis."

        return answers

    def _calculate_disease_match_score(self, scenario: ClinicalScenario, profile: Dict) -> float:
        """Calculate match score between scenario and disease profile"""
        score = 0.0

        # Match symptoms
        for symptom in scenario.presenting_symptoms:
            symptom_lower = symptom.lower()
            for key_feature in profile.get("key_features", []):
                if key_feature.lower() in symptom_lower:
                    score += 20

        # Match onset age
        age_years = self._extract_age_years(scenario.patient.age)
        if age_years and "typical_onset" in profile:
            onset_range = profile["typical_onset"]
            if onset_range[0] <= age_years <= onset_range[1]:
                score += 15

        return score

    def _extract_age_years(self, age_str: str) -> Optional[float]:
        """Extract numeric age in years from age string"""
        try:
            if "year" in age_str.lower():
                return float(age_str.split()[0])
            elif "month" in age_str.lower():
                return float(age_str.split()[0]) / 12
            return None
        except:
            return None

    def _get_supporting_features(self, scenario: ClinicalScenario, profile: Dict) -> List[str]:
        """Get features that support the diagnosis"""
        supporting = []

        for symptom in scenario.presenting_symptoms:
            symptom_lower = symptom.lower()
            for feature in profile.get("key_features", []):
                if feature.lower() in symptom_lower:
                    supporting.append(symptom)
                    break

        # Add lab findings
        if scenario.lab_results:
            for lab in scenario.lab_results:
                if "elevated" in str(lab.interpretation).lower():
                    supporting.append(f"Elevated {lab.test_name}")

        return supporting

    def _get_inconsistent_features(self, scenario: ClinicalScenario, profile: Dict) -> List[str]:
        """Get features that are inconsistent with the diagnosis"""
        # Simplified - would be more comprehensive in production
        return []

    def _identify_limitations(self, scenario: ClinicalScenario) -> List[str]:
        """Identify limitations in the analysis"""
        limitations = []

        if not scenario.genetic_findings:
            limitations.append("No genetic data available - interpretation based on clinical features only")

        if not scenario.imaging_findings:
            limitations.append("No imaging data available")

        if not scenario.family_history:
            limitations.append("Family history not provided - inheritance pattern unclear")

        return limitations

    def _initialize_disease_profiles(self) -> Dict:
        """Initialize disease profiles (simplified version)"""
        return {
            "DMD": {
                "key_features": ["proximal weakness", "gowers sign", "calf pseudohypertrophy", "elevated CK"],
                "typical_onset": [3, 8],
                "inheritance": "X-linked",
                "diagnostic_tests": ["DMD gene deletion/duplication analysis", "DMD gene sequencing", "Muscle biopsy"]
            },
            "BMD": {
                "key_features": ["proximal weakness", "calf pseudohypertrophy", "elevated CK", "preserved ambulation"],
                "typical_onset": [10, 30],
                "inheritance": "X-linked",
                "diagnostic_tests": ["DMD gene analysis", "Cardiac MRI", "ECG"]
            },
            "LGMD": {
                "key_features": ["proximal weakness", "scapular winging", "elevated CK", "no cardiac involvement"],
                "typical_onset": [5, 40],
                "inheritance": "Autosomal recessive/dominant",
                "diagnostic_tests": ["CAPN3 gene testing", "Muscle MRI", "Muscle biopsy"]
            },
            "LAMA2-CMD": {
                "key_features": ["hypotonia", "weakness from birth", "white matter changes", "elevated CK"],
                "typical_onset": [0, 1],
                "inheritance": "Autosomal recessive",
                "diagnostic_tests": ["LAMA2 gene testing", "Brain MRI", "Muscle biopsy with merosin staining"]
            }
        }

    def _initialize_treatments(self) -> Dict:
        """Initialize treatment database"""
        return {
            "DMD": {
                "corticosteroids": {
                    "drugs": ["prednisone", "deflazacort"],
                    "evidence": "Level A"
                },
                "exon_skipping": {
                    "exon_45": "Casimersen",
                    "exon_51": "Eteplirsen",
                    "exon_53": ["Golodirsen", "Viltolarsen"]
                },
                "gene_therapy": ["Elevidys"],
                "nonsense_suppression": ["Ataluren"]
            },
            "BMD": {
                "cardiac": ["ACE inhibitors", "Beta blockers", "ARBs"],
                "supportive": ["Physical therapy", "Occupational therapy"]
            }
        }

    def _initialize_diagnostic_pathways(self) -> Dict:
        """Initialize diagnostic pathways"""
        return {
            "elevated_ck_pathway": [
                "Clinical evaluation",
                "Family history",
                "CK level confirmation",
                "Genetic testing (DMD gene first if male)",
                "Consider muscle biopsy if genetic testing negative"
            ],
            "infant_hypotonia_pathway": [
                "Rule out central causes",
                "CK level",
                "Brain MRI (look for white matter changes)",
                "Genetic panel for congenital myopathies",
                "Consider LAMA2 testing if white matter changes present"
            ]
        }