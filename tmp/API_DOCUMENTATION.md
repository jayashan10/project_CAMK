# API Documentation: Variant Interpretation with ClinVar Integration

## Overview

The Clinical Decision Support API provides endpoints for variant interpretation using **curated clinical data** enriched with **real-time ClinVar API queries**. The system:

1. **Primary Source**: Curated variant database with FDA therapy mappings and reading frame predictions
2. **Secondary Source**: NCBI ClinVar API for clinical significance and confidence metrics (optional)

## Running the API

### Start the Server

```bash
# Using uv (recommended)
uv run uvicorn backend.api.main:app --reload

# Or regular uvicorn
uvicorn backend.api.main:app --reload
```

Server will start at: `http://localhost:8000`

### Interactive API Documentation

- **Swagger UI**: http://localhost:8000/docs (interactive, try endpoints live)
- **ReDoc**: http://localhost:8000/redoc (clean documentation view)

### Environment Configuration

Required in `.env`:
```bash
# ClinVar Integration (Optional but recommended)
ENABLE_CLINVAR=true
NCBI_API_KEY=your_api_key_here  # Get from https://www.ncbi.nlm.nih.gov/account/
```

---

## API Endpoints

### 1. Interpret Single Variant

**Endpoint**: `POST /api/variants/interpret`

Interprets a genetic variant using curated data + real-time ClinVar lookup.

#### Request Body

```json
{
  "gene": "DMD",
  "exons": [45, 46, 47],
  "variant_type": "deletion",
  "hgvs": "NM_004006.2:c.6439-?_6762+?del"  // Optional
}
```

#### Response Structure

```json
{
  "gene": "DMD",
  "variant_type": "deletion",
  "exons": [45, 46, 47],
  "hgvs": "NM_004006.2:c.6439-?_6762+?del",
  "protein_change": null,

  "clinical_data": {
    "source": "curated",
    "reading_frame": "out-of-frame",
    "predicted_phenotype": "Duchenne Muscular Dystrophy",
    "severity": "severe",
    "eligible_treatments": ["Casimersen (Amondys 45)"],
    "notes": "Common deletion pattern"
  },

  "clinvar_data": {
    "clinvar_id": "VCV000123456",
    "clinical_significance": "Pathogenic",
    "review_status": "practice guideline",
    "submitter_count": 5,
    "last_evaluated": "2024-03-15",
    "url": "https://www.ncbi.nlm.nih.gov/clinvar/variation/123456"
  }
}
```

#### Example Usage (curl)

```bash
curl -X POST "http://localhost:8000/api/variants/interpret" \
  -H "Content-Type: application/json" \
  -d '{
    "gene": "DMD",
    "exons": [45, 46, 47],
    "variant_type": "deletion"
  }'
```

#### Example Usage (Python)

```python
import requests

response = requests.post("http://localhost:8000/api/variants/interpret", json={
    "gene": "DMD",
    "exons": [45, 46, 47],
    "variant_type": "deletion"
})

data = response.json()

# Access curated clinical data
print(f"Phenotype: {data['clinical_data']['predicted_phenotype']}")
print(f"Reading Frame: {data['clinical_data']['reading_frame']}")
print(f"Treatments: {data['clinical_data']['eligible_treatments']}")

# Access ClinVar data (if available)
if data.get('clinvar_data'):
    print(f"ClinVar Significance: {data['clinvar_data']['clinical_significance']}")
    print(f"Review Status: {data['clinvar_data']['review_status']}")
```

---

### 2. Search Variants by Gene

**Endpoint**: `GET /api/variants/search/{gene}`

Returns all curated variants for a gene, optionally enriched with ClinVar data.

#### Parameters

- `gene` (path): Gene symbol (e.g., "DMD", "LAMA2", "CAPN3")
- `variant_type` (query, optional): Filter by type (e.g., "deletion", "missense")
- `include_clinvar` (query, optional): Include ClinVar enrichment (default: true)

#### Response Structure

```json
{
  "gene": "DMD",
  "variant_count": 19,
  "clinvar_enabled": true,
  "data_sources": ["curated", "clinvar"],
  "variants": [
    {
      "gene": "DMD",
      "variant_type": "deletion",
      "exons": [45, 46, 47],
      "clinical_data": { /*...*/ },
      "clinvar_data": { /*...*/ }
    },
    // ... more variants
  ]
}
```

#### Example Usage

