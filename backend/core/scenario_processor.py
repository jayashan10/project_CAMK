"""Clinical Scenario Processor - Main orchestration logic backed by knowledge graph."""
from typing import Dict, List, Optional
from datetime import datetime

from backend.knowledge_graph.service import KnowledgeGraphService

from .clinical_scenario import (
    ClinicalScenario,
    ScenarioResponse,
    DifferentialDiagnosis,
    ClinicalRecommendation,
    GeneticFinding,
    extract_hpo_terms,
    calculate_phenotype_similarity,
)


class ScenarioProcessor:
    """Processes clinical scenarios and generates comprehensive responses."""

    def __init__(self, knowledge_service: Optional[KnowledgeGraphService] = None):
        self.knowledge_service = knowledge_service or KnowledgeGraphService()
        self.knowledge_service.ensure_schema()
        self.knowledge_service.seed()

        # Cache frequently used knowledge for faster access during processing
        self.disease_profiles = self.knowledge_service.get_disease_profiles()
        self.general_recommendations = self.knowledge_service.get_general_recommendations()

    def process_scenario(self, scenario: ClinicalScenario) -> ScenarioResponse:
        """Main processing pipeline for clinical scenarios."""
        # Step 1: Extract clinical features and map to HPO terms
        hpo_terms = extract_hpo_terms(scenario.presenting_symptoms)

        # Step 2: Generate differential diagnosis
        differential = self._generate_differential_diagnosis(scenario, hpo_terms)

        # Step 3: Interpret genetic findings if present
        variant_interpretation = None
        if scenario.genetic_findings:
            variant_interpretation = self._interpret_variants(
                scenario.genetic_findings,
                differential[0].disease_name if differential else None,
            )

        # Step 4: Generate clinical recommendations
        recommendations = self._generate_recommendations(
            scenario,
            differential[0] if differential else None,
            variant_interpretation,
        )

        # Step 5: Answer specific clinical questions
        question_answers = self._answer_clinical_questions(
            scenario.clinical_questions,
            differential,
            variant_interpretation,
            recommendations,
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
            limitations=self._identify_limitations(scenario),
        )

    def _generate_differential_diagnosis(
        self,
        scenario: ClinicalScenario,
        hpo_terms,
    ) -> List[DifferentialDiagnosis]:
        """Generate differential diagnosis based on clinical presentation."""
        differentials = []

        for disease_code, profile in self.disease_profiles.items():
            score = self._calculate_disease_match_score(scenario, profile)

            if scenario.patient.sex == "male" and profile.get("inheritance") == "X-linked":
                score += 10

            if scenario.lab_results:
                for lab in scenario.lab_results:
                    if (
                        lab.test_name == "Creatine Kinase"
                        and lab.interpretation
                        and "elevated" in lab.interpretation.lower()
                        and disease_code in ["DMD", "BMD", "LGMD"]
                    ):
                        score += 15

            age_value = self._extract_age_years(scenario.patient.age)
            if age_value is not None:
                if disease_code == "DMD" and 3 <= age_value <= 8:
                    score += 10
                elif disease_code == "BMD" and age_value > 10:
                    score += 10
                elif disease_code == "LAMA2-CMD" and age_value < 2:
                    score += 15

            if score > 30:
                diff = DifferentialDiagnosis(
                    disease_name=disease_code,
                    confidence_score=min(score, 95),
                    supporting_features=self._get_supporting_features(scenario, profile),
                    inconsistent_features=self._get_inconsistent_features(scenario, profile),
                    recommended_tests=profile.get("diagnostic_tests", []),
                )
                differentials.append(diff)

        differentials.sort(key=lambda x: x.confidence_score, reverse=True)
        return differentials[:5]

    def _interpret_variants(
        self,
        genetic_findings: List[GeneticFinding],
        primary_diagnosis: Optional[str],
    ) -> Dict:
        """Interpret genetic variants in clinical context."""
        interpretations: Dict[str, Dict] = {}

        for finding in genetic_findings:
            if not finding.variant_type:
                continue

            annotations = self.knowledge_service.get_variant_annotations(
                gene=finding.gene,
                variant_type=finding.variant_type,
            )

            matched = None
            if finding.exons_affected:
                exon_set = set(finding.exons_affected)
                for annotation in annotations:
                    annotated_exons = set(annotation.get("exons", []))
                    if annotated_exons == exon_set:
                        matched = annotation
                        break

            if matched:
                interpretation = {
                    "gene": finding.gene,
                    "variant": finding.variant,
                    "variant_type": finding.variant_type,
                    "reading_frame": matched.get("reading_frame"),
                    "predicted_phenotype": matched.get("predicted_phenotype"),
                    "severity": matched.get("severity"),
                    "eligible_treatments": matched.get("eligible_treatments", []),
                }
            else:
                interpretation = self._fallback_dmd_variant_interpretation(finding)

            if interpretation:
                key = f"{finding.gene}_{finding.variant or '_'.join(str(x) for x in (finding.exons_affected or []))}"
                interpretations[key] = interpretation

        return interpretations

    def _fallback_dmd_variant_interpretation(self, finding: GeneticFinding) -> Optional[Dict]:
        """Fallback interpretation when knowledge graph lacks an exact annotation."""
        if finding.gene != "DMD" or finding.variant_type != "deletion" or not finding.exons_affected:
            return None

        reading_frame = self._check_reading_frame(finding.exons_affected)
        interpretation = {
            "gene": finding.gene,
            "variant": finding.variant,
            "variant_type": finding.variant_type,
            "reading_frame": reading_frame,
            "eligible_treatments": [],
        }

        if reading_frame == "out-of-frame":
            interpretation["predicted_phenotype"] = "Duchenne Muscular Dystrophy"
            interpretation["severity"] = "severe"
        else:
            interpretation["predicted_phenotype"] = "Becker Muscular Dystrophy"
            interpretation["severity"] = "mild to moderate"

        if 45 in finding.exons_affected:
            interpretation["eligible_treatments"].append("Casimersen (Amondys 45)")
        if 51 in finding.exons_affected:
            interpretation["eligible_treatments"].append("Eteplirsen (Exondys 51)")
        if 53 in finding.exons_affected:
            interpretation["eligible_treatments"].extend(["Golodirsen (Vyondys 53)", "Viltolarsen (Viltepso)"])

        return interpretation

    @staticmethod
    def _check_reading_frame(exons_affected: List[int]) -> str:
        """Simplified reading frame checker for DMD deletions."""
        out_of_frame_patterns = [
            [45, 46, 47],
            [3, 4, 5, 6, 7],
            [48, 49, 50],
        ]
        in_frame_patterns = [
            [45],
            [48, 49],
            [45, 46, 47, 48],
        ]

        if exons_affected in out_of_frame_patterns:
            return "out-of-frame"
        if exons_affected in in_frame_patterns:
            return "in-frame"
        return "in-frame" if len(exons_affected) % 3 == 0 else "out-of-frame"

    def _generate_recommendations(
        self,
        scenario: ClinicalScenario,
        primary_diagnosis: Optional[DifferentialDiagnosis],
        variant_interpretation: Optional[Dict],
    ) -> List[ClinicalRecommendation]:
        """Generate clinical recommendations based on diagnosis."""
        recommendations: List[ClinicalRecommendation] = []

        if not primary_diagnosis:
            if self.general_recommendations:
                for rec in self.general_recommendations:
                    recommendations.append(
                        ClinicalRecommendation(
                            category=rec.get("category", "diagnosis"),
                            recommendation=rec.get("recommendation", ""),
                            evidence_level=rec.get("evidence_level"),
                            urgency=rec.get("urgency"),
                            references=rec.get("references"),
                        )
                    )
            else:
                recommendations.append(
                    ClinicalRecommendation(
                        category="diagnosis",
                        recommendation="Consider comprehensive neuromuscular panel genetic testing",
                        urgency="routine",
                    )
                )
            return recommendations

        disease_code = primary_diagnosis.disease_name
        disease_specific_recs = self.knowledge_service.get_treatment_recommendations(disease_code)

        for rec in disease_specific_recs:
            recommendations.append(
                ClinicalRecommendation(
                    category=rec.get("category"),
                    recommendation=rec.get("recommendation", ""),
                    evidence_level=rec.get("evidence_level"),
                    urgency=rec.get("urgency"),
                    references=rec.get("references"),
                )
            )

        if disease_code == "DMD" and variant_interpretation:
            for variant_data in variant_interpretation.values():
                if variant_data.get("eligible_treatments"):
                    for treatment in variant_data["eligible_treatments"]:
                        recommendations.append(
                            ClinicalRecommendation(
                                category="treatment",
                                recommendation=f"Patient is eligible for {treatment} - consider referral to neuromuscular specialist",
                                evidence_level="Level A",
                                urgency="urgent",
                            )
                        )

        return recommendations

    def _answer_clinical_questions(
        self,
        questions: List[str],
        differential: List[DifferentialDiagnosis],
        variant_interpretation: Optional[Dict],
        recommendations: List[ClinicalRecommendation],
    ) -> Dict[str, str]:
        """Answer specific clinical questions."""
        answers: Dict[str, str] = {}

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
        """Calculate match score between scenario and disease profile."""
        score = 0.0

        for symptom in scenario.presenting_symptoms:
            symptom_lower = symptom.lower()
            for key_feature in profile.get("key_features", []):
                if key_feature and key_feature.lower() in symptom_lower:
                    score += 20

        age_years = self._extract_age_years(scenario.patient.age)
        if age_years is not None and "typical_onset" in profile and profile["typical_onset"]:
            onset_range = profile["typical_onset"]
            if onset_range[0] <= age_years <= onset_range[1]:
                score += 15

        return score

    @staticmethod
    def _extract_age_years(age_str: str) -> Optional[float]:
        """Extract numeric age in years from age string."""
        try:
            lower = age_str.lower()
            if "year" in lower:
                return float(age_str.split()[0])
            if "month" in lower:
                return float(age_str.split()[0]) / 12
            return None
        except Exception:  # pylint: disable=broad-except
            return None

    def _get_supporting_features(self, scenario: ClinicalScenario, profile: Dict) -> List[str]:
        """Get features that support the diagnosis."""
        supporting = []

        for symptom in scenario.presenting_symptoms:
            symptom_lower = symptom.lower()
            for feature in profile.get("key_features", []):
                if feature and feature.lower() in symptom_lower:
                    supporting.append(symptom)
                    break

        if scenario.lab_results:
            for lab in scenario.lab_results:
                if lab.interpretation and "elevated" in lab.interpretation.lower():
                    supporting.append(f"Elevated {lab.test_name}")

        return supporting

    def _get_inconsistent_features(self, scenario: ClinicalScenario, profile: Dict) -> List[str]:
        """Get features that are inconsistent with the diagnosis."""
        return []

    @staticmethod
    def _identify_limitations(scenario: ClinicalScenario) -> List[str]:
        """Identify limitations in the analysis."""
        limitations: List[str] = []

        if not scenario.genetic_findings:
            limitations.append("No genetic data available - interpretation based on clinical features only")
        if not scenario.imaging_findings:
            limitations.append("No imaging data available")
        if not scenario.family_history:
            limitations.append("Family history not provided - inheritance pattern unclear")

        return limitations
