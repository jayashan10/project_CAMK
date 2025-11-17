"""
Clinical Decision Support Data

This module contains curated clinical knowledge that is NOT available in the
Monarch Initiative knowledge graph, including:
- Treatment and management recommendations with evidence levels
- Variant annotations with reading frame predictions and therapy eligibility
- Diagnostic pathways and clinical workflows
- General recommendations for uncertain diagnoses

This data supplements the disease/gene/phenotype information from Monarch with
actionable clinical decision support based on established guidelines.

Sources:
- Birnkrant DJ, et al. Diagnosis and management of Duchenne muscular dystrophy.
  Lancet Neurol. 2018
- TREAT-NMD Standards of Care Guidelines
- FDA-approved exon-skipping therapies for DMD
"""

from typing import List, Dict


# Treatment and management recommendations linked to diseases
TREATMENT_RECOMMENDATIONS: List[Dict] = [
    {
        "disease_code": "DMD",
        "category": "treatment",
        "recommendation": "Initiate corticosteroid therapy (prednisone 0.75 mg/kg/day or deflazacort 0.9 mg/kg/day)",
        "evidence_level": "Level A",
        "urgency": "urgent",
        "references": ["Birnkrant et al., Lancet Neurol 2018"],
    },
    {
        "disease_code": "DMD",
        "category": "surveillance",
        "recommendation": "Baseline cardiac evaluation (ECG and echocardiogram)",
        "evidence_level": "Level A",
        "urgency": "urgent",
        "references": [],
    },
    {
        "disease_code": "DMD",
        "category": "surveillance",
        "recommendation": "Pulmonary function testing (baseline)",
        "evidence_level": "Level A",
        "urgency": "routine",
        "references": [],
    },
    {
        "disease_code": "DMD",
        "category": "treatment",
        "recommendation": "Physical therapy referral for stretching and contracture prevention",
        "evidence_level": "Level B",
        "urgency": "routine",
        "references": [],
    },
    {
        "disease_code": "DMD",
        "category": "genetic_counseling",
        "recommendation": "Genetic counseling for family members (X-linked inheritance)",
        "evidence_level": "Level A",
        "urgency": "routine",
        "references": [],
    },
    {
        "disease_code": "BMD",
        "category": "surveillance",
        "recommendation": "Annual cardiac evaluation (cardiomyopathy can occur independent of skeletal muscle involvement)",
        "evidence_level": "Level A",
        "urgency": "urgent",
        "references": [],
    },
    {
        "disease_code": "BMD",
        "category": "treatment",
        "recommendation": "Consider ACE inhibitor or ARB for cardiac protection",
        "evidence_level": "Level B",
        "urgency": "routine",
        "references": [],
    },
    {
        "disease_code": "LGMD",
        "category": "diagnosis",
        "recommendation": "Genetic testing for CAPN3 mutations (LGMD R1/2A)",
        "evidence_level": None,
        "urgency": "routine",
        "references": [],
    },
    {
        "disease_code": "LGMD",
        "category": "surveillance",
        "recommendation": "Regular muscle strength assessment",
        "evidence_level": None,
        "urgency": "routine",
        "references": [],
    },
]

# Variant annotations connecting specific exon deletions to predicted phenotypes and therapies
# This data is critical for distinguishing DMD from BMD based on reading frame rules
# and for determining eligibility for FDA-approved exon-skipping therapies
#
# READING FRAME RULE:
# - Out-of-frame deletions (disrupts ORF) → Duchenne MD (severe, no dystrophin)
# - In-frame deletions (maintains ORF) → Becker MD (milder, partial dystrophin)
# - Rule holds in ~90% of DMD and ~94% of BMD cases
# - Known exceptions: Exon 2 deletions, Exon 78 deletions
#
# FDA-APPROVED EXON-SKIPPING THERAPIES:
# - Exon 45 amenable: Casimersen (Amondys 45)
# - Exon 51 amenable: Eteplirsen (Exondys 51)
# - Exon 53 amenable: Golodirsen (Vyondys 53), Viltolarsen (Viltepso)
#
# Sources:
# - UMD-DMD Database (November 2024 update)
# - PMC11593839, PMC5242159, PMC10252864
# - FDA approval documents for exon-skipping therapies

