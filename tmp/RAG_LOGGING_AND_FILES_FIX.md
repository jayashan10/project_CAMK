# RAG Logging & File Listing - Fix Summary

**Date:** November 16, 2024
**Status:** ✅ FIXED

---

## 🎯 What Was Fixed

### 1. ✅ Detailed Backend Logging

**File:** `backend/rag/gemini_file_search.py`

**What it shows:**
```
================================================================================
📝 RAG QUERY: 'What are the cardiac surveillance recommendations for DMD?'
🔍 FILTER: disease_code="DMD"
================================================================================

💬 GEMINI RESPONSE (906 chars):
   For individuals with Duchenne Muscular Dystrophy (DMD), cardiac
   surveillance involves several key recommendations...

--------------------------------------------------------------------------------

📚 Retrieved 2 evidence passages from guidelines:
   1. Source: se84qy4p0bjs
      Confidence: 1.0
      Text: swallowing dysfunction, constipation, gastro-oesophageal...

   2. Source: se84qy4p0bjs
      Confidence: 0.9
      Text: of health-care professionals; the neuromuscular specialist...

================================================================================
```

**Logs include:**
- ✅ The exact query sent to Gemini
- ✅ Any metadata filters applied (disease_code, etc.)
- ✅ The full synthesized response from Gemini (first 300 chars)
- ✅ Number of evidence passages retrieved
- ✅ Source document IDs
- ✅ Confidence scores
- ✅ Retrieved text snippets (first 100 chars)

**Where to see it:**
- In your `uvicorn` server terminal output
- When using the custom RAG query interface
- When analyzing scenarios with RAG recommendations

---

### 2. ✅ Actual PDF Filenames in Guidelines Browser

**Files Modified:**
- `backend/rag/gemini_file_search.py` - Fixed `list_uploaded_files()` method
- `backend/api/routes/rag.py` - Added `size_bytes` and `mime_type` fields
- `frontend/components/RAGQuery/index.tsx` - Display file sizes and types

**Before:**
```
📖 Uploaded Guidelines (1)
┌────────────────────────────────────────────┐
│ File Search Store                          │
│ fileSearchStores/4ahzybbmolo8-nnmkizo1owsa │
└────────────────────────────────────────────┘
```

**After:**
```
📖 Uploaded Guidelines (2)
┌───────────────────────────────────────────────────┐
│ DMD_Diagnosis_Part1_2018.pdf          [0.5 MB]   │
│ files/abc123...                                   │
│ 📄 PDF  📅 11/16/2024                            │
├───────────────────────────────────────────────────┤
│ DMD-diagnosis-and-management-part-2.pdf [0.6 MB] │
│ files/xyz789...                                   │
│ 📄 PDF  📅 11/16/2024                            │
└───────────────────────────────────────────────────┘
```

**Shows:**
- ✅ Actual PDF filename (not store ID)
- ✅ File size in MB/KB
- ✅ File type (PDF)
- ✅ Upload date
- ✅ Unique file ID for traceability

---

## 🚀 How to See the Changes

### Step 1: Restart Backend
```bash
cd /Users/Shared/Files\ From\ d.localized/NEU/CAMK/Project_CAMK

# Stop current server (Ctrl+C)

# Restart with detailed logging
uvicorn backend.api.main:app --reload --port 8000
```

**You'll now see detailed RAG logging in the terminal!**

### Step 2: Restart Frontend
```bash
cd frontend

# Stop current server (Ctrl+C)

# Restart
npm run dev
```

### Step 3: Test Custom RAG Query

1. Open http://localhost:3000
2. Scroll to "📚 Ask Clinical Guidelines (RAG)"
3. Click "📖 Uploaded Guidelines" - **you'll see actual PDF names!**
4. Type a question: "What are the cardiac surveillance recommendations for DMD?"
5. Click "Ask Guidelines"

**Watch your backend terminal** - you'll see:
```
================================================================================
📝 RAG QUERY: 'What are the cardiac surveillance recommendations for DMD?'
🔍 FILTER: disease_code="DMD"
================================================================================
💬 GEMINI RESPONSE (906 chars):
   [Full response preview...]
--------------------------------------------------------------------------------
📚 Retrieved 2 evidence passages from guidelines:
   1. Source: se84qy4p0bjs
      Confidence: 1.0
      Text: [Retrieved text snippet...]
================================================================================
```

### Step 4: Test Scenario Analysis

1. Load "Classic DMD" example scenario
2. Click "Analyze Scenario"

**Watch your backend terminal** - you'll see RAG queries being made:
```
================================================================================
📝 RAG QUERY: 'What are the evidence-based treatment and clinical management recommendations for DMD?'
================================================================================
💬 GEMINI RESPONSE (...)
📚 Retrieved 5 evidence passages from guidelines:
   ...
================================================================================
```

---

## 📊 What You'll See in Backend Logs

### Scenario Processing Example:

```
INFO:     ================================================================================
INFO:     📝 RAG QUERY: 'What are the evidence-based treatment and clinical management recommendations for DMD?'
INFO:     ================================================================================
INFO:     💬 GEMINI RESPONSE (1234 chars):
INFO:        Evidence-based treatment for DMD includes corticosteroid therapy,
INFO:        multidisciplinary care coordination, cardiac surveillance...
INFO:     --------------------------------------------------------------------------------
INFO:     📚 Retrieved 5 evidence passages from guidelines:
INFO:        1. Source: se84qy4p0bjs
INFO:           Confidence: 1.0
INFO:           Text: Prednisone or prednisolone 0.75 mg/kg per day should be initiated...
INFO:        2. Source: se84qy4p0bjs
INFO:           Confidence: 0.9
INFO:           Text: Baseline cardiac evaluation with ECG and echocardiography...
INFO:        3. Source: se84qy4p0bjs
INFO:           Confidence: 0.8
INFO:           Text: Physical therapy referral for stretching and contracture prevention...
INFO:     ================================================================================
INFO:     Returning 5 static + 5 RAG = 10 total recommendations for DMD
```

### Custom Query Example:

```
INFO:     ================================================================================
INFO:     📝 RAG QUERY: 'What are the side effects of corticosteroid therapy?'
INFO:     🔍 FILTER: disease_code="DMD"
INFO:     ================================================================================
INFO:     💬 GEMINI RESPONSE (756 chars):
INFO:        Corticosteroid therapy in DMD can have several side effects including
INFO:        weight gain, behavioral changes, adrenal insufficiency...
INFO:     --------------------------------------------------------------------------------
INFO:     📚 Retrieved 3 evidence passages from guidelines:
INFO:        1. Source: se84qy4p0bjs
INFO:           Confidence: 1.0
INFO:           Text: Monitor for side effects including weight gain, behavioral changes...
INFO:     ================================================================================
```

---

## 🎓 Benefits for Demonstration

### 1. Transparency
- Show **exactly what query** was sent to the RAG system
- Show **exactly what response** came back from Gemini
- Show **which text passages** were retrieved from which documents

### 2. Debugging
- Easy to trace issues with RAG queries
- See confidence scores for each result
- Verify that the right documents are being retrieved

### 3. Professionalism
- Guidelines browser shows actual PDFs, not technical IDs
- File sizes help users understand what's uploaded
- Upload dates provide version tracking

### 4. Trust
- Users can see the actual question being asked
- Users can see the full synthesized answer
- Users can verify retrieved text matches the summary

---

## 📝 Files Modified

### Backend
1. ✅ `backend/rag/gemini_file_search.py`
   - Added detailed query/response logging
   - Fixed `list_uploaded_files()` to return actual PDF names
   - Extract file size and MIME type

2. ✅ `backend/api/routes/rag.py`
   - Added `size_bytes` and `mime_type` fields to `GuidelineInfo` model
   - Pass through file metadata from service

### Frontend
1. ✅ `frontend/components/RAGQuery/index.tsx`
   - Added `size_bytes` and `mime_type` to TypeScript interface
   - Display file sizes in human-readable format (MB/KB)
   - Show file type icons (📄 PDF)
   - Show upload dates (📅)

### Test Scripts
1. ✅ **NEW:** `test_rag_logging.py` - Demonstrates backend logging

---

## ✅ Verification Checklist

- [ ] Backend restarts without errors
- [ ] Frontend restarts without errors
- [ ] Navigate to http://localhost:3000
- [ ] See "📚 Ask Clinical Guidelines (RAG)" section
- [ ] Click "📖 Uploaded Guidelines" shows **actual PDF names** (not store ID)
- [ ] File sizes displayed (e.g., "0.5 MB")
- [ ] Ask custom question
- [ ] Check backend terminal - see **detailed logging** with query, response, and retrieved text
- [ ] Load "Classic DMD" scenario
- [ ] Click "Analyze Scenario"
- [ ] Check backend terminal - see **RAG query logs** during processing

---

## 🎯 Example Backend Log Output

When you run a scenario or custom query, your `uvicorn` terminal will show:

```
INFO:     Connected to Neo4j at neo4j://127.0.0.1:7687
INFO:     Monarch database detected with 30486 diseases
INFO:     Gemini RAG service initialized for guideline retrieval

================================================================================
📝 RAG QUERY: 'What are the cardiac surveillance recommendations for DMD?'
🔍 FILTER: disease_code="DMD"
================================================================================

💬 GEMINI RESPONSE (906 chars):
   For individuals with Duchenne Muscular Dystrophy (DMD), cardiac
   surveillance involves several key recommendations to monitor and
   manage heart health. It is advised to consult a cardiologist...

--------------------------------------------------------------------------------

📚 Retrieved 2 evidence passages from guidelines:
   1. Source: se84qy4p0bjs
      Confidence: 1.0
      Text: swallowing dysfunction, constipation, gastro-oesophageal reflux...

   2. Source: se84qy4p0bjs
      Confidence: 0.9
      Text: of health-care professionals; the neuromuscular specialist serves...

================================================================================
```

This makes it **crystal clear** what's happening behind the scenes!

---

**Status:** 🟢 READY FOR DEMO
**Last Updated:** November 16, 2024
**Perfect for demonstrating RAG transparency in your coursework!** 🚀
