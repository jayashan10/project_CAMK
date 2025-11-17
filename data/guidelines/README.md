# Clinical Guidelines Directory

This directory stores clinical guideline PDFs for the RAG (Retrieval-Augmented Generation) system. These guidelines are uploaded to Google Gemini File Search for semantic retrieval of evidence-based treatment recommendations.

## Directory Structure

```
data/guidelines/
├── DMD/                    # Duchenne Muscular Dystrophy guidelines
├── BMD/                    # Becker Muscular Dystrophy guidelines
├── LGMD/                   # Limb-Girdle Muscular Dystrophy guidelines
├── variant_interpretation/ # ACMG, GeneReviews, variant classification
└── general/                # General guidelines (genetic counseling, etc.)
```

## Priority Guidelines to Acquire

### Tier 1 (Essential - High Priority)

**1. Birnkrant DJ, et al. (2018). DMD Care Considerations**
- **Source**: Lancet Neurology (3-part series)
- **Links**:
  - Part 1: https://www.thelancet.com/journals/laneur/article/PIIS1474-4422(18)30024-3/fulltext
  - Part 2: https://www.thelancet.com/journals/laneur/article/PIIS1474-4422(18)30025-5/fulltext
  - Part 3: https://www.thelancet.com/journals/laneur/article/PIIS1474-4422(18)30026-7/fulltext
- **Save as**:
  - `DMD/birnkrant_2018_part1_diagnosis.pdf`
  - `DMD/birnkrant_2018_part2_rehabilitation.pdf`
  - `DMD/birnkrant_2018_part3_cardiac_respiratory.pdf`

**2. ACMG/AMP Variant Interpretation Guidelines (2015)**
- **Source**: Genetics in Medicine
- **Link**: https://www.nature.com/articles/gim201530
- **Save as**: `variant_interpretation/acmg_2015_standards.pdf`

**3. TREAT-NMD Standards of Care**
- **Source**: https://treat-nmd.org/care/dmd/
- **Download**: Individual care modules (corticosteroids, cardiac, respiratory)
- **Save as**: `DMD/treat_nmd_dmd_corticosteroids.pdf` (or combined)

### Tier 2 (Important - FDA Approvals)

**4. FDA Drug Approval Documents**

**Eteplirsen (Exondys 51) - Exon 51 Skipping**
- **Link**: https://www.accessdata.fda.gov/drugsatfda_docs/nda/2016/206488_summary.pdf
- **Save as**: `DMD/fda_eteplirsen_approval_2016.pdf`

**Casimersen (Amondys 45) - Exon 45 Skipping**
- **Link**: Search FDA.gov for NDA 211970
- **Save as**: `DMD/fda_casimersen_approval_2021.pdf`

**Golodirsen (Vyondys 53) - Exon 53 Skipping**
- **Link**: Search FDA.gov for NDA 211960
- **Save as**: `DMD/fda_golodirsen_approval_2019.pdf`

### Tier 3 (Supplementary)

**5. GeneReviews: Dystrophinopathies**
- **Source**: NCBI/University of Washington
- **Link**: https://www.ncbi.nlm.nih.gov/books/NBK1119/
- **How to download**: Click "PDF" button on the page
- **Save as**: `variant_interpretation/genereviews_dystrophinopathies.pdf`

**6. Other Guidelines** (optional)
- BMD cardiac surveillance protocols
- LGMDR1 clinical overviews
- Genetic counseling guidelines for X-linked disorders

## How to Use

### 1. Acquire PDFs

Download the guideline PDFs from the sources listed above and save them to the appropriate subdirectories.

### 2. Upload to Gemini File Search

Once you have the PDFs, run the upload script:

```bash
# Dry run to see what would be uploaded
python backend/rag/upload_guidelines.py --dry-run

# Actually upload the guidelines
python backend/rag/upload_guidelines.py

# List currently uploaded guidelines
python backend/rag/upload_guidelines.py --list
```

### 3. Verify Upload

The upload script will show:
- ✅ Successfully uploaded files
- ⏭️ Skipped files (not found)
- ❌ Errors (if any)

### 4. Query Guidelines

Once uploaded, the guidelines can be queried via the `GeminiFileSearchService`:

```python
from backend.rag.gemini_file_search import GeminiFileSearchService

service = GeminiFileSearchService()
service.initialize_store()

# Search for corticosteroid recommendations
results = service.search_guidelines(
    query="What are the corticosteroid therapy recommendations?",
    disease_code="DMD"
)

for evidence in results:
    print(f"Recommendation: {evidence.recommendation}")
    print(f"Source: {evidence.source}")
    print(f"Citation: {evidence.citation}")
```

## Notes

- **File format**: PDFs are recommended (preserves tables, charts, formatting)
- **File size limit**: 100 MB per file (should be sufficient for guidelines)
- **Storage**: Free tier provides 1 GB total storage
- **Copyright**: Ensure you comply with copyright restrictions. Use for educational/research purposes only.

## Metadata

Each guideline PDF is uploaded with rich metadata for precise filtering:

- `disease_code`: Disease code (DMD, BMD, LGMD, etc.)
- `guideline_type`: Type (management, standards_of_care, fda_approval, etc.)
- `publication_year`: Year published
- `evidence_level`: Evidence level (Level_A, Level_B, Level_C)
- `topics`: Comma-separated topics (corticosteroids, cardiac_care, etc.)
- `organization`: Publishing organization (TREAT-NMD, ACMG, etc.)

This metadata enables targeted searches like "DMD management guidelines with Level A evidence".

## Troubleshooting

**Problem**: Upload script says "File not found"
- **Solution**: Ensure PDFs are in the correct subdirectory matching the path in `upload_guidelines.py`

**Problem**: "Gemini client not initialized"
- **Solution**: Set `GOOGLE_API_KEY` in your `.env` file. Get a free key from https://aistudio.google.com/app/apikey

**Problem**: Upload fails with API error
- **Solution**: Check your API quota (free tier: 1,500 requests/day). Try again later if exceeded.

## References

- TREAT-NMD: https://treat-nmd.org/care/dmd/
- Birnkrant 2018: https://www.thelancet.com/journals/laneur/article/PIIS1474-4422(18)30024-3/fulltext
- ACMG Standards: https://www.nature.com/articles/gim201530
- FDA Approvals: https://www.accessdata.fda.gov/scripts/cder/daf/
- GeneReviews: https://www.ncbi.nlm.nih.gov/books/NBK1119/
