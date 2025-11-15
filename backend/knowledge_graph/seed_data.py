"""Seed data for the muscular dystrophy knowledge graph.

This module centralizes the curated clinical domain knowledge so it can be
loaded into either a Neo4j graph database or an in-memory fallback store.
"""
from __future__ import annotations

from typing import Dict, List

# Diseases with their clinical attributes and relationships
DISEASES: List[Dict] = [
    {
        "code": "DMD",
        "name": "Duchenne Muscular Dystrophy",
        "inheritance": "X-linked",
        "typical_onset": {"min": 3, "max": 8},
        "severity": "severe",
        "key_features": [
            "proximal weakness",
            "gowers sign",
            "calf pseudohypertrophy",
            "elevated CK",
        ],
        "phenotypes": [
            {
                "feature_key": "proximal_weakness",
                "hpo_id": "HP:0003701",
                "term": "Proximal muscle weakness",
                "specificity": 0.6,
            },
            {
                "feature_key": "gowers_sign",
                "hpo_id": "HP:0003391",
                "term": "Gowers sign",
                "specificity": 0.85,
            },
            {
                "feature_key": "calf_pseudohypertrophy",
                "hpo_id": "HP:0003707",
                "term": "Calf muscle pseudohypertrophy",
                "specificity": 0.9,
            },
            {
                "feature_key": "elevated_ck",
                "hpo_id": "HP:0003236",
                "term": "Elevated serum creatine kinase",
                "specificity": 0.4,
            },
        ],
        "genes": ["DMD"],
        "diagnostic_tests": [
            {
                "name": "DMD gene deletion/duplication analysis",
                "type": "genetic",
                "frequency": "initial",
            },
            {"name": "DMD gene sequencing", "type": "genetic", "frequency": "as needed"},
            {"name": "Muscle biopsy", "type": "pathology", "frequency": "conditional"},
        ],
        "pathways": ["elevated_ck_pathway"],
    },
    {
        "code": "BMD",
        "name": "Becker Muscular Dystrophy",
        "inheritance": "X-linked",
        "typical_onset": {"min": 10, "max": 30},
        "severity": "moderate",
        "key_features": [
            "proximal weakness",
            "calf pseudohypertrophy",
            "elevated CK",
            "preserved ambulation",
        ],
        "phenotypes": [
            {
                "feature_key": "proximal_weakness",
                "hpo_id": "HP:0003701",
                "term": "Proximal muscle weakness",
                "specificity": 0.5,
            },
            {
                "feature_key": "calf_pseudohypertrophy",
                "hpo_id": "HP:0003707",
                "term": "Calf muscle pseudohypertrophy",
                "specificity": 0.75,
            },
            {
                "feature_key": "elevated_ck",
                "hpo_id": "HP:0003236",
                "term": "Elevated serum creatine kinase",
                "specificity": 0.4,
            },
        ],
        "genes": ["DMD"],
        "diagnostic_tests": [
            {"name": "DMD gene analysis", "type": "genetic", "frequency": "initial"},
            {"name": "Cardiac MRI", "type": "cardiac", "frequency": "annual"},
            {"name": "Electrocardiogram", "type": "cardiac", "frequency": "annual"},
        ],
        "pathways": ["elevated_ck_pathway"],
    },
    {
        "code": "LGMD",
        "name": "Limb-Girdle Muscular Dystrophy R1 (CAPN3)",
        "inheritance": "Autosomal recessive",
        "typical_onset": {"min": 5, "max": 40},
        "severity": "variable",
        "key_features": [
            "proximal weakness",
            "scapular winging",
            "elevated CK",
            "no cardiac involvement",
        ],
        "phenotypes": [
            {
                "feature_key": "proximal_weakness",
                "hpo_id": "HP:0003701",
                "term": "Proximal muscle weakness",
                "specificity": 0.4,
            },
            {
                "feature_key": "elevated_ck",
                "hpo_id": "HP:0003236",
                "term": "Elevated serum creatine kinase",
                "specificity": 0.3,
            },
        ],
        "genes": ["CAPN3"],
        "diagnostic_tests": [
            {"name": "CAPN3 gene testing", "type": "genetic", "frequency": "initial"},
            {"name": "Muscle MRI", "type": "imaging", "frequency": "baseline"},
            {"name": "Muscle biopsy", "type": "pathology", "frequency": "conditional"},
        ],
        "pathways": ["elevated_ck_pathway"],
    },
    {
        "code": "LAMA2-CMD",
        "name": "LAMA2-Related Congenital Muscular Dystrophy",
        "inheritance": "Autosomal recessive",
        "typical_onset": {"min": 0, "max": 1},
        "severity": "severe",
        "key_features": [
            "hypotonia",
            "weakness from birth",
            "white matter changes",
            "elevated CK",
        ],
        "phenotypes": [
            {
                "feature_key": "hypotonia",
                "hpo_id": "HP:0001252",
                "term": "Hypotonia",
                "specificity": 0.6,
            },
            {
                "feature_key": "white_matter_changes",
                "hpo_id": "HP:0002501",
                "term": "White matter abnormalities",
                "specificity": 0.7,
            },
            {
                "feature_key": "elevated_ck",
                "hpo_id": "HP:0003236",
                "term": "Elevated serum creatine kinase",
                "specificity": 0.3,
            },
        ],
        "genes": ["LAMA2"],
        "diagnostic_tests": [
            {"name": "LAMA2 gene testing", "type": "genetic", "frequency": "initial"},
            {"name": "Brain MRI", "type": "imaging", "frequency": "initial"},
            {
                "name": "Muscle biopsy with merosin staining",
                "type": "pathology",
                "frequency": "conditional",
            },
        ],
        "pathways": ["infant_hypotonia_pathway"],
    },
]

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