VARIANT_ANNOTATIONS: List[Dict] = [
    # ========== DMD DELETIONS - HOTSPOT REGION (Exons 45-55) ==========
    # This region accounts for ~60% of all DMD deletions

    # Exon 45-related deletions
    {
        "gene": "DMD",
        "variant_type": "deletion",
        "exons": [45],
        "reading_frame": "in-frame",  # Single exon, divisible by 3
        "predicted_phenotype": "Becker Muscular Dystrophy",
        "severity": "mild to moderate",
        "eligible_treatments": ["Casimersen (Amondys 45)"],  # Can skip exon 45
        "notes": "Single exon deletion, typically milder phenotype",
    },
    {
        "gene": "DMD",
        "variant_type": "deletion",
        "exons": [45, 46, 47],
        "reading_frame": "out-of-frame",  # 3 exons but disrupts ORF
        "predicted_phenotype": "Duchenne Muscular Dystrophy",
        "severity": "severe",
        "eligible_treatments": ["Casimersen (Amondys 45)"],  # Skipping 45 may restore frame
        "notes": "Common deletion pattern",
    },
    {
        "gene": "DMD",
        "variant_type": "deletion",
        "exons": [45, 46, 47, 48, 49, 50],
        "reading_frame": "in-frame",  # 6 exons, maintains ORF
        "predicted_phenotype": "Becker Muscular Dystrophy",
        "severity": "moderate",
        "eligible_treatments": [],
        "notes": "Large in-frame deletion",
    },

    # Exon 50 deletions - MOST COMMON SINGLE DELETION
    {
        "gene": "DMD",
        "variant_type": "deletion",
        "exons": [50],
        "reading_frame": "out-of-frame",
        "predicted_phenotype": "Duchenne Muscular Dystrophy",
        "severity": "severe",
        "eligible_treatments": [],  # No FDA therapy for exon 50 yet
        "notes": "Most common single exon deletion (~20% of cases)",
    },
    {
        "gene": "DMD",
        "variant_type": "deletion",
        "exons": [48, 49, 50],
        "reading_frame": "in-frame",
        "predicted_phenotype": "Becker Muscular Dystrophy",
        "severity": "mild to moderate",
        "eligible_treatments": [],
        "notes": "In-frame deletion with preserved reading frame",
    },

    # Exon 51 deletions - Second most common
    {
        "gene": "DMD",
        "variant_type": "deletion",
        "exons": [51],
        "reading_frame": "out-of-frame",
        "predicted_phenotype": "Duchenne Muscular Dystrophy",
        "severity": "severe",
        "eligible_treatments": ["Eteplirsen (Exondys 51)"],
        "notes": "Second most common deletion, FDA therapy available",
    },
    {
        "gene": "DMD",
        "variant_type": "deletion",
        "exons": [49, 50, 51],
        "reading_frame": "out-of-frame",
        "predicted_phenotype": "Duchenne Muscular Dystrophy",
        "severity": "severe",
        "eligible_treatments": ["Eteplirsen (Exondys 51)"],
        "notes": "Multi-exon deletion amenable to exon 51 skipping",
    },
    {
        "gene": "DMD",
        "variant_type": "deletion",
        "exons": [48, 49, 50, 51],
        "reading_frame": "out-of-frame",
        "predicted_phenotype": "Duchenne Muscular Dystrophy",
        "severity": "severe",
        "eligible_treatments": ["Eteplirsen (Exondys 51)"],
        "notes": "Large deletion amenable to exon 51 skipping",
    },

    # Exon 52 deletions
    {
        "gene": "DMD",
        "variant_type": "deletion",
        "exons": [52],
        "reading_frame": "out-of-frame",
        "predicted_phenotype": "Duchenne Muscular Dystrophy",
        "severity": "severe",
        "eligible_treatments": [],
        "notes": "Single exon deletion",
    },

    # Exon 53 deletions
    {
        "gene": "DMD",
        "variant_type": "deletion",
        "exons": [53],
        "reading_frame": "out-of-frame",
        "predicted_phenotype": "Duchenne Muscular Dystrophy",
        "severity": "severe",
        "eligible_treatments": ["Golodirsen (Vyondys 53)", "Viltolarsen (Viltepso)"],
        "notes": "FDA therapies available for exon 53 skipping",
    },
    {
        "gene": "DMD",
        "variant_type": "deletion",
        "exons": [50, 51, 52, 53],
        "reading_frame": "out-of-frame",
        "predicted_phenotype": "Duchenne Muscular Dystrophy",
        "severity": "severe",
        "eligible_treatments": ["Golodirsen (Vyondys 53)", "Viltolarsen (Viltepso)"],
        "notes": "Large deletion amenable to exon 53 skipping",
    },

    # Exon 44 deletion - Common, represents ~12% of DMD cases
    {
        "gene": "DMD",
        "variant_type": "deletion",
        "exons": [44],
        "reading_frame": "out-of-frame",
        "predicted_phenotype": "Duchenne Muscular Dystrophy",
        "severity": "severe",
        "eligible_treatments": [],
        "notes": "Common deletion (~12% of DMD), no FDA therapy yet",
    },

    # Large deletion spanning hotspot
    {
        "gene": "DMD",
        "variant_type": "deletion",
        "exons": [45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55],
        "reading_frame": "out-of-frame",
        "predicted_phenotype": "Duchenne Muscular Dystrophy",
        "severity": "severe",
        "eligible_treatments": [],
        "notes": "Large hotspot deletion, severe phenotype",
    },

    # ========== DMD DELETIONS - PROXIMAL HOTSPOT (Exons 2-10) ==========
    # Second most common region for deletions

    {
        "gene": "DMD",
        "variant_type": "deletion",
        "exons": [2],
        "reading_frame": "exception",  # Known exception to reading frame rule
        "predicted_phenotype": "Variable (DMD or BMD)",
        "severity": "variable",
        "eligible_treatments": [],
        "notes": "Exception to reading frame rule - can cause either DMD or BMD",
    },
    {
        "gene": "DMD",
        "variant_type": "deletion",
        "exons": [3, 4, 5, 6, 7],
        "reading_frame": "out-of-frame",
        "predicted_phenotype": "Duchenne Muscular Dystrophy",
        "severity": "severe",
        "eligible_treatments": [],
        "notes": "Proximal deletion affecting actin-binding domain",
    },
    {
        "gene": "DMD",
        "variant_type": "deletion",
        "exons": [8, 9],
        "reading_frame": "out-of-frame",
        "predicted_phenotype": "Duchenne Muscular Dystrophy",
        "severity": "severe",
        "eligible_treatments": [],
        "notes": "Proximal region deletion",
    },

    # ========== DMD DELETIONS - OTHER REGIONS ==========

    {
        "gene": "DMD",
        "variant_type": "deletion",
        "exons": [19],
        "reading_frame": "out-of-frame",
        "predicted_phenotype": "Duchenne Muscular Dystrophy",
        "severity": "severe",
        "eligible_treatments": [],
        "notes": "Less common deletion outside hotspot regions",
    },
    {
        "gene": "DMD",
        "variant_type": "deletion",
        "exons": [78],
        "reading_frame": "exception",  # Known exception
        "predicted_phenotype": "Variable (DMD or BMD)",
        "severity": "variable",
        "eligible_treatments": [],
        "notes": "C-terminal deletion, exception to reading frame rule",
    },

    # ========== DMD POINT MUTATIONS ==========
    {
        "gene": "DMD",
        "variant_type": "nonsense",
        "exons": [23],
        "hgvs": "c.3151C>T",
        "protein_change": "p.Arg1051*",
        "reading_frame": "truncating",
        "predicted_phenotype": "Duchenne Muscular Dystrophy",
        "severity": "severe",
        "eligible_treatments": ["Ataluren (Translarna)"],  # For nonsense mutations in some regions
        "notes": "Nonsense mutation eligible for read-through therapy (not FDA approved in US)",
    },

    # ========== LAMA2 VARIANTS (Congenital Muscular Dystrophy) ==========

    {
        "gene": "LAMA2",
        "variant_type": "nonsense",
        "hgvs": "c.2049_2050delAG",
        "protein_change": "p.Arg683fs",
        "predicted_phenotype": "LAMA2-Related Congenital Muscular Dystrophy",
        "severity": "severe",
        "eligible_treatments": [],
        "notes": "Common frameshift mutation causing complete merosin deficiency",
    },
    {
        "gene": "LAMA2",
        "variant_type": "missense",
        "hgvs": "c.4405T>C",
        "protein_change": "p.Cys1469Arg",
        "predicted_phenotype": "LAMA2-Related Congenital Muscular Dystrophy",
        "severity": "moderate to severe",
        "eligible_treatments": [],
        "notes": "Missense mutation affecting laminin binding",
    },
    {
        "gene": "LAMA2",
        "variant_type": "nonsense",
        "hgvs": "c.7732C>T",
        "protein_change": "p.Arg2578*",
        "predicted_phenotype": "LAMA2-Related Congenital Muscular Dystrophy",
        "severity": "severe",
        "eligible_treatments": [],
        "notes": "Nonsense mutation causing severe phenotype",
    },
    {
        "gene": "LAMA2",
        "variant_type": "deletion",
        "hgvs": "c.7147delC",
        "protein_change": "p.Leu2383fs",
        "predicted_phenotype": "LAMA2-Related Congenital Muscular Dystrophy",
        "severity": "severe",
        "eligible_treatments": [],
        "notes": "Frameshift deletion",
    },

    # ========== CAPN3 VARIANTS (LGMD2A/R1) ==========

    {
        "gene": "CAPN3",
        "variant_type": "missense",
        "hgvs": "c.550delA",
        "protein_change": "p.Thr184fs",
        "predicted_phenotype": "Limb-Girdle Muscular Dystrophy Type 2A (LGMD2A/R1)",
        "severity": "moderate",
        "eligible_treatments": [],
        "notes": "Most common CAPN3 mutation in European populations",
    },
    {
        "gene": "CAPN3",
        "variant_type": "nonsense",
        "hgvs": "c.2362AG>TCATCT",
        "protein_change": "p.Arg788Ser",
        "predicted_phenotype": "Limb-Girdle Muscular Dystrophy Type 2A (LGMD2A/R1)",
        "severity": "moderate",
        "eligible_treatments": [],
        "notes": "Complex insertion/substitution",
    },
    {
        "gene": "CAPN3",
        "variant_type": "missense",
        "hgvs": "c.1715G>C",
        "protein_change": "p.Arg572Pro",
        "predicted_phenotype": "Limb-Girdle Muscular Dystrophy Type 2A (LGMD2A/R1)",
        "severity": "mild to moderate",
        "eligible_treatments": [],
        "notes": "Missense mutation with variable phenotype",
    },
    {
        "gene": "CAPN3",
        "variant_type": "deletion",
        "hgvs": "c.1194delT",
        "protein_change": "p.Phe398fs",
        "predicted_phenotype": "Limb-Girdle Muscular Dystrophy Type 2A (LGMD2A/R1)",
        "severity": "moderate to severe",
        "eligible_treatments": [],
        "notes": "Frameshift deletion causing loss of function",
    },
]

