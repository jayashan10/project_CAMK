# Curated Variant Database Documentation

## Overview

This system uses a **curated variant approach** for clinical decision support, with ClinVar serving as an optional showcase/reference feature. Our curated database provides complete control over therapy mappings, reading frame predictions, and clinical interpretations critical for muscular dystrophy management.

## Why Curated Variants?

### Advantages of Curated Approach
- **Full control** over FDA therapy eligibility mappings
- **Accurate reading frame predictions** for DMD vs BMD distinction
- **No API dependencies** for critical clinical decisions
- **Clinically validated** interpretations
- **Fast and reliable** (no network calls)
- **Treatment-focused** with direct therapy connections

### ClinVar Limitations
- No FDA therapy eligibility data
- No reading frame predictions for DMD deletions
- Limited query capabilities (can't filter by specific criteria)
- Too much noise (hundreds of variants without clinical prioritization)
- Missing muscular dystrophy-specific annotations

## Curated Variant Summary

### Statistics
- **Total curated variants:** 29
- **DMD variants:** 19 (including all therapy-eligible deletions)
- **LAMA2 variants:** 4 (common pathogenic mutations)
- **CAPN3 variants:** 4 (LGMD2A/R1 mutations)

### DMD Variants by Category

#### Therapy-Eligible Deletions
| Exons | Reading Frame | Phenotype | Eligible Therapy | Notes |
|-------|---------------|-----------|------------------|-------|
| 45 | in-frame | BMD | Casimersen (Amondys 45) | Single exon deletion |
| 45, 46, 47 | out-of-frame | DMD | Casimersen (Amondys 45) | Common deletion pattern |
| 51 | out-of-frame | DMD | Eteplirsen (Exondys 51) | Second most common deletion |
| 49, 50, 51 | out-of-frame | DMD | Eteplirsen (Exondys 51) | Multi-exon deletion |
| 48, 49, 50, 51 | out-of-frame | DMD | Eteplirsen (Exondys 51) | Large deletion |
| 53 | out-of-frame | DMD | Golodirsen, Viltolarsen | FDA therapies available |
| 50, 51, 52, 53 | out-of-frame | DMD | Golodirsen, Viltolarsen | Large deletion |

#### Common Deletions Without FDA Therapy
| Exons | Reading Frame | Phenotype | Notes |
|-------|---------------|-----------|-------|
| 50 | out-of-frame | DMD | Most common single deletion (~20%) |
| 44 | out-of-frame | DMD | ~12% of DMD cases |
| 52 | out-of-frame | DMD | Single exon deletion |
| 19 | out-of-frame | DMD | Outside hotspot regions |

#### Reading Frame Exceptions
| Exons | Reading Frame | Phenotype | Notes |
|-------|---------------|-----------|-------|
| 2 | exception | Variable | Exception to reading frame rule |
| 78 | exception | Variable | C-terminal deletion exception |

#### Large/Complex Deletions
| Exons | Reading Frame | Phenotype | Notes |
|-------|---------------|-----------|-------|
| 45-50 | in-frame | BMD | Large in-frame deletion |
| 48, 49, 50 | in-frame | BMD | Preserved reading frame |
| 3, 4, 5, 6, 7 | out-of-frame | DMD | Proximal deletion |
| 8, 9 | out-of-frame | DMD | Proximal region |
| 45-55 | out-of-frame | DMD | Large hotspot deletion |

### LAMA2 Variants (Congenital MD)
| Type | HGVS | Protein | Severity | Notes |
|------|------|---------|----------|-------|
| Nonsense | c.2049_2050delAG | p.Arg683fs | Severe | Common frameshift |
| Missense | c.4405T>C | p.Cys1469Arg | Moderate-Severe | Affects laminin binding |
| Nonsense | c.7732C>T | p.Arg2578* | Severe | Nonsense mutation |
| Deletion | c.7147delC | p.Leu2383fs | Severe | Frameshift deletion |

### CAPN3 Variants (LGMD2A/R1)
| Type | HGVS | Protein | Severity | Notes |
|------|------|---------|----------|-------|
| Missense | c.550delA | p.Thr184fs | Moderate | Most common in Europe |
| Nonsense | c.2362AG>TCATCT | p.Arg788Ser | Moderate | Complex insertion |
| Missense | c.1715G>C | p.Arg572Pro | Mild-Moderate | Variable phenotype |
| Deletion | c.1194delT | p.Phe398fs | Moderate-Severe | Frameshift |

## How to Add New Curated Variants

### 1. Edit the Clinical Data File
Open `backend/knowledge_graph/clinical_data.py` and add to `VARIANT_ANNOTATIONS`:

```python
{
    "gene": "DMD",  # Gene symbol
    "variant_type": "deletion",  # deletion/nonsense/missense/etc
    "exons": [46, 47],  # List of affected exons (for deletions)
    "hgvs": "c.xxxx",  # Optional: HGVS notation
    "protein_change": "p.xxx",  # Optional: Protein change
    "reading_frame": "out-of-frame",  # in-frame/out-of-frame/exception
    "predicted_phenotype": "Duchenne Muscular Dystrophy",  # DMD/BMD/LAMA2-CMD/etc
    "severity": "severe",  # severe/moderate/mild/variable
    "eligible_treatments": ["Drug Name"],  # List of FDA-approved therapies
    "notes": "Clinical significance notes",  # Optional notes
}
```

### 2. Validate Reading Frame
For DMD deletions, use these rules:
- **Out-of-frame**: Disrupts open reading frame → DMD (severe)
- **In-frame**: Maintains open reading frame → BMD (milder)
- **General rule**: If `len(exons) % 3 == 0` → likely in-frame
- **Exceptions**: Exons 2 and 78 don't follow the rule

### 3. Map Therapy Eligibility
FDA-approved exon-skipping therapies:
- **Exon 45 amenable**: Casimersen (Amondys 45)
- **Exon 51 amenable**: Eteplirsen (Exondys 51)
- **Exon 53 amenable**: Golodirsen (Vyondys 53), Viltolarsen (Viltepso)

### 4. Test the New Variant
Run the demo notebook to ensure the variant is matched correctly:
```python
from backend.core.clinical_scenario import ClinicalScenario, GeneticFinding
from backend.core.scenario_processor import ScenarioProcessor

# Create a scenario with your new variant
genetic_finding = GeneticFinding(
    gene="DMD",
    variant_type="deletion",
    exons_affected=[your_exons],
    zygosity="hemizygous"
)

# Process and check interpretation
processor = ScenarioProcessor()
# ... rest of scenario setup
```

## ClinVar Integration (Showcase Feature)

### Current Status
- ✅ ClinVarService fully implemented
- ✅ Caching and rate limiting working
- ⚠️ **Disabled by default** (`ENABLE_CLINVAR=false`)
- ℹ️ Used for **showcase only**, not clinical decisions

### Enabling ClinVar Showcase
To enable ClinVar as a reference feature:

```bash
# .env file
ENABLE_CLINVAR=true
NCBI_API_KEY=your_api_key_here  # Optional but recommended
```

### What ClinVar Provides (When Enabled)
- Clinical significance labels (Pathogenic/Benign/VUS)
- Review status (0-4 stars)
- Submitter counts
- ClinVar IDs for reference

### What ClinVar Does NOT Provide
- ❌ FDA therapy eligibility
- ❌ Reading frame predictions
- ❌ Treatment recommendations
- ❌ Muscular dystrophy-specific rules

## Architecture

```
User Input (Genetic Finding)
    ↓
ScenarioProcessor._interpret_variants()
    ↓
KnowledgeGraphService.get_variant_annotations()
    ↓
├─→ PRIMARY: Curated VARIANT_ANNOTATIONS
│     ├─→ Reading frame prediction
│     ├─→ Therapy eligibility
│     └─→ Clinical interpretation
│
└─→ OPTIONAL: ClinVar enrichment (if enabled)
      └─→ Adds confidence metrics only
    ↓
Variant Interpretation (with treatments)
```

## Maintenance

### Regular Updates Needed
1. **New FDA approvals**: Add therapy eligibility mappings
2. **New pathogenic variants**: Add based on clinical literature
3. **Reading frame refinements**: Update based on new research
4. **ClinVar cache**: Auto-expires after 30 days

### Monitoring
- Check logs for unmatched variants: `"⚠️ No curated match for..."`
- Review fallback usage frequency
- Track which variants are most commonly queried

## References

### DMD/BMD
- UMD-DMD Database (November 2024 update)
- Birnkrant DJ, et al. Diagnosis and management of Duchenne muscular dystrophy. Lancet Neurol. 2018
- FDA approval documents for exon-skipping therapies
- PMC11593839, PMC5242159, PMC10252864

### LAMA2-CMD
- Allamand V, et al. LAMA2-related muscular dystrophy. GeneReviews. 2022
- Oliveira J, et al. LAMA2 gene mutation update. Hum Mutat. 2018

### CAPN3/LGMD2A
- Fanin M, et al. Calpain-3 deficiency. GeneReviews. 2022
- LGMD2A variant database (Leiden Open Variation Database)

## Contact

For questions about variant curation or to report missing variants, please:
1. Check existing variants in `backend/knowledge_graph/clinical_data.py`
2. Consult clinical literature for variant pathogenicity
3. Add new variants following the structure above
4. Test with demo scenarios

---

*Last Updated: November 2024*
*Total Curated Variants: 29*
*Therapy-Eligible DMD Deletions: 7*