```bash
# Get all DMD deletions with ClinVar data
curl "http://localhost:8000/api/variants/search/DMD?variant_type=deletion"

# Get all LAMA2 variants without ClinVar enrichment
curl "http://localhost:8000/api/variants/search/LAMA2?include_clinvar=false"
```

---

### 3. Direct ClinVar Query (Showcase)

**Endpoint**: `GET /api/variants/clinvar/gene/{gene}`

Query NCBI ClinVar API directly without curated data (showcase feature).

#### Parameters

- `gene` (path): Gene symbol
- `max_results` (query): Maximum results (default: 50, max: 200)

#### Response Structure

```json
{
  "gene": "DMD",
  "source": "ClinVar (NCBI E-utilities API)",
  "variant_count": 50,
  "max_results": 50,
  "note": "This is raw ClinVar data without curated clinical interpretations",
  "variants": [
    {
      "clinvar_id": "VCV000123456",
      "clinical_significance": "Pathogenic",
      "review_status": "practice guideline",
      "submitter_count": 5,
      "phenotypes": ["Duchenne muscular dystrophy"]
    },
    // ... more variants
  ]
}
```

#### Example Usage

```bash
curl "http://localhost:8000/api/variants/clinvar/gene/DMD?max_results=10"
```

**Note**: This endpoint requires `ENABLE_CLINVAR=true`. Returns 503 if disabled.

---

### 4. List FDA-Approved Therapies

**Endpoint**: `GET /api/variants/therapies`

Lists all FDA-approved therapies for muscular dystrophies in the curated database.

#### Response Structure

```json
{
  "therapy_count": 5,
  "note": "FDA-approved exon-skipping therapies curated from clinical guidelines",
  "therapies": [
    {
      "name": "Casimersen (Amondys 45)",
      "gene": "DMD",
      "variant_count": 2,
      "eligible_exons": [[45], [45, 46, 47]]
    },
    {
      "name": "Eteplirsen (Exondys 51)",
      "gene": "DMD",
      "variant_count": 3,
      "eligible_exons": [[51], [49, 50, 51], [48, 49, 50, 51]]
    },
    // ... more therapies
  ]
}
```

#### Example Usage

```bash
curl "http://localhost:8000/api/variants/therapies"
```

---

## Where ClinVar Data Appears in UI

### Primary Use Case: Variant Interpretation Card

When you build your React/Next.js frontend, ClinVar data will appear in the variant interpretation section:

```typescript
interface VariantInterpretation {
  gene: string;
  exons?: number[];
  hgvs?: string;

  // PRIMARY: Curated clinical data (always shown)
  clinical_data: {
    reading_frame: string;
    predicted_phenotype: string;
    severity: string;
    eligible_treatments: string[];
    notes?: string;
  };

  // SECONDARY: ClinVar reference (optional badge/expandable section)
  clinvar_data?: {
    clinvar_id: string;
    clinical_significance: string;
    review_status: string;
    submitter_count: number;
    url: string;
  };
}
```

### Recommended UI Layout

```
┌────────────────────────────────────────────────────┐
│ 🧬 Variant: DMD deletion exons 45-47              │
├────────────────────────────────────────────────────┤
│                                                    │
│ CLINICAL INTERPRETATION (Primary)                 │
│ • Reading Frame: Out-of-frame                     │
│ • Phenotype: Duchenne Muscular Dystrophy          │
│ • Severity: Severe                                │
│                                                    │
│ ELIGIBLE TREATMENTS                               │
│ ✓ Casimersen (Amondys 45)                        │
│   [Prescribing Info] [Clinical Trials]           │
│                                                    │
│ ┌──────────────────────────────────────────────┐ │
│ │ ClinVar Reference (Optional)  [✓ Pathogenic] │ │
│ │ Review Status: ★★★☆ (3/4 stars)              │ │
│ │ [View in ClinVar →]                          │ │
│ └──────────────────────────────────────────────┘ │
│                                                    │
└────────────────────────────────────────────────────┘
```

### Example React Component

