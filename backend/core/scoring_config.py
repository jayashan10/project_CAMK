"""
Scoring Configuration for Clinical Decision Support System

This file contains all scoring weights and thresholds used in the differential
diagnosis algorithm. These values can be adjusted by clinicians based on their
clinical judgment and domain expertise.

IMPORTANT: These weights are currently based on clinical heuristics and should
be validated against real-world data or expert consensus.
"""

# ═══════════════════════════════════════════════════════════════
# SCORING WEIGHTS
# ═══════════════════════════════════════════════════════════════

# Inheritance Pattern Matching
# Weight added when patient sex matches disease inheritance pattern
# (e.g., male patient with X-linked disease)
SEX_INHERITANCE_MATCH_WEIGHT = 10.0

# Monarch HPO Overlap
# Multiplier for each HPO term that matches in Monarch knowledge graph
# Total bonus = (number of HPO matches) × this multiplier
MONARCH_HPO_MATCH_MULTIPLIER = 5.0

# Laboratory Results
# Weight added when specific lab abnormalities support a disease
ELEVATED_CK_WEIGHT = 15.0  # Creatine kinase elevation (muscular dystrophies)

# Age-Appropriate Onset
# Weights added when patient age falls within typical onset range for disease
AGE_APPROPRIATE_DMD_WEIGHT = 10.0       # Duchenne MD (onset 3-8 years)
AGE_APPROPRIATE_BMD_WEIGHT = 10.0       # Becker MD (onset >10 years)
AGE_APPROPRIATE_CMD_WEIGHT = 15.0       # Congenital MD (onset <2 years)

# ═══════════════════════════════════════════════════════════════
# THRESHOLDS
# ═══════════════════════════════════════════════════════════════

# Differential Diagnosis Inclusion Threshold
# Diseases must score ABOVE this threshold to be included in differential
# (Note: Uses > comparison, so score must be strictly greater than threshold)
DIFFERENTIAL_INCLUSION_THRESHOLD = 30.0

# Maximum Confidence Score
# Cap confidence scores at this value to avoid over-confidence
MAX_CONFIDENCE_SCORE = 95.0

# Maximum Diseases in Differential
# Limit the number of diseases shown in final differential diagnosis
MAX_DIFFERENTIAL_DIAGNOSES = 5

# ═══════════════════════════════════════════════════════════════
# DISEASE-SPECIFIC AGE RANGES
# ═══════════════════════════════════════════════════════════════

# Age ranges (in years) for typical disease onset
# Used to calculate age-appropriate bonuses
DISEASE_AGE_RANGES = {
    "DMD": {"min": 3, "max": 8},        # Duchenne: typically 3-8 years
    "BMD": {"min": 10, "max": None},    # Becker: typically >10 years
    "LAMA2-CMD": {"min": 0, "max": 2},  # Congenital: birth to 2 years
}

# ═══════════════════════════════════════════════════════════════
# LAB TEST CRITERIA
# ═══════════════════════════════════════════════════════════════

# Diseases where elevated CK is a strong supporting feature
DISEASES_WITH_ELEVATED_CK = ["DMD", "BMD", "LGMD"]

# Keywords to detect elevated CK in lab interpretation
ELEVATED_CK_KEYWORDS = ["elevated", "high", "increased"]

# ═══════════════════════════════════════════════════════════════
# NOTES FOR CLINICIANS
# ═══════════════════════════════════════════════════════════════

"""
ADJUSTING WEIGHTS:

1. Sex/Inheritance Match (currently 10 points):
   - Increase if inheritance pattern is highly predictive
   - Decrease if you want to be less biased by sex/inheritance

2. Monarch HPO Match (currently 5 points per match):
   - Increase to give more weight to phenotype overlap
   - Decrease if Monarch matches are too noisy/non-specific

3. Elevated CK (currently 15 points):
   - Increase if CK is very specific for muscular dystrophies
   - Decrease if CK elevation is common in many conditions

4. Age Appropriateness (currently 10-15 points):
   - Increase to strongly favor age-typical presentations
   - Decrease to consider atypical presentations more often

5. Inclusion Threshold (currently 30 points):
   - Increase to be more selective (fewer diagnoses in differential)
   - Decrease to be more inclusive (more diagnoses considered)

VALIDATION RECOMMENDATIONS:

- Test against known cases to calibrate weights
- Consult domain experts (pediatric neurologists, geneticists)
- Review literature for evidence-based scoring systems
- Consider machine learning approaches if labeled data available
"""