# Variant annotations connecting specific exon events to predicted phenotypes and therapies
VARIANT_ANNOTATIONS: List[Dict] = [
    {
        "gene": "DMD",
        "variant_type": "deletion",
        "exons": [45, 46, 47],
        "reading_frame": "out-of-frame",
        "predicted_phenotype": "Duchenne Muscular Dystrophy",
        "severity": "severe",
        "eligible_treatments": ["Casimersen (Amondys 45)"],
    },
    {
        "gene": "DMD",
        "variant_type": "deletion",
        "exons": [45],
        "reading_frame": "in-frame",
        "predicted_phenotype": "Becker Muscular Dystrophy",
        "severity": "mild to moderate",
        "eligible_treatments": ["Casimersen (Amondys 45)"],
    },
    {
        "gene": "DMD",
        "variant_type": "deletion",
        "exons": [51],
        "reading_frame": "out-of-frame",
        "predicted_phenotype": "Duchenne Muscular Dystrophy",
        "severity": "severe",
        "eligible_treatments": ["Eteplirsen (Exondys 51)"],
    },
    {
        "gene": "DMD",
        "variant_type": "deletion",
        "exons": [53],
        "reading_frame": "out-of-frame",
        "predicted_phenotype": "Duchenne Muscular Dystrophy",
        "severity": "severe",
        "eligible_treatments": ["Golodirsen (Vyondys 53)", "Viltolarsen (Viltepso)"],
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

# Reference resources that can be converted into larger datasets for production
data_sources: List[Dict] = [
    {
        "name": "TREAT-NMD Care Guidelines",
        "description": "Consensus care standards for neuromuscular disorders including DMD/BMD",
        "url": "https://treat-nmd.org/care/dmd/",
        "license": "Creative Commons",
    },
    {
        "name": "GeneReviews",
        "description": "Curated clinical overviews of genetic conditions",
        "url": "https://www.ncbi.nlm.nih.gov/books/NBK1119/",
        "license": "Public domain",
    },
    {
        "name": "Orphanet",
        "description": "Rare disease encyclopedia with phenotype and management data",
        "url": "https://www.orpha.net/",
        "license": "Open Data" ,
    },
    {
        "name": "ClinVar",
        "description": "Public archive of genomic variants and their clinical significance",
        "url": "https://www.ncbi.nlm.nih.gov/clinvar/",
        "license": "Open Data",
    },
]
