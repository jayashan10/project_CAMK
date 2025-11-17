"""Clinical Scenario Processor - Main orchestration logic backed by knowledge graph."""
import logging
from typing import Dict, List, Optional
from datetime import datetime

from backend.knowledge_graph.service import KnowledgeGraphService

logger = logging.getLogger(__name__)

from .clinical_scenario import (
    ClinicalScenario,
    ScenarioResponse,
    DifferentialDiagnosis,
    ClinicalRecommendation,
    GeneticFinding,
    MonarchMatch,
    MonarchSearchSummary,
    ScoringBreakdown,
    ScoringComponent,
    extract_hpo_terms,
    calculate_phenotype_similarity,
)
from . import scoring_config


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
        import logging
        logger = logging.getLogger(__name__)

        # Step 1: Extract clinical features and map to HPO terms
        hpo_terms = extract_hpo_terms(scenario.presenting_symptoms)
        logger.info(f"📝 Extracted {len(hpo_terms)} HPO mappings from symptoms")

        # Step 2: Generate differential diagnosis (with detailed reasoning capture)
        differential_result = self._generate_differential_diagnosis_with_details(scenario, hpo_terms)
        differential = differential_result["differential"]
        monarch_summary = differential_result.get("monarch_summary")
        top_monarch = differential_result.get("top_monarch")
        scoring_details = differential_result.get("scoring_details")

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

        # Step 6: Compile response with enhanced reasoning data
        return ScenarioResponse(
            scenario_id=scenario.scenario_id or f"scenario_{datetime.now().timestamp()}",
            differential_diagnoses=differential,
            primary_diagnosis=differential[0].disease_name if differential else None,
            variant_interpretation=variant_interpretation,
            recommendations=recommendations,
            question_answers=question_answers,
            overall_confidence=differential[0].confidence_score if differential else 0,
            limitations=self._identify_limitations(scenario),
            # Enhanced reasoning flow data
            hpo_mappings=hpo_terms if hpo_terms else None,
            monarch_search_summary=monarch_summary,
            top_monarch_matches=top_monarch,
            scoring_details=scoring_details,
        )

    def _generate_differential_diagnosis(
        self,
        scenario: ClinicalScenario,
        hpo_terms,
    ) -> List[DifferentialDiagnosis]:
        """Generate differential diagnosis based on clinical presentation."""
        import logging
        logger = logging.getLogger(__name__)

        differentials = []
        hpo_ids = [mapping.hpo_id for mapping in hpo_terms if mapping.hpo_id]

        logger.info(f"🧬 ScenarioProcessor: Extracted {len(hpo_ids)} HPO IDs from symptoms: {hpo_ids}")

        phenotype_matches = (
            self.knowledge_service.search_diseases_by_phenotypes(hpo_ids) if hpo_ids else []
        )
        monarch_match_map = {match["code"]: match for match in phenotype_matches}

        logger.info(f"🏥 ScenarioProcessor: Scoring {len(self.disease_profiles)} disease profiles")
        all_scores = []

        for disease_code, profile in self.disease_profiles.items():
            score = self._calculate_disease_match_score(scenario, profile)
            base_score = score

            if scenario.patient.sex == "male" and profile.get("inheritance") == "X-linked":
                score += 10

            match_info = monarch_match_map.get(disease_code)
            if match_info:
                score += match_info["match_count"] * 5

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

            all_scores.append((disease_code, score, base_score))

            if score > 30:
                diff = DifferentialDiagnosis(
                    disease_name=disease_code,
                    confidence_score=min(score, 95),
                    supporting_features=self._get_supporting_features(scenario, profile),
                    inconsistent_features=self._get_inconsistent_features(scenario, profile),
                    recommended_tests=profile.get("diagnostic_tests", []),
                )
                differentials.append(diff)

        # Log all scores for debugging
        logger.info(f"📊 Disease Scoring Results (ALL {len(all_scores)} diseases):")
        all_scores.sort(key=lambda x: x[1], reverse=True)
        for i, (code, final_score, base_score) in enumerate(all_scores[:20], 1):
            status = "✅ INCLUDED" if final_score > 30 else "❌ EXCLUDED (score ≤ 30)"
            logger.info(f"   {i}. [{code}] Final={final_score}, Base={base_score} - {status}")

        differentials.sort(key=lambda x: x.confidence_score, reverse=True)
        logger.info(f"🎯 ScenarioProcessor: Returning top {min(5, len(differentials))} diagnoses (out of {len(differentials)} with score > 30)")

        return differentials[:5]

    def _generate_differential_diagnosis_with_details(
        self,
        scenario: ClinicalScenario,
        hpo_terms,
    ) -> Dict:
        """Generate differential diagnosis with full reasoning details for visualization."""
        import logging
        from collections import defaultdict
        logger = logging.getLogger(__name__)

        differentials = []
        scoring_breakdowns = []
        hpo_ids = [mapping.hpo_id for mapping in hpo_terms if mapping.hpo_id]

        logger.info(f"🧬 ScenarioProcessor: Extracted {len(hpo_ids)} HPO IDs from symptoms: {hpo_ids}")

        # Search Monarch knowledge graph
        phenotype_matches = (
            self.knowledge_service.search_diseases_by_phenotypes(hpo_ids) if hpo_ids else []
        )
        monarch_match_map = {match["code"]: match for match in phenotype_matches}

        # Create Monarch summary
        match_count_distribution = defaultdict(int)
        for match in phenotype_matches:
            match_count_distribution[str(match["match_count"])] += 1

        monarch_summary = MonarchSearchSummary(
            total_diseases_found=len(phenotype_matches),
            hpo_ids_searched=hpo_ids,
            diseases_by_match_count=dict(match_count_distribution)
        )

        # Get top 20 Monarch matches for graph visualization
        top_monarch_matches = [
            MonarchMatch(
                disease_id=match["disease_id"],
                disease_name=match["disease_name"],
                match_count=match["match_count"],
                matched_hpo_ids=match["matched_hpo_ids"],
                code=match.get("code")
            )
            for match in phenotype_matches[:20]
        ]

        logger.info(f"🏥 ScenarioProcessor: Scoring {len(self.disease_profiles)} disease profiles")

        # Score all diseases and capture detailed breakdown
        for disease_code, profile in self.disease_profiles.items():
            base_score = self._calculate_disease_match_score(scenario, profile)
            score = base_score
            components = []

            # Component 1: Base phenotype matching
            if base_score > 0:
                components.append(ScoringComponent(
                    component_name="Phenotype Matching",
                    points_added=base_score,
                    reasoning=f"Matched clinical features from disease profile"
                ))

            # Component 2: X-linked inheritance bonus
            if scenario.patient.sex == "male" and profile.get("inheritance") == "X-linked":
                components.append(ScoringComponent(
                    component_name="Sex/Inheritance Match",
                    points_added=scoring_config.SEX_INHERITANCE_MATCH_WEIGHT,
                    reasoning="Male patient with X-linked disease"
                ))
                score += scoring_config.SEX_INHERITANCE_MATCH_WEIGHT

            # Component 3: Monarch phenotype overlap bonus
            match_info = monarch_match_map.get(disease_code)
            if match_info:
                monarch_bonus = match_info["match_count"] * scoring_config.MONARCH_HPO_MATCH_MULTIPLIER
                components.append(ScoringComponent(
                    component_name="Monarch HPO Overlap",
                    points_added=float(monarch_bonus),
                    reasoning=f"{match_info['match_count']} HPO terms matched in Monarch"
                ))
                score += monarch_bonus

            # Component 4: Lab results bonus
            if scenario.lab_results:
                for lab in scenario.lab_results:
                    if (
                        lab.test_name == "Creatine Kinase"
                        and lab.interpretation
                        and any(keyword in lab.interpretation.lower() for keyword in scoring_config.ELEVATED_CK_KEYWORDS)
                        and disease_code in scoring_config.DISEASES_WITH_ELEVATED_CK
                    ):
                        components.append(ScoringComponent(
                            component_name="Elevated CK",
                            points_added=scoring_config.ELEVATED_CK_WEIGHT,
                            reasoning="Elevated creatine kinase supports muscular dystrophy"
                        ))
                        score += scoring_config.ELEVATED_CK_WEIGHT

            # Component 5: Age appropriateness bonus
            age_value = self._extract_age_years(scenario.patient.age)
            if age_value is not None:
                # Check age ranges from config
                if disease_code in scoring_config.DISEASE_AGE_RANGES:
                    age_range = scoring_config.DISEASE_AGE_RANGES[disease_code]
                    min_age = age_range.get("min", 0)
                    max_age = age_range.get("max")

                    is_age_appropriate = False
                    if max_age is None:
                        is_age_appropriate = age_value >= min_age
                    else:
                        is_age_appropriate = min_age <= age_value <= max_age

                    if is_age_appropriate:
                        # Get disease-specific weight
                        if disease_code == "DMD":
                            weight = scoring_config.AGE_APPROPRIATE_DMD_WEIGHT
                            range_desc = f"{min_age}-{max_age} years"
                        elif disease_code == "BMD":
                            weight = scoring_config.AGE_APPROPRIATE_BMD_WEIGHT
                            range_desc = f">{min_age} years"
                        elif disease_code == "LAMA2-CMD":
                            weight = scoring_config.AGE_APPROPRIATE_CMD_WEIGHT
                            range_desc = f"<{max_age} years"
                        else:
                            weight = 10.0  # Default weight for unlisted diseases
                            range_desc = f"{min_age}-{max_age if max_age else '∞'} years"

                        components.append(ScoringComponent(
                            component_name="Age-Appropriate Onset",
                            points_added=weight,
                            reasoning=f"Patient age {age_value} within typical {disease_code} onset ({range_desc})"
                        ))
                        score += weight

            # Create scoring breakdown
            included = score > scoring_config.DIFFERENTIAL_INCLUSION_THRESHOLD
            exclusion_reason = None if included else f"Score {score:.1f} ≤ threshold ({scoring_config.DIFFERENTIAL_INCLUSION_THRESHOLD})"

            scoring_breakdowns.append(ScoringBreakdown(
                disease_code=disease_code,
                disease_name=profile.get("name", disease_code),
                base_score=base_score,
                scoring_components=components,
                final_score=score,
                included_in_differential=included,
                exclusion_reason=exclusion_reason
            ))

            # Add to differential if passes threshold
            if included:
                diff = DifferentialDiagnosis(
                    disease_name=disease_code,
                    confidence_score=min(score, scoring_config.MAX_CONFIDENCE_SCORE),
                    supporting_features=self._get_supporting_features(scenario, profile),
                    inconsistent_features=self._get_inconsistent_features(scenario, profile),
                    recommended_tests=profile.get("diagnostic_tests", []),
                )
                differentials.append(diff)

        # Sort and log
        differentials.sort(key=lambda x: x.confidence_score, reverse=True)
        scoring_breakdowns.sort(key=lambda x: x.final_score, reverse=True)

        logger.info(f"📊 Disease Scoring Results: {len(scoring_breakdowns)} diseases scored")
        logger.info(f"🎯 Returning top {min(scoring_config.MAX_DIFFERENTIAL_DIAGNOSES, len(differentials))} diagnoses (out of {len(differentials)} with score > {scoring_config.DIFFERENTIAL_INCLUSION_THRESHOLD})")

        return {
            "differential": differentials[:scoring_config.MAX_DIFFERENTIAL_DIAGNOSES],
            "monarch_summary": monarch_summary,
            "top_monarch": top_monarch_matches,
            "scoring_details": scoring_breakdowns
        }

    def _interpret_variants(
        self,
        genetic_findings: List[GeneticFinding],
        primary_diagnosis: Optional[str],
    ) -> Dict:
        """Interpret genetic variants using curated variant annotations and ClinVar enrichment."""
        interpretations: Dict[str, Dict] = {}

        for finding in genetic_findings:
            # Build basic variant info
            interpretation = {
                "gene": finding.gene,
                "variant": finding.variant,
                "variant_type": finding.variant_type,
                "zygosity": finding.zygosity,
                "exons": finding.exons_affected,
            }

            # Try to get variant annotations from curated database
            annotations = self.knowledge_service.get_variant_annotations(
                gene=finding.gene,
                variant_type=finding.variant_type,
            )

            # Look for matching annotation from our curated database
            matched = None
            if finding.exons_affected:
                exon_set = set(finding.exons_affected)
                for annotation in annotations:
                    annotated_exons = set(annotation.get("exons", []))
                    if annotated_exons == exon_set:
                        matched = annotation
                        logger.info(f"✅ Matched curated variant: {finding.gene} exons {finding.exons_affected}")
                        if annotation.get("notes"):
                            logger.info(f"   Note: {annotation.get('notes')}")
                        break

            # Use curated annotation data if available
            if matched:
                # Add curated clinical data
                if matched.get("reading_frame"):
                    interpretation["reading_frame"] = matched.get("reading_frame")
                if matched.get("predicted_phenotype"):
                    interpretation["predicted_phenotype"] = matched.get("predicted_phenotype")
                if matched.get("severity"):
                    interpretation["severity"] = matched.get("severity")
                if matched.get("eligible_treatments"):
                    interpretation["eligible_treatments"] = matched.get("eligible_treatments")
                    logger.info(f"   Eligible therapies: {', '.join(matched.get('eligible_treatments', []))}")

                # Add ClinVar enrichment data if available
                if matched.get("clinvar_id"):
                    interpretation["clinvar_id"] = matched.get("clinvar_id")
                if matched.get("clinvar_significance"):
                    interpretation["clinvar_significance"] = matched.get("clinvar_significance")
                if matched.get("clinvar_review_status"):
                    interpretation["clinvar_review_status"] = matched.get("clinvar_review_status")

                # Add ClinVar variants table data if available
                if matched.get("clinvar_variants"):
                    interpretation["clinvar_variants"] = matched.get("clinvar_variants")
                    logger.info(f"   ClinVar variants table: {len(matched.get('clinvar_variants'))} variants")
                if matched.get("clinvar_gene_summary"):
                    interpretation["clinvar_gene_summary"] = matched.get("clinvar_gene_summary")

                # Add HGVS and protein change if available
                if matched.get("hgvs"):
                    interpretation["hgvs"] = matched.get("hgvs")
                if matched.get("protein_change"):
                    interpretation["protein_change"] = matched.get("protein_change")
            else:
                # No exact match found - try fallback interpretation for DMD deletions
                logger.info(f"⚠️ No curated match for {finding.gene} variant, using fallback interpretation")
                fallback = self._fallback_dmd_variant_interpretation(finding)
                if fallback:
                    interpretation.update(fallback)

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
                            # RAG-specific fields (present for RAG-sourced recommendations)
                            source_type=rec.get("source_type"),
                            citation=rec.get("citation"),
                            confidence=rec.get("confidence"),
                            chunk_id=rec.get("chunk_id"),
                            retrieved_text=rec.get("retrieved_text"),
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
                    # RAG-specific fields (present for RAG-sourced recommendations)
                    source_type=rec.get("source_type"),
                    citation=rec.get("citation"),
                    confidence=rec.get("confidence"),
                    chunk_id=rec.get("chunk_id"),
                    retrieved_text=rec.get("retrieved_text"),
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
        if not scenario.patient.family_history:
            limitations.append("Family history not provided - inheritance pattern unclear")

        return limitations