# Diagnostic pathways capture structured clinical workflows
DIAGNOSTIC_PATHWAYS: List[Dict] = [
    {
        "code": "elevated_ck_pathway",
        "name": "Elevated CK Diagnostic Pathway",
        "steps": [
            "Clinical evaluation",
            "Family history",
            "CK level confirmation",
            "Genetic testing (DMD gene first if male)",
            "Consider muscle biopsy if genetic testing negative",
        ],
    },
    {
        "code": "infant_hypotonia_pathway",
        "name": "Infant Hypotonia Diagnostic Pathway",
        "steps": [
            "Rule out central causes",
            "CK level",
            "Brain MRI (look for white matter changes)",
            "Genetic panel for congenital myopathies",
            "Consider LAMA2 testing if white matter changes present",
        ],
    },
]

# General recommendations used when the diagnosis is uncertain
GENERAL_RECOMMENDATIONS: List[Dict] = [
    {
        "category": "diagnosis",
        "recommendation": "Consider comprehensive neuromuscular panel genetic testing",
        "evidence_level": None,
        "urgency": "routine",
        "references": [],
    }
]

# DISEASES - Minimal disease definitions for in-memory fallback
# When Neo4j/Monarch is not available, this provides basic disease data
# Full disease/gene/phenotype data comes from Monarch Initiative when available
DISEASES: List[Dict] = [
    {
        "code": "DMD",
        "name": "Duchenne Muscular Dystrophy",
        "inheritance": "X-linked recessive",
        "genes": ["DMD"],
        "typical_onset": {"min": 3, "max": 8},
        "severity": "severe",
        "key_features": [
            "Progressive proximal muscle weakness",
            "Elevated CK (often >10x normal)",
            "Gowers sign",
            "Calf pseudohypertrophy",
            "Loss of ambulation by age 12-13",
        ],
        "phenotypes": [
            {"feature_key": "proximal_weakness", "hpo_id": "HP:0003701", "term": "Proximal muscle weakness"},
            {"feature_key": "elevated_ck", "hpo_id": "HP:0003236", "term": "Elevated serum creatine kinase"},
            {"feature_key": "gowers_sign", "hpo_id": "HP:0003391", "term": "Gowers sign"},
            {"feature_key": "calf_pseudohypertrophy", "hpo_id": "HP:0003707", "term": "Calf muscle pseudohypertrophy"},
        ],
        "diagnostic_tests": [
            {"name": "Creatine Kinase", "type": "lab", "frequency": "always elevated"},
            {"name": "DMD gene sequencing/deletion analysis", "type": "genetic", "frequency": "diagnostic"},
        ],
        "pathways": ["elevated_ck_pathway"],
    },
    {
        "code": "BMD",
        "name": "Becker Muscular Dystrophy",
        "inheritance": "X-linked recessive",
        "genes": ["DMD"],
        "typical_onset": {"min": 10, "max": 30},
        "severity": "moderate",
        "key_features": [
            "Progressive proximal muscle weakness",
            "Elevated CK",
            "Preserved ambulation into adulthood",
            "Cardiomyopathy risk",
        ],
        "phenotypes": [
            {"feature_key": "proximal_weakness", "hpo_id": "HP:0003701", "term": "Proximal muscle weakness"},
            {"feature_key": "elevated_ck", "hpo_id": "HP:0003236", "term": "Elevated serum creatine kinase"},
        ],
        "diagnostic_tests": [
            {"name": "Creatine Kinase", "type": "lab"},
            {"name": "DMD gene sequencing", "type": "genetic"},
            {"name": "Echocardiogram", "type": "cardiac"},
        ],
        "pathways": ["elevated_ck_pathway"],
    },
    {
        "code": "LGMD",
        "name": "Limb-Girdle Muscular Dystrophy",
        "inheritance": "Autosomal recessive or dominant",
        "genes": ["CAPN3", "DYSF", "ANO5"],
        "typical_onset": {"min": 10, "max": 40},
        "severity": "variable",
        "key_features": [
            "Proximal limb weakness",
            "Variable progression",
            "Elevated CK",
        ],
        "phenotypes": [
            {"feature_key": "proximal_weakness", "hpo_id": "HP:0003701", "term": "Proximal muscle weakness"},
            {"feature_key": "elevated_ck", "hpo_id": "HP:0003236", "term": "Elevated serum creatine kinase"},
        ],
        "diagnostic_tests": [
            {"name": "Creatine Kinase", "type": "lab"},
            {"name": "LGMD genetic panel", "type": "genetic"},
        ],
        "pathways": ["elevated_ck_pathway"],
    },
    {
        "code": "LAMA2-CMD",
        "name": "LAMA2-Related Congenital Muscular Dystrophy",
        "inheritance": "Autosomal recessive",
        "genes": ["LAMA2"],
        "typical_onset": {"min": 0, "max": 2},
        "severity": "severe",
        "key_features": [
            "Severe hypotonia from birth",
            "White matter changes on brain MRI",
            "Elevated CK",
            "Contractures",
        ],
        "phenotypes": [
            {"feature_key": "hypotonia", "hpo_id": "HP:0001252", "term": "Muscular hypotonia"},
            {"feature_key": "elevated_ck", "hpo_id": "HP:0003236", "term": "Elevated serum creatine kinase"},
        ],
        "diagnostic_tests": [
            {"name": "Brain MRI", "type": "imaging"},
            {"name": "LAMA2 gene testing", "type": "genetic"},
        ],
        "pathways": ["infant_hypotonia_pathway"],
    },
]

# data_sources - Empty list (metadata for backward compatibility)
# Data sources are now tracked separately (Monarch + curated clinical data)
data_sources: List[Dict] = []