```typescript
import { useState } from 'react';

interface Props {
  variant: VariantInterpretation;
}

export function VariantCard({ variant }: Props) {
  const [showClinVar, setShowClinVar] = useState(false);

  return (
    <div className="variant-card">
      {/* Primary Clinical Data */}
      <div className="clinical-data">
        <h3>Clinical Interpretation</h3>
        <p>Reading Frame: {variant.clinical_data.reading_frame}</p>
        <p>Phenotype: {variant.clinical_data.predicted_phenotype}</p>
        <p>Severity: {variant.clinical_data.severity}</p>
      </div>

      {/* Eligible Treatments */}
      <div className="treatments">
        <h3>Eligible Treatments</h3>
        {variant.clinical_data.eligible_treatments.map(treatment => (
          <div key={treatment} className="treatment-badge">
            ✓ {treatment}
          </div>
        ))}
      </div>

      {/* ClinVar Reference (Optional) */}
      {variant.clinvar_data && (
        <div className="clinvar-section">
          <button onClick={() => setShowClinVar(!showClinVar)}>
            <span className="badge">
              {variant.clinvar_data.clinical_significance}
            </span>
            {showClinVar ? '▼' : '▶'} ClinVar Reference
          </button>

          {showClinVar && (
            <div className="clinvar-details">
              <p>ClinVar ID: {variant.clinvar_data.clinvar_id}</p>
              <p>Review Status: {variant.clinvar_data.review_status}</p>
              <p>Submitters: {variant.clinvar_data.submitter_count}</p>
              <a href={variant.clinvar_data.url} target="_blank">
                View in ClinVar →
              </a>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
```

---

## Data Flow Architecture

```
┌─────────────────┐
│  Frontend UI    │
│  (React/Next)   │
└────────┬────────┘
         │
         │ HTTP Request
         ▼
┌─────────────────────────────────────────┐
│  FastAPI Backend                        │
│  (/api/variants/interpret)              │
└────────┬────────────────────────────────┘
         │
         ├─────────────────────────────────┐
         │                                 │
         ▼                                 ▼
┌──────────────────┐            ┌──────────────────┐
│ Curated Database │            │ ClinVar API      │
│ (clinical_data.  │            │ (NCBI E-utils)   │
│  py)             │            │                  │
│                  │            │ • Clinical sig   │
│ • Reading frame  │            │ • Review status  │
│ • FDA therapies  │            │ • Submitters     │
│ • Phenotypes     │            │                  │
└──────────────────┘            └──────────────────┘
         │                                 │
         │                                 │
         └─────────────┬───────────────────┘
                       │
                       ▼
              ┌────────────────┐
              │ Combined JSON  │
              │ Response       │
              └────────────────┘
                       │
                       ▼
              ┌────────────────┐
              │  Frontend UI   │
              │  Renders       │
              └────────────────┘
```

---

## Testing the API

Run the comprehensive test suite:

```bash
# Make sure server is running first
uv run uvicorn backend.api.main:app --reload &

# Run tests
uv run python test_variant_api.py
```

Test output shows:
1. ✅ Health check
2. ✅ Variant interpretation (curated + ClinVar)
3. ✅ Gene search with multiple variants
4. ✅ Direct ClinVar query
5. ✅ FDA therapies list

---

## Performance Considerations

### ClinVar API Rate Limits

- **With API key**: 10 requests/second
- **Without API key**: 3 requests/second
- **Caching**: 30-day TTL in `.clinvar_cache/`

### Optimization Strategies

1. **Batch requests**: Use `/api/variants/search/{gene}` to get all variants at once
2. **Cache-first**: ClinVar data is cached automatically
3. **Async loading**: Load curated data immediately, ClinVar data progressively
4. **Disable when not needed**: Set `include_clinvar=false` for faster responses

---

## Error Handling

### Common Errors

**404 - Variant Not Found**
```json
{
  "detail": "No curated annotation found for DMD variant. Try using exons or HGVS expression."
}
```

**503 - ClinVar Disabled**
```json
{
  "detail": "ClinVar API is disabled. Set ENABLE_CLINVAR=true in .env"
}
```

**500 - ClinVar API Failure**
```json
{
  "detail": "ClinVar API query failed: [error details]"
}
```

**Note**: ClinVar failures do NOT break the response - curated data is still returned.

---

## Summary

### ClinVar Integration in UI

1. **Primary Display**: Always show curated clinical data (reading frame, treatments)
2. **Secondary Badge**: Show ClinVar confidence badge when available
3. **Expandable Section**: Full ClinVar details on demand
4. **Progressive Loading**: Curated data loads immediately, ClinVar enriches asynchronously

### Best Practices

- ✅ Use curated data for clinical decisions
- ✅ Show ClinVar as "reference" or "validation"
- ✅ Clearly label data sources
- ✅ Don't block UI on ClinVar loading
- ✅ Handle ClinVar failures gracefully

### Next Steps

1. Build React components using the API responses
2. Implement progressive loading (curated first, ClinVar second)
3. Add confidence indicators using ClinVar review status
4. Create drill-down views to ClinVar when available

---

For more details, visit the interactive API docs:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